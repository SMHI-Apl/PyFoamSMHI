#!/usr/bin/env python
# -*- coding: us-ascii -*-
"""Utility to run wind simulations in batch mode."""
from os import path
import os
import time
import sys
import logging
from math import cos, sin
from optparse import OptionParser

# PyFoam modules
from PyFoam.Execution.ConvergenceRunner import ConvergenceRunner
from PyFoam.Execution.UtilityRunner import UtilityRunner
from PyFoam.LogAnalysis.StandardLogAnalyzer import StandardLogAnalyzer
from PyFoam.RunDictionary.ParameterFile import ParameterFile

# PyFoamContrib
from PyFoamSMHI.contrib.ParallelExecutionNSC import LAMMachine
from PyFoamSMHI.contrib import (
    ConvergenceTable, FoamArchive, ControlFile, CaseHandler
)
from PyFoamSMHI.contrib.utilities import generateCf
from PyFoamSMHI.templates.PyFoamWindRunnerCfTemplate import defaultCf


usage = "usage: %prog controlFile [options] "
version = "%prog 1.0"


def dir2vec(wdir):
    wdir_radians = 3.1415926536 / 180 * (90. - wdir)
    x = -1 * cos(wdir_radians)
    y = -1 * sin(wdir_radians)
    return '(%f %f 0)' % (x, y)


