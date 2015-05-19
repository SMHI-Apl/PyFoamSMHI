#!/usr/bin/env python
#Python standard modules
from os import path
import os, glob, time,sys, logging
from optparse import OptionParser

#PyFoam modules
from PyFoam.Execution.UtilityRunner import UtilityRunner
from PyFoam.RunDictionary.SolutionFile import SolutionFile
from PyFoam.RunDictionary.ParameterFile import ParameterFile
#PyFoamContrib
from PyFoamSMHI.contrib import FoamArchive, CaseHandler
from PyFoamSMHI.templates.PyFoamWindRunnerCfTemplate import defaultCf


usage = "usage: %prog [options] "
version="%prog 1.0"


def main():
    parser=OptionParser(usage= usage, version=version)
    parser.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="Only print warnings and errors")
    
    parser.add_option("-a", "--archiveDir",
                      action="store", dest="archiveDir", default=None,
                      help="Path to archive directory to fetch results from")
    
    parser.add_option("-l", "--logfile",
                      action="store",dest="logfile",default=None,
                      help="Writes output to logfile")
    
    parser.add_option("-d", "--debug",
                      action="store_true",dest="debug",default=False,
                      help="Writes output to logfile")
    
    parser.add_option("-c", "--case",
                      action="store",dest="case",default=None,
                      help="Specifies case directory")
 
    parser.add_option("-w", "--wdir",
                      action="store",dest="wdir",default=None,
                      help="Wind dir to change boundary to")
    
    (options, args) = parser.parse_args()
    
    rootLogger=logging.getLogger('')
    logger=logging.getLogger('setWdir')
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
            
    if options.case!=None:
        casePath=path.abspath(options.case)
    else:
        casePath=os.getcwd()
        
    caseName=path.basename(casePath)
    ch=CaseHandler.CaseHandler(casePath)
    
    wdir=float(options.wdir)
    ch.clearResults()
    logger.info("Modifying bc:s...")  
    ch.modWindDir(ch.initialDir(),wdir)
    logger.info("bc:s modified!")
    
if __name__ == "__main__":
    main()

