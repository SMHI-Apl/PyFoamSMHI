#!/usr/bin/env python
"""Set bc to represent given wind direction, or restore fields from archive."""

#Python standard modules
from os import path
import os
import glob
import time
import sys
import logging
import argparse

#PyFoam modules
from PyFoam.Execution.UtilityRunner import UtilityRunner
from PyFoam.RunDictionary.SolutionFile import SolutionFile
from PyFoam.RunDictionary.ParameterFile import ParameterFile

#PyFoamContrib
from PyFoamSMHI.contrib import FoamArchive, CaseHandler, FoamArchive
from PyFoamSMHI.templates.PyFoamWindRunnerCfTemplate import defaultCf
from PyFoamSMHI.contrib.utilities import (
    VerboseAction,
    LogFileAction
)

log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-v',
        action=VerboseAction, dest='loglevel', default=logging.INFO,
        help='increase verbosity in terminal',
    )
    
    parser.add_argument(
        '-l', metavar='logfile',
        action=LogFileAction, dest='logfile',
        help='write verbose output to logfile',
    )

    parser.add_argument(
        "-a", "--archiveDir",
        action="store", dest="archiveDir", default=None,
        help="Path to archive directory to fetch results from"
    )

    parser.add_argument(
        "-c", "--case",
        action="store",dest="case",default=None,
        help="Specifies case directory"
    )
 
    parser.add_argument(
        "--wdir",
        action="store",dest="wdir",default=None, type=float,
        help="Wind dir to change boundary to or restore from archive"
    )

    parser.add_argument(
        "--wspeed",
        action="store",dest="wspeed",default=None, type=float,
        help="Wind speed to restore from archive"
    )

    args = parser.parse_args()
                
    if args.case!=None:
        casePath=path.abspath(args.case)
    else:
        casePath=os.getcwd()
        
    caseName=path.basename(casePath)
    ch=CaseHandler.CaseHandler(casePath)

    ch.clearResults()
    log.info("Modifying bc:s...")  
    ch.modWindDir(ch.initialDir(),args.wdir)
    log.info("bc:s modified!")

    if args.archiveDir is not None:
        if args.wspeed is None or args.wdir is None:
            log.error('Must specify both -wdir and -wspeed to restore fields from archive')
            sys.exit(1)            
        
        flowArchive = FoamArchive.FoamArchive(casePath, args.archiveDir)
        dirName = "wspeed_%3.1f_wdir_%3.1f" % (args.wspeed, args.wdir)
        if not flowArchive.inArchive(dirName=dirName):
            log.error("Missing flow files in dir: %s"  % dirName)
        else:
            flowArchive.restore(dirName, ch.initialDir())
            
    
if __name__ == "__main__":
    main()

