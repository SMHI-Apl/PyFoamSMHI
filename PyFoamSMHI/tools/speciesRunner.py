#!/usr/bin/env python
#Python standard modules
from os import path
import os, glob, time,sys, logging
from optparse import OptionParser

#PyFoam modules
from PyFoam.Execution.ConvergenceRunner import ConvergenceRunner
from PyFoam.Execution.UtilityRunner import UtilityRunner
from PyFoam.LogAnalysis.StandardLogAnalyzer import StandardLogAnalyzer
from PyFoam.RunDictionary.SolutionFile import SolutionFile
from PyFoam.RunDictionary.ParameterFile import ParameterFile

#PyFoamContrib
from PyFoamSMHI.ParallelExecutionNSC import LAMMachine
from PyFoamSMHI import ConvergenceTable, FoamArchive, ControlFile, CaseHandler, ExtendedParameterFile
from PyFoamSMHI.templates.PyFoamWindRunnerCfTemplate import defaultCf

import pdb

usage = "usage: %prog controlFile [options] "
version="%prog 1.0"

#sys.argv=[sys.argv[0],"--case","/home/openfoam/dvlp/highRize","/home/openfoam/dvlp/highRize/controlFile"]

def generateCf(filename):
    if not path.exists(path.dirname(filename)):
        print "Error, path for controlfile does not exist"
    if path.exists(filename):
        answer=raw_input("File already exists, replace? (y/n)")
        if answer=="n":
            sys.exit()
        elif answer=="y":
            fid=open(filename,"w")
            fid.write(defaultCf)
            fid.close()
        else:
            print "Invalid answer (should be y or n)"
            sys.exit()
    else:
        fid=open(filename,"w")
        fid.write(defaultCf)
        fid.close()
            