def main():
    parser = OptionParser(usage=usage, version=version)
    parser.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="Only print warnings and errors")

    parser.add_option("-t", "--template",
                      action="store", dest="controlfile", default=None,
                      help="Generate default controlfile")

    parser.add_option("-l", "--logfile",
                      action="store", dest="logfile", default=None,
                      help="Writes output to logfile")

    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="Writes output to logfile")

    parser.add_option("-c", "--case",
                      action="store", dest="case", default=None,
                      help="Specifies case directory")

    (options, args) = parser.parse_args()

    rootLogger = logging.getLogger('')
    logger = logging.getLogger('windRunner')
    reportLevel = logging.INFO
    if options.quiet:
        reportLevel = logging.WARNING
    if options.debug:
        reportLevel = logging.DEBUG
    rootLogger.setLevel(reportLevel)

    if options.logfile is None:
        console = logging.StreamHandler()
        console.setLevel(reportLevel)
        formatter = logging.Formatter(
            '%(name)-12s: %(levelname)-8s %(message)s'
        )
        console.setFormatter(formatter)
        rootLogger.addHandler(console)

    if options.controlfile is not None:
        generateCf(options.controlfile, defaultCf)
        print "Wrote default controlfile"
        sys.exit(0)

    if options.logfile is not None:
        logFileName = path.abspath(options.logfile)
        if not path.exists(path.dirname(logFileName)):
            print "Bad argument, directory for logfile does not exist"
            sys.exit(1)
        logfile = logging.FileHandler(logFileName, "w")
        logfile.setLevel(reportLevel)
        formatter = logging.Formatter(
            '%(name)-12s: %(levelname)-8s %(message)s'
        )
        logfile.setFormatter(formatter)
        rootLogger.addHandler(logfile)

    if len(args) != 1:
        parser.error("Incorrect number of arguments")

    cf = ControlFile.ControlFile(fileName=path.abspath(args[0]))

    if options.case is not None:
        casePath = path.abspath(options.case)
    else:
        casePath = os.getcwd()

    caseName = path.basename(casePath)
    ch = CaseHandler.CaseHandler(casePath)

    wspeeds = cf.findScalarList(
        "wspeeds:", optional=False
    )
    wdirs = cf.findScalarList(
        "wdirs:", optional=False
    )
    iterations = cf.findScalar(
        "iterations:", optional=False
    )
    inlet_z0 = cf.findScalarList("z0:", optional=False)
    z0Dict = {}
    for i, wdir in enumerate(wdirs):
        z0Dict[wdir] = inlet_z0[i]

    fieldsToArchive = cf.findStringList(
        "fieldsToArchive:", optional=False
    )
    archiveDirName = cf.findString(
        "flowArchiveDirName:", optional=False
    )
    restoreArchived = cf.findBoolean(
        "restoreArchived:", optional=True, default=False
    )
    nodes = int(cf.findScalar("nodes:", optional=False))
    CPUs = cf.findScalar("CPUs:", optional=True)
    if CPUs is None:
        nprocesses = 16 * nodes
    else:
        nprocesses = int(CPUs)
    # -----------------------------------
    solver = cf.findString("solver:", default="windFoam")
    initCmds = cf.findStringList("initialize:", default=["setLanduse"])
    flowArchive = FoamArchive.FoamArchive(casePath, archiveDirName)
    nwdir = len(wdirs)
    convTable = ConvergenceTable.ConvergenceTable(casePath)

    logger.info("Running windRunner.py")
    logger.info("Setup overview:")
    logger.info(25 * "-")
    logger.info("Case: " + caseName)
    logger.info(25 * "-")
    logger.info("Wind directions are: " + str(wdirs))
    logger.info("Wind speeds are: " + str(wspeeds))
    nruns = nwdir * len(wspeeds)
    logger.info("Total number of runs: " + str(nruns))
    logger.info(25 * "-")
    logger.info("Number of iterations are: " + str(iterations))
    logger.info("Number of nodes are: " + str(nodes))
    logger.info("Fields to be archived: " + str(fieldsToArchive))
    logger.info(50 * "=")

    controlDict = ParameterFile(ch.controlDict())
    # uses include file from 0/include
    ABLConditions = ParameterFile(
        path.join(ch.name, '0', 'include', 'ABLConditions')
    )

    compression = controlDict.readParameter("writeCompression")
    if compression == "compressed" or compression == "on":
        filesToArchive = [field + ".gz" for field in fieldsToArchive]
    else:
        filesToArchive = fieldsToArchive

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
    ch.backUpInitialFields()
    logger.info("Backup made of initial fields")
    for wspeed in wspeeds:
        for wdir in wdirs:
            timeInit = time.time()
            controlDict.replaceParameter(
                "writeInterval",
                str(iterations)
            )
            logger.info(
                "Running calculations for dir: " +
                str(wdir) + " speed: " + str(wspeed)
            )
            logger.info(
                "Time left: " + str(timeLeft/60.0) +
                "min, Time spent: " + str(timeSpent/60.0) + "min"
            )
            logger.info(
                "Estimated time for finish: " +
                str(timeEstimated[:4])
            )
            logger.info(
                "Cases finished: " + str(casesRun) +
                " cases left: " + str(casesLeft))
            logger.info(" ")
            ch.clearResults()

            dirName = "wspeed_" + str(wspeed) + "_wdir_"+str(wdir)
            logger.info("restoreArchived = "+str(restoreArchived))
            if flowArchive.inArchive(dirName=dirName) and not restoreArchived:
                logger.info('Results already in archive, moving on...')
                casesRun += 1
                casesLeft -= 1
                timeCase = time.time() - timeInit
                timeSpent += timeCase
                timeLeft = casesLeft * timeCase
                timeEstimated = time.localtime(time.time() + timeLeft)
                continue               

            logger.info("...Modifying bc:s")
            ch.modWindDir(ch.initialDir(), wdir)
            logger.info("bc:s modified!")

            ABLConditions.replaceParameter(
                "Uref", "%f" % wspeed
            )
            ABLConditions.replaceParameter(
                "flowDir",
                dir2vec(wdir)
            )
            ABLConditions.replaceParameter(
                "z0",
                'uniform %f' % z0Dict[wdir]
            )
            for initCmd in initCmds:
                initUtil = UtilityRunner(
                    argv=[initCmd, "-case", casePath],
                    silent=True,
                    logname=initCmd
                )
                initUtil.start()
                if initUtil.runOK():
                    logger.info(
                        "Successfully finished: %s" % initCmd
                    )
                else:
                    logger.error(
                        "Error when running: %s" % initCmd
                    )
                    sys.exit(1)
            if restoreArchived and \
               flowArchive.inArchive(dirName=dirName):
                logger.info("Restoring archived flow fields")
                flowArchive.restore(
                    dirName, ch.initialDir(), fieldsToArchive
                )
                for filename in fieldsToArchive:
                    flowArchive.getFile(
                        outputFile=path.join(ch.initialDir(), filename),
                        fileName=filename, archiveDirName=dirName
                    )
                logger.info("Restored archived flow fields!")

            if nprocesses > 1:
                if Lam.machineOK():
                    decomposeCmd = "decomposePar"
                    decomposeUtil = UtilityRunner(
                        argv=[decomposeCmd, "-case", casePath],
                        silent=True,
                        logname="decomposePar"
                    )
                    logger.info(
                        "...Decomposing case to run on" +
                        str(Lam.cpuNr())+str(" of processors")
                    )
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
                Lam = None
                logger.info("Serial Run chosen!")

            logger.info("...Running solver for wind field")
            windFoamSolver = ConvergenceRunner(
                StandardLogAnalyzer(),
                argv=[solver, "-case", casePath],
                silent=True,
                lam=Lam,
                logname=solver
            )
            windFoamSolver.start()
            if windFoamSolver.runOK():
                logger.info("Iterations finished for solver")
            else:
                logger.error("Error while running solver")
                sys.exit()

            if nprocesses > 1:
                logger.info("Reconstructing decomposed case...")
                reconstructCmd = "reconstructPar"
                reconstructUtil = UtilityRunner(
                    argv=[reconstructCmd, "-latestTime", "-case", casePath],
                    silent=True,
                    logname="reconstrucPar")
                reconstructUtil.start()
                if reconstructUtil.runOK():
                    logger.info("recunstruction ready!")
                else:
                    logger.error("Error while running recontructPar")
                    sys.exit(1)

                logger.info("Removing decomposed mesh")
                ch.execute("rm -r " + os.path.join(casePath, "processor*"))
                logger.info("Removed decomposed mesh!")

            convTable.addResidual(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                solver,
                "linear_Ux",
                casesRun + 1
            )
            convTable.addResidual(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                solver,
                "linear_Uy",
                casesRun + 1
            )
            convTable.addResidual(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                solver,
                "linear_k",
                casesRun + 1
            )
            convTable.addResidual(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                solver,
                "linear_epsilon",
                casesRun + 1
            )
            convTable.addProbes(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                "U",
                casesRun + 1)
            convTable.addProbes(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                "k",
                casesRun + 1
            )
            convTable.addProbes(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                "epsilon",
                casesRun + 1
            )
            convTable.addProbes(
                "wd_" + str(wdir) + "_ws_" + str(wspeed),
                "p",
                casesRun + 1
            )

            logger.info(
                "Archiving results from directory: %s" % ch.latestDir()
            )
            # save latest concentration result files
            solFiles = [file for file in os.listdir(ch.latestDir())
                        if file in filesToArchive]
            for filename in solFiles:
                dirName = "wspeed_" + str(wspeed) + "_wdir_" + str(wdir)
                flowArchive.addFile(
                    path.join(ch.latestDir(), filename),
                    dirName=dirName
                )

            logger.info(
                "Finished wdir: " + str(wdir) + " wspeed: " +
                str(wspeed) + "Last iter = " + ch.getLast()
            )
            logger.info(" ")
            casesRun += 1
            casesLeft -= 1
            timeCase = time.time() - timeInit
            timeSpent += timeCase
            timeLeft = casesLeft * timeCase
            timeEstimated = time.localtime(time.time() + timeLeft)

            ch.clearResults()
            logger.info(
                "Cleared all result directories exept: %s"
                % (" ".join(ch.getTimes()))
            )
            ch.restoreInitialFields()
            logger.info("Restored initital fields from backup copy")
            # restoring windData dictionary to original state
            ABLConditions.purgeFile()
            convTable.writeProbes()
            convTable.writeResiduals()
            logger.info(
                "Residuals and probes from solver " +
                "written to case/convergence directory"
            )
    # Restoring controlDict to original state
    controlDict.purgeFile()
    logger.info("Finished batch calculation!")

if __name__ == "__main__":
    main()

