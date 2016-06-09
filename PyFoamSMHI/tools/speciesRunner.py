#!/usr/bin/env python

from os import path
import os
import time
import sys
import logging
import argparse

# PyFoam modules
from PyFoam.Execution.ConvergenceRunner import ConvergenceRunner
from PyFoam.Execution.UtilityRunner import UtilityRunner
from PyFoam.LogAnalysis.StandardLogAnalyzer import StandardLogAnalyzer
from PyFoam.RunDictionary.ParameterFile import ParameterFile

# PyFoamContrib
from PyFoamSMHI.contrib.ParallelExecutionNSC import LAMMachine
from PyFoamSMHI.contrib import (
    ConvergenceTable,
    FoamArchive,
    ControlFile,
    CaseHandler,
    ExtendedParameterFile
)
from PyFoamSMHI.contrib.utilities import (
    generateCf,
    VerboseAction,
    LogFileAction
)

from PyFoamSMHI.templates.PyFoamWindRunnerCfTemplate import defaultCf

usage = "usage: %prog controlFile [options] "
version = "%prog 1.0"

# sys.argv=[sys.argv[0],"--case","/home/openfoam/dvlp/highRize","/home/openfoam/dvlp/highRize/controlFile"]

log = logging.getLogger(__name__)

CORES_PER_NODE = 16
FLOW_FILES = ["U", "p", "k", "epsilon", "nut"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_option(
        "-t", "--template",
        action="store", dest="template",
        help="Generate default controlfile"
    )

    parser.add_argument(
        '-v',
        action=VerboseAction, dest='loglevel', default=logging.get_loglevel(),
        help='increase verbosity in terminal',
    )

    parser.add_argument(
        '-l', metavar='logfile',
        action=LogFileAction, dest='logfile',
        help='write verbose output to logfile',
    )

    parser.add_argument(
        "-c", "--case",
        action="store", dest="case", default=os.getcwd(),
        help="Specifies case directory (default is current workdir)",
    )

    args = parser.parse_args()
    
    if args.template is not None:
        generateCf(args.template, defaultCf)
        log.info('Wrote default controlfile')
        sys.exit(0)
            
    cf = ControlFile.ControlFile(args.template)
   
    caseName = path.basename(args.case)
    ch = CaseHandler.CaseHandler(args.case)
    
    wspeeds = cf.findScalarList("wspeeds:", optional=False)
    wdirs = cf.findScalarList("wdirs:", optional=False)
    iterations = cf.findScalar("iterations:", optional=False)
    fieldsToArchive = cf.findStringList("fieldsToArchive:", optional=False)
    flowArchiveDirName = cf.findString(
        "flowArchiveDirName:", optional=True, default='flowArchive'
    )
    concArchiveDirName = cf.findString(
        "concArchiveDirName:", optional=True, default='concArchive'
    )
    archiveVTK = cf.findBoolean("archiveVTK:", optional=True, default=False)
    VTKArchiveDir = cf.findExistingPath("VTKArchiveDir:", optional=False)
    nodes = int(cf.findScalar("nodes:", optional=False))
    CPUs = cf.findScalar("CPUs:", optional=True)
    if CPUs is None:
        nprocesses = CORES_PER_NODE * nodes
    else:
        nprocesses = int(CPUs)
    #-----------------------------------
    solver = cf.findString("solver:", default="speciesFoam")
    initCmds = cf.findStringList("initialize:", default=[])
    flowArchive = FoamArchive.FoamArchive(args.case, flowArchiveDirName)
    concArchive = FoamArchive.FoamArchive(args.case, concArchiveDirName)

    nwdir = len(wdirs)
    convTable = ConvergenceTable.ConvergenceTable(args.case)
    
    log.info("Running speciesFoam")
    log.info("Setup overview:")
    log.info(25 * "-")
    log.info("Case: " + caseName)
    log.info(25 * "-")
    log.info("Wind directions are: " + str(wdirs))
    log.info("Wind speeds are: " + str(wspeeds))
    nruns = nwdir * len(wspeeds)
    log.info("Total number of runs: " + str(nruns))
    log.info(25 * "-")
    log.info("Number of iterations are: " + str(iterations))
    log.info("Number of nodes are: " + str(nodes))
    log.info("Fields to be archived: " + str(fieldsToArchive))
    log.info("ArchiveToVTK is set to: " + str(archiveVTK))
    log.info(50 * "=")
    
    controlDict = ParameterFile(ch.controlDict())
    statisticsDict = ExtendedParameterFile.ExtendedParameterFile(
        path.join(ch.systemDir(), "statisticsDict")
    )

    if controlDict.readParameter("writeCompression") == "compressed":
        filesToArchive = [field + ".gz" for field in fieldsToArchive]
        flowFiles = [field + ".gz" for field in FLOW_FILES]

    if not path.exists(VTKArchiveDir) and archiveVTK:
        log.error("The VTKArchiveDir does not exist")
        sys.exit(1)
        
    # booting lammachine for parallell execution
    if nprocesses > 1:
        Lam = LAMMachine(nr=nprocesses)
        Lam.writeScotch(ch)
    
    controlDict.replaceParameter("stopAt", "nextWrite")
    
    timeLeft = iterations * nruns * 20
    timeSpent = 05
    timeCase = iterations * 20
    timeEstimated = time.localtime(time.time() + timeLeft)
    casesRun = 0
    casesLeft = nruns
    log.info("Backing up initial fields")
    ch.backUpInitialFields()
    log.info("Backup made of initial fields")
    for wspeed in wspeeds:
        for wdir in wdirs:
            timeInit = time.time()
            dirName = "wspeed_" + str(wspeed) + "_wdir_" + str(wdir)
            
            if not flowArchive.inArchive(dirName=dirName):
                log.warning("Missing flow files in dir: "+dirName)
                log.warning("No run will be made for missing flow files")
            else:
                controlDict.replaceParameter("writeInterval", str(iterations))
                log.info(
                    "Running calculations for dir: " +
                    str(wdir) + " speed: " + str(wspeed)
                )
                log.info(
                    "Time left: " + str(timeLeft / 60.0) +
                    "min, Time spent: "+str(timeSpent / 60.0) + "min"
                )
                log.info(
                    "Estimated time for finish: " + str(timeEstimated[:4])
                )
                log.info(
                    "Cases finished: " + str(casesRun) +
                    " cases left: " + str(casesLeft)
                )
                log.info(" ")
                ch.clearResults()
                log.info("...Modifying bc:s")
                for f in flowFiles:
                    ch.execute("rm " + path.join(ch.initialDir(), f))
                ch.modWindDir(ch.initialDir(), wdir)
                log.info("bc:s modified!")
                log.info("Restoring archived flow fields")
                flowArchive.restore(dirName, flowFiles, ch.initialDir())
                for filename in flowFiles:
                    flowArchive.getFile(
                        outputFile=path.join(ch.initialDir(), filename),
                        fileName=filename, archiveDirName=dirName
                    )
                log.info("Restored archived flow fields!")

                for initCmd in initCmds:
                    initUtil = UtilityRunner(
                        argv=[initCmd, "-case", args.case],
                        silent=True,
                        logname=initCmd
                    )
                    initUtil.start()
                    if initUtil.runOK():
                        log.info(
                            "Successfully finished: %s" % initCmd
                        )
                    else:
                        log.error(
                            "Error when running: %s" % initCmd
                        )
                        sys.exit(1)

                if nprocesses > 1:
                    if Lam.machineOK():
                        decomposeCmd = "decomposePar"
                        decomposeUtil = UtilityRunner(
                            argv=[decomposeCmd, "-case", args.case],
                            silent=True, logname="decomposePar"
                        )
                        log.info(
                            "Decomposing case for %i processors" % Lam.cpuNr()
                        )
                        decomposeUtil.start()
                        if decomposeUtil.runOK():
                            log.info("Case decomposed!")
                        else:
                            log.error("Error when running decomposePar")
                            sys.exit()
                    else:
                        log.error("Error: Could not start lam-machine")
                        sys.exit()
                else:
                    Lam = None
                    log.info("Serial Run chosen!")
        
                log.info("...Running solver for species")
                FoamSolver = ConvergenceRunner(
                    StandardLogAnalyzer(),
                    argv=[solver, "-case", args.case],
                    silent=True, lam=Lam, logname=solver
                )
                FoamSolver.start()
                if FoamSolver.runOK():
                    log.info("Iterations finished for speciesFoam")
                else:
                    log.error("Error while running speciesFoam")
                    sys.exit()
            
                if nprocesses > 1:
                    log.info("Reconstructing decomposed case...")
                    reconstructCmd = "reconstructPar"
                    reconstructUtil = UtilityRunner(
                        argv=[reconstructCmd, "-case", args.case],
                        silent=True, logname="reconstrucPar"
                    )
                    reconstructUtil.start()
                    if reconstructUtil.runOK():
                        log.info("recunstruction ready!")
                    else:
                        log.error("Error while running recontructPar")
                        sys.exit()
    
                    log.info("Removing decomposed mesh")
                    ch.execute(
                        "rm -r " + os.path.join(args.case, "processor*")
                    )
                    log.info("Removed decomposed mesh!")

                iterationsReady = (
                    int(ch.getLast()) -
                    int(path.basename(ch.initialDir()))
                )
                if iterationsReady < iterations:
                    log.warning(
                        "Run was aborted before finalizing" +
                        " the wanted number of iterations"
                    )
                    log.warning(
                        "Guessing that nan:s were present in results. " +
                        "Removing results from current run and moving on"
                    )
                                    
                log.info("Archiving results")
                # save latest concentration result files
                solFiles = [
                    f for f in os.listdir(ch.latestDir())
                    if f[:4] == "spec" and f[:12] != "spec_default" and
                    ".bak" not in f and "~" not in f and "#" not in f
                ]
                for filename in solFiles:
                    dirName = "wspeed_" + str(wspeed) + "_wdir_" + str(wdir)
                    concArchive.addFile(
                        path.join(ch.latestDir(), filename), dirName=dirName
                    )
                    convTable.addResidual(
                        "wd_" + str(wdir) + "_ws_" + str(wspeed),
                        "speciesFoam", "linear_" + filename,
                        casesRun+1
                    )
                    convTable.addProbes(
                        "wd_" + str(wdir) + "_ws_" + str(wspeed),
                        filename,
                        casesRun + 1
                    )
                log.info(
                    "Residuals and probes from solver " +
                    "speciesFoam added to convergence table"
                )

                # Adding the list of names of archived concentration
                # files to the statisticsDict dictionary
                archivedConcFiles = concArchive.listFilesInDirs("spec_")
                statisticsDict.replaceParameterList(
                    "concFileList", archivedConcFiles
                )
                             
                log.info("Finished wdir: %f, wspeed: %f, Last iter: %i" % (
                    wdir, wspeed, ch.getLast())
                )
                log.info(" ")
                casesRun += 1
                casesLeft -= 1
                timeCase = time.time() - timeInit
                timeSpent += timeCase
                timeLeft = casesLeft * timeCase
                timeEstimated = time.localtime(time.time() + timeLeft)

                ch.clearResults()
                ch.restoreInitialFields()
                log.info("Restored initital fields")
            
                # restoring windData dictionary to original state
                convTable.writeProbes()
                convTable.writeResiduals()
                log.info(
                    "Residuals and probes from solver windFoam " +
                    "written to case/convergence directory"
                )
            
    # Restoring controlDict to original state
    controlDict.purgeFile()
    log.info("Finished batch calculation!")


if __name__ == "__main__":
    main()

