import sys
import re
import os
import logging
import subprocess
from os import path
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
from PyFoam.RunDictionary.ParameterFile import ParameterFile
from PyFoam.RunDictionary.SolutionDirectory import SolutionDirectory


class CaseHandler(SolutionDirectory):

    def __init__(self, dirPath, bkpdir=None):
        self.logger = logging.getLogger('BcModifier')
        self.machinesFile = None
        SolutionDirectory.__init__(self, dirPath)
        self.bkpdir = path.join(self.name, bkpdir or 'backupInitialDir')

    def clearResults(self, after=None, before=None):
        """remove all time-directories after/before a certain time. If no time is
        set all times except the initial time are removed"""
        self.reread()

        if before is None:
            mintime = float(self.first)
        else:
            mintime = float(before)

        if after is None:
            maxtime = float(self.first)
        else:
            maxtime = float(after)

        for f in self.times:
            if float(f) < mintime or float(f) > maxtime:
                self.execute("rm -r " + path.join(self.name, f))

        self.reread()

    def execute(self, cmd):
        """Execute the command cmd
        Currently no error-handling is done
        @return: A list with all the output-lines of the execution"""

        proc = subprocess.Popen(
            cmd, shell=True,
            stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True
        )
        proc.wait()
        if proc.stdout is not None:
            return proc.stdout.readlines()
        else:
            return None

    def backUpInitialFields(self):
        if not path.exists(self.bkpdir):
            os.mkdir(self.bkpdir)
            self.execute(
                "cp -r " +
                path.join(self.initialDir(), "*[^.ba]") +
                " " + self.bkpdir + "/"
            )

    def restoreInitialFields(self):
        if not os.path.exists(self.bkpdir):
            print(
                "Cannot restore initial fields, " +
                "backup directory does not exist"
            )
            sys.exit(1)
        else:
            try:
                self.execute("rm -r " + path.join(self.initialDir(), '*'))
                # self.execute("mkdir "+self.initialDir())
                self.execute(
                    "cp -r " + path.join(self.bkpdir, "*") +
                    " " + self.initialDir() + "/"
                )
            except:
                print(
                    "Warning: could not restore initial fields, skipping"
                )

    def createMachinesFile(self, serversCPUsDict):
        machinesPath = path.join(self.name, "machines")
        try:
            fid = open(machinesPath, 'w')
            for server in serversCPUsDict.keys():
                fid.write(
                    server + " cpu=" + str(int(serversCPUsDict[server])) + "\n"
                )
            fid.close()
        except:
            print("Error: could not write machines file")
            sys.exit(1)
        self.machinesFile = machinesPath

    def getFields(self, time):
        timePath = path.join(self.name, str(time))
        fields = os.listdir(timePath)

        def isGood(f):
            if ".bak" in f:
                return False
            if f[0] == "#":
                return False
            if "~" in f:
                return False
            return True

        fields = [
            f for f in fields if isGood(f) and
            path.isfile(path.join(timePath, f))
        ]
        return fields

    def modWindDir(self, time, newDir):

        boundaryPhysTypes = {
            'dirNBnorth': 'inlet', 'dirNBeast': 'side',
            'dirNBsouth': 'outlet', 'dirNBwest': 'side',
            'dirNEBnorth': 'inlet', 'dirNEBeast': 'inlet',
            'dirNEBsouth': 'outlet', 'dirNEBwest': 'outlet',
            'dirEBnorth': 'side', 'dirEBeast': 'inlet',
            'dirEBsouth': 'side', 'dirEBwest': 'outlet',
            'dirSEBnorth': 'outlet', 'dirSEBeast': 'inlet',
            'dirSEBsouth': 'inlet', 'dirSEBwest': 'outlet',
            'dirSBnorth': 'outlet', 'dirSBeast': 'side',
            'dirSBsouth': 'inlet', 'dirSBwest': 'side',
            'dirSWBnorth': 'outlet', 'dirSWBeast': 'outlet',
            'dirSWBsouth': 'inlet', 'dirSWBwest': 'inlet',
            'dirWBnorth': 'side', 'dirWBeast': 'outlet',
            'dirWBsouth': 'side', 'dirWBwest': 'inlet',
            'dirNWBnorth': 'inlet', 'dirNWBeast': 'outlet',
            'dirNWBsouth': 'outlet', 'dirNWBwest': 'inlet',
        }

        dirSymbol = "-"
        if newDir == 0 or newDir == 360:
            dirSymbol = 'N'
        elif newDir > 0 and newDir < 90:
            dirSymbol = 'NE'
        elif newDir == 90:
            dirSymbol = 'E'
        elif newDir > 90 and newDir < 180:
            dirSymbol = 'SE'
        elif newDir == 180:
            dirSymbol = 'S'
        elif newDir > 180 and newDir < 270:
            dirSymbol = 'SW'
        elif newDir == 270:
            dirSymbol = 'W'
        elif newDir > 270 and newDir < 360:
            dirSymbol = 'NW'

        if dirSymbol == '-':
            print("Error: Given new directory is out of range 0-360 degrees")
            sys.exit(1)

        fields = self.getFields(time)
        for field in fields:
            fieldPath = path.join(self.name, str(time), field)
            for boundary in ['north', 'east', 'south', 'west']:
                key = 'dir' + dirSymbol + 'B' + boundary
                boundaryPhysType = boundaryPhysTypes[key]
                if ".gz" in field:
                    fieldDef = self.physTypeToFieldType(
                        boundaryPhysType, field[: -3]
                    )
                else:
                    fieldDef = self.physTypeToFieldType(
                        boundaryPhysType, field
                    )
                self.modFieldBcType(fieldPath, boundary, fieldDef)

    def physTypeToFieldType(self, physType, fieldName):
        if physType == "symmetryPlane":
            return "symmetryPlane"
        if "spec_" in fieldName:
            fieldName = "scalar"

        fields = {
            "U": {
                "wall": """\
                type            uniformFixedValue;
                uniformValue    (0 0 0);
                value           uniform (0 0 0);""",

                "inlet": """
                type            atmBoundaryLayerInletVelocity;
                #include        "include/ABLConditions\"""",

                "outlet": """\
                type            inletOutlet;
                inletValue      uniform (0 0 0);
                value           $internalField;""",

                "side": "   type zeroGradient;"
            },
            "p": {
                "wall": "type zeroGradient;",

                "inlet": "type zeroGradient;",

                "outlet": """\
                type            uniformFixedValue;
                uniformValue    constant $pressure;""",

                "side": "   type zeroGradient;"
            },
            "epsilon": {
                "wall": """\
                type            epsilonWallFunction;
                Cmu             0.09;
                kappa           0.4;
                E               9.8;
                value           $internalField;""",

                "inlet": """\
                type            atmBoundaryLayerInletEpsilon;
                #include        "include/ABLConditions\"""",

                "outlet": """\
                type            inletOutlet;
                inletValue      uniform $turbulentEpsilon;
                value           $internalField;""",

                "side": "   type zeroGradient;"
            },
            "k": {
                "wall": """\
                type            kqRWallFunction;
                value           uniform 0.0;""",

                "inlet": """\
                type            atmBoundaryLayerInletK;
                #include        "include/ABLConditions\"""",

                "outlet": """\
                type            inletOutlet;
                inletValue      uniform $turbulentKE;
                value           $internalField;""",

                "side": "   type zeroGradient;"
            },
            "nut": {
                "wall": """\
                type            nutkAtmRoughWallFunction;
                z0              uniform 0.001;
                value           uniform 0.0;""",

                "inlet": """\
                type            calculated;
                value           uniform 0;""",

                "outlet": """\
                type            calculated;
                value           uniform 0;""",

                "side": "   type zeroGradient;"
            },
        }
        # "scalar": {
        #     "wall": "zeroGradient",
        #     "inlet": "typeuniformFixedValue",
        #     "outlet": "inletOutlet",
        #     "side": "type zeroGradient;"
        # }

        # "nuTilda": {
        #     "wall": "type calculated;",
        #     "inlet": "type calculated;",
        #     "outlet": "type calculated;",
        #     "side": "type calculated;",
        # },
        # "R": {
        #     "wall": """\
        #     type            kqRWallFunction;
        #     value           uniform 0.0;""",
        #     "inlet": "type calculated;",
        #     "outlet": "type calculated;",
        #     "side": "type calculated;"
        # },

        if fieldName not in fields.keys():
            self.logger.warning(
                "Did not find bc rules for field: " + fieldName +
                ", using default zeroGradient"
            )
            return "   type zeroGradient;"

        if physType not in fields[fieldName].keys():
            self.logger.error(
                "Handling of boundary condition: " +
                physType + " not implemented")
            sys.exit(1)

        return fields[fieldName][physType]

    def readFieldBcType(self, fieldPath, patch):
        file = ParameterFile(fieldPath)
        file.readFile()
        exp = re.compile(
            "(" + patch + r"\s*?\n\s*?\{.*?type)(\s*?)(.*?)(;.*?\})",
            re.DOTALL
        )

        bcMatch = exp.search(file.content)

        if bcMatch is None:
            self.logger.debug(
                "Could not find patch: " + patch + " in file: " + file.name
            )
        try:
            patchType = bcMatch.group(3)
        except:
            self.logger.error(
                "Could not get patch type from file: " +
                file.name + " check the file!"
            )
            sys.exit(1)
        return patchType.strip()

    def modFieldBcType(self, fieldPath, patch, newBcType):
        file = ParameterFile(fieldPath)
        try:
            file.readFile()
        except UnicodeDecodeError:
            self.logger.error('Error reading file: %s, check for bad files in the inital directory' % fieldPath)
            sys.exit(1)
        exp = re.compile(patch + r".*?\{(.*?)\}", re.DOTALL)
        file.readFile()
        [newStr, num] = exp.subn(
            "%s\n  {\n%s\n  }\n" % (patch, newBcType),
            file.content
        )

        if num == 0:
            self.logger.error(
                "Patch: " + patch + "not found in " +
                file.name + " could not modify bc"
            )
            sys.exit(1)
        else:
            file.content = newStr
            file.writeFile()