def main():
    parser=OptionParser(usage= usage, version=version)
    parser.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="Only print warnings and errors")    
    
    parser.add_option("-t", "--template",
                      action="store",dest="controlfile",default=None,
                      help="Generate default controlfile")

    parser.add_option("-l", "--logfile",
                      action="store",dest="logfile",default=None,
                      help="Writes output to logfile")
    
    parser.add_option("-d", "--debug",
                      action="store_true",dest="debug",default=False,
                      help="Writes output to logfile")
    
    parser.add_option("-c", "--case",
                      action="store",dest="case",default=None,
                      help="Specifies case directory")
    
    (options, args) = parser.parse_args()
    
    rootLogger=logging.getLogger('')
    logger=logging.getLogger('speciesRunner')
    reportLevel=logging.INFO
    if options.quiet:
        reportLevel=logging.WARNING
    if options.debug:
        reportLevel=logging.DEBUG
    rootLogger.setLevel(reportLevel)

    if options.logfile==None:
        console=logging.StreamHandler()
        console.setLevel(reportLevel)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)    
        rootLogger.addHandler(console)
    
    if options.controlfile!=None:
        generateCf(path.abspath(options.controlfile))
        print "Wrote default controlfile"
        sys.exit()
        
    if options.logfile!=None:
        logFileName=path.abspath(options.logfile)
        if not path.exists(path.dirname(logFileName)):
            print "Bad argument, directory for logfile does not exist"
            sys.exit()
        logfile=logging.FileHandler(logFileName,"w")
        logfile.setLevel(reportLevel)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        logfile.setFormatter(formatter)    
        rootLogger.addHandler(logfile)
            
    if len(args)!=1:
        parser.error("Incorrect number of arguments")
        
    cf=ControlFile.ControlFile(fileName=path.abspath(args[0]))
   
    if options.case!=None:
        casePath=path.abspath(options.case)
    else:
        casePath=os.getcwd()
        
    caseName=path.basename(casePath)
    ch=CaseHandler.CaseHandler(casePath)
    
    wspeeds=cf.findScalarList("wspeeds:",optional=False)
    wdirs=cf.findScalarList("wdirs:",optional=False)
    iterations=cf.findScalar("iterations:",optional=False)
    fieldsToArchive=cf.findStringList("fieldsToArchive:",optional=False)    
    flowArchiveDirName=cf.findString("flowArchiveDirName:",optional=False)
    concArchiveDirName=cf.findString("concArchiveDirName:",optional=False)
    archiveVTK=cf.findBoolean("archiveVTK:",optional=False)
    VTKArchiveDir=cf.findExistingPath("VTKArchiveDir:",optional=False)
    nodes=int(cf.findScalar("nodes:",optional=False))
    CPUs=cf.findScalar("CPUs:",optional=True)        
    if CPUs==None:
        nprocesses=8*nodes
    else:
        nprocesses=int(CPUs)
    #-----------------------------------
    solver=cf.findString("solver:",default="speciesFoam")
    initCmd=cf.findString("initialize:",optional=True)    
   
    flowArchive=FoamArchive.FoamArchive(casePath,flowArchiveDirName)
    concArchive=FoamArchive.FoamArchive(casePath,concArchiveDirName)
    flowFiles=["U","p","k","epsilon","nut"]
    nwdir= len(wdirs)    
    convTable=ConvergenceTable.ConvergenceTable(casePath)
    
    logger.info("Running speciesFoam")
    logger.info("Setup overview:")
    logger.info(25*"-")
    logger.info("Case: "+ caseName)
    logger.info(25*"-")
    logger.info("Wind directions are: "+ str(wdirs))
    logger.info("Wind speeds are: "+str(wspeeds))
    nruns=nwdir*len(wspeeds)
    logger.info("Total number of runs: "+str(nruns))
    logger.info(25*"-")
    logger.info("Number of iterations are: "+str(iterations))
    logger.info("Number of nodes are: "+str(nodes))
    logger.info("Fields to be archived: "+str(fieldsToArchive))
    logger.info("ArchiveToVTK is set to: "+str(archiveVTK))
    logger.info(50*"=")
    
    controlDict=ParameterFile(ch.controlDict())
    statisticsDict=ExtendedParameterFile.ExtendedParameterFile(path.join(ch.systemDir(),"statisticsDict"))

    if controlDict.readParameter("writeCompression")=="compressed":
        filesToArchive=[field+".gz" for field in fieldsToArchive]
        flowFiles=[field+".gz" for field in flowFiles]

    if not path.exists(VTKArchiveDir) and archiveVTK:
        logger.error("The VTKArchiveDir does not exist")
        sys.exit()
        
    #booting lammachine for parallell execution
    if nprocesses>1:
        Lam=LAMMachine(nr=nprocesses)
        Lam.writeScotch(ch)
    
    controlDict.replaceParameter("stopAt", "nextWrite")
    
    timeLeft=iterations*nruns*20
    timeSpent=05
    timeCase=iterations*20
    timeEstimated=time.localtime(time.time()+timeLeft)
    casesRun=0
    casesLeft=nruns
    logger.info("Backing up initial fields")
    ch.backUpInitialFields()
    logger.info("Backup made of initial fields")
    for wspeed in wspeeds:
        for wdir in wdirs:
            timeInit=time.time()
            dirName="wspeed_"+str(wspeed)+"_wdir_"+str(wdir)
            
            if not flowArchive.inArchive(dirName=dirName):
                logger.warning("Missing flow files in dir: "+dirName)
                logger.warning("No run will be made for missing flow files")
            else:
                controlDict.replaceParameter("writeInterval",str(iterations))
                logger.info("Running calculations for dir: "+ str(wdir)+ " speed: "+ str(wspeed))
                logger.info("Time left: "+str(timeLeft/60.0)+"min, Time spent: "+str(timeSpent/60.0)+"min")
                logger.info("Estimated time for finish: "+str(timeEstimated[:4]))
                logger.info("Cases finished: "+str(casesRun)+" cases left: "+str(casesLeft))
                logger.info(" ")
                ch.clearResults()
                logger.info("...Modifying bc:s")
                for f in flowFiles:
                    ch.execute("rm "+path.join(ch.initialDir(),f))                
                ch.modWindDir(ch.initialDir(),wdir)
                logger.info("bc:s modified!")
                logger.info("Restoring archived flow fields")

                flowArchive.restore(dirName,flowFiles,ch.initialDir())
                for filename in flowFiles:
                    flowArchive.getFile(outputFile=path.join(ch.initialDir(),filename),fileName=filename,archiveDirName=dirName)
                logger.info("Restored archived flow fields!")

                if nprocesses>1:
                    if Lam.machineOK():
                        decomposeCmd="decomposePar"
                        decomposeUtil=UtilityRunner(argv=[decomposeCmd,"-case",casePath],silent=True,logname="decomposePar")
                        logger.info("...Decomposing case to run on"+str(Lam.cpuNr())+str(" of processors"))
                        decomposeUtil.start()
                        if decomposeUtil.runOK():
                            logger.info("Case decomposed!")
                        else:
                            logger.error("Error when running decomposePar")
                            sys.exit()
                    else:
                        logger.error("Error: Could not start lam-machine")
                        sys.exit()
                else:
                    Lam=None
                    logger.info("Serial Run chosen!")
        
                logger.info("...Running solver for species")
                FoamSolver = ConvergenceRunner(StandardLogAnalyzer(),argv=[solver,"-case",casePath],silent=True,lam=Lam,logname=solver)
                FoamSolver.start()
                if FoamSolver.runOK():
                    logger.info("Iterations finished for speciesFoam")
                else:
                    logger.error("Error while running speciesFoam")
                    sys.exit()
            
                if nprocesses>1:
                    logger.info("Reconstructing decomposed case...")
                    reconstructCmd="reconstructPar"
                    reconstructUtil=UtilityRunner(argv=[reconstructCmd,"-case",casePath],silent=True,logname="reconstrucPar")
                    reconstructUtil.start()
                    if reconstructUtil.runOK():
                        logger.info("recunstruction ready!")
                    else:
                        logger.error("Error while running recontructPar")
                        sys.exit()
    
                    logger.info("Removing decomposed mesh")
                    ch.execute("rm -r "+os.path.join(casePath,"processor*"))
                    logger.info("Removed decomposed mesh!")


                iterationsReady=int(ch.getLast())-int(path.basename(ch.initialDir())) 
                if iterationsReady < iterations:
                    logger.warning("Run was aborted before finalizing the wanted number of iterations")
                    logger.warning("Guessing that nan:s were present in results. Removing results from current run and moving on to next run")
                                    
                logger.info("Archiving results")
                #save latest concentration result files
                solFiles=[f for f in os.listdir(ch.latestDir()) if f[:4]=="spec" and f[:12]!="spec_default" and not ".bak" in f and not "~" in f and not "#" in f]
                for filename in solFiles:
                    dirName= "wspeed_"+str(wspeed)+"_wdir_"+str(wdir)
                    concArchive.addFile(path.join(ch.latestDir(),filename),dirName=dirName)
                    convTable.addResidual("wd_"+str(wdir)+"_ws_"+str(wspeed),"speciesFoam","linear_"+filename,casesRun+1)
                    convTable.addProbes("wd_"+str(wdir)+"_ws_"+str(wspeed),filename,casesRun+1)                
                logger.info("Residuals and probes from solver speciesFoam added to convergence table")

                #Adding the list of names of archived concentration files to the statisticsDict dictionary
                archivedConcFiles=concArchive.listFilesInDirs("spec_")        
                statisticsDict.replaceParameterList("concFileList",archivedConcFiles)

                if archiveVTK:
                    #Creating a temporary last time directory to be used by foamToVTK
                    VTKTime=str(eval(path.basename(ch.latestDir()))+1)
                    newTimeDir=path.join(casePath,VTKTime)
                    os.mkdir(newTimeDir)
                    for filename in solFiles:
                        oldFile=path.join(casePath,str(eval(ch.getLast())-1),filename)
                        ch.execute("cp "+oldFile+" "+newTimeDir+"/")
    
                    foamToVTKUtil=UtilityRunner(argv=["foamToVTK","-case",casePath,"-time "+VTKTime],silent=True,logname="foamToVTK")
                    foamToVTKUtil.start()
                    if foamToVTKUtil.runOK():
                        ch.execute("mv "+path.join(casePath,"VTK")+" "+path.join(VTKArchiveDir,"VTK"+"_wspeed_"+str(wspeed)+"_wdir_"+str(wdir)))               
                        ch.execute("rm -r "+path.join(casePath,VTKTime) )
                        logger.info("Exported to VTK archive!")
                    else:
                        logger.error("Error when exporting to VTK")
                        sys.exit()
                             
                logger.info("Finished wdir: "+ str(wdir)+ " wspeed: "+ str(wspeed)+ "Last iter = "+ch.getLast())
                logger.info(" ")
                casesRun+=1
                casesLeft-=1
                timeCase=time.time()-timeInit
                timeSpent+=timeCase
                timeLeft=casesLeft*timeCase
                timeEstimated=time.localtime(time.time()+timeLeft)

                ch.clearResults()
                ch.restoreInitialFields()
                logger.info("Restored initital fields")
            
                #restoring windData dictionary to original state
                convTable.writeProbes()
                convTable.writeResiduals()
                logger.info("Residuals and probes from solver windFoam written to case/convergence directory")
            
    #Restoring controlDict to original state
    controlDict.purgeFile()
    logger.info("Finished batch calculation!")

if __name__ == "__main__":
    main()

