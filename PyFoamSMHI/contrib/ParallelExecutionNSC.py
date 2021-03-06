# -*- coding: utf-8 -*-
"""Things that are needed for convenient parallel Execution"""

import commands
from PyFoam.Basics.Utilities import Utilities
from PyFoam.FoamInformation import foamMPI
from PyFoam.Error import error, warning, debug
from PyFoam import configuration as config

from os import path, environ, system


class LAMMachine(Utilities):
    """Wrapper class for starting an stopping a LAM-Machine"""

    def __init__(self, machines=None, nr=None):
        """@param machines: Name of the file with the machine information
        @param nr: Number of processes"""

        Utilities.__init__(self)

        self.stop()

        if machines == "":
            machines = None

        if machines is None and foamMPI() == "LAM":
            error("Machinefile must be specified for LAM")

        if machines is None and nr is None:
            error(
                "Either machinefile or Nr of CPUs must be  " +
                "specified for MPI type",
                foamMPI()
            )

        self.mFile = machines
        self.procNr = nr

        self.boot()
        if not self.machineOK():
            error("Error: LAM was not started")

    def machineOK(self):
        """Check whether the LAM machine was properly booted"""
        if self.running:
            if(foamMPI() == "LAM"):
                if self.cpuNr() <= 0:
                    self.running = False

        return self.running

    def stop(self):
        """Stops a LAM-machine (if one is running)"""
        self.running = False
        if(foamMPI() == "LAM"):
            self.execute("lamhalt -v")

    def boot(self):
        """Boots a LAM-machine using the machine-file"""
        if foamMPI() == "LAM":
            warning("LAM is untested. Any Feedback most welcome")
            self.execute("lamboot -s -v "+self.mFile)
            self.running = True
        elif 'MPI' in foamMPI():
            self.running = True
        else:
            error(" Unknown or missing MPI-Implementation: "+foamMPI())

    def cpuNr(self):
        if(foamMPI() == "LAM"):
            if self.running:
                lines = self.execute("lamnodes")
                nr = 0
                for l in lines:
                    tmp = l.split(':')
                    if len(tmp) > 1:
                        nr += int(tmp[1])
                return nr
            else:
                return -1
        elif 'MPI' in foamMPI():
            return self.procNr

    def buildMPIrun(self, argv, expandApplication=True):
        """Builds a list with a working mpirun command (for that MPI-Implementation)
        @param argv: the original arguments that are to be wrapped
        @param expandApplication: Expand the
        @return: list with the correct mpirun-command"""

        mpirun = ["mpprun"]

        progname = argv[0]
        if expandApplication:
            stat, progname = commands.getstatusoutput('which '+progname)
            if stat:
                progname = argv[0]
                warning(
                    "which can not find a match for",
                    progname, ". Hoping for the best"
                )

        mpirun += [progname] + argv[1:3] + ["-parallel"] + argv[3:]

        if config().getdebug("ParallelExecution"):
            debug("MPI:", foamMPI())
            debug("Arguments:", mpirun)
            system("which mpirun")
            system("which rsh")
            debug("Environment", environ)
            for a in mpirun:
                if a in environ:
                    debug("Transfering variable", a, "with value", environ[a])

        return mpirun

    def writeMetis(self, sDir):
        """Write the parameter-File for a metis decomposition
        @param sDir: Solution directory
        @type sDir: PyFoam.RunDictionary.SolutionDirectory"""

        params = "method metis;\n"

        self.writeDecomposition(sDir, params)

    def writeScotch(self, sDir):
        """Write the parameter-File for a scotch decomposition
        @param sDir: Solution directory
        @type sDir: PyFoam.RunDictionary.SolutionDirectory"""

        params = "method scotch;\n"

        self.writeDecomposition(sDir, params)

    def writeSimple(self, sDir, direction):
        """Write the parameter-File for a metis decomposition
        @param sDir: Solution directory
        @type sDir: PyFoam.RunDictionary.SolutionDirectory
        @param direction: direction in which to decompose (0=x, 1=y, 2=z)"""

        params = "method simple;\n"
        params += "\nsimpleCoeffs\n{\n\t n \t ("
        if direction == 0:
            params += str(self.cpuNr()) + " "
        else:
            params += "1 "
        if direction == 1:
            params += str(self.cpuNr()) + " "
        else:
            params += "1 "
        if direction == 2:
            params += str(self.cpuNr())
        else:
            params += "1"
        params += ");\n\t delta \t 0.001;\n}\n"

        self.writeDecomposition(sDir, params)

    def writeDecomposition(self, sDir, par):
        """Write parameter file for a decomposition
        @param par:Parameters specific for that kind of decomposition
        @type par:str
        @param sDir: Solution directory
        @type sDir: PyFoam.RunDictionary.SolutionDirectory"""

        f = open(path.join(sDir.systemDir(), "decomposeParDict"), "w")
        self.writeDictionaryHeader(f)
        f.write("// * * * * * * * * * //\n\n")
        f.write("numberOfSubdomains "+str(self.cpuNr())+";\n\n")
        f.write(par)
        f.write("\n\n// * * * * * * * * * //")
        f.close()
