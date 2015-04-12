import sys, re, os, logging
from os import path, popen4
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
from PyFoam.RunDictionary.ParameterFile import ParameterFile
from PyFoam.RunDictionary.SolutionDirectory import SolutionDirectory
import pdb

class CaseHandler(SolutionDirectory):
    
    def __init__(self, dirPath):
        self.logger=logging.getLogger('BcModifier')
        self.machinesFile=None
        SolutionDirectory.__init__(self,dirPath)
                
    def clearResults(self,after=None,before=None):
        """remove all time-directories after/before a certain time. If no time is
        set all times except the initial time are removed"""
        self.reread()
        
        if before==None:
            mintime=float(self.first)
        else:
            mintime=float(before)
        
        if after==None:
            maxtime=float(self.first)
        else:
            maxtime=float(after)
            
        for f in self.times:
            if float(f)<mintime or float(f)>maxtime:
                self.execute("rm -r "+path.join(self.name,f))
        
        self.reread()


    def execute(self,cmd):
        """Execute the command cmd        
        Currently no error-handling is done
        @return: A list with all the output-lines of the execution"""
        rein, raus=popen4(cmd)
        tmp=raus.readlines()
        return tmp

    def backUpInitialFields(self):
        bgPath=path.join(self.name,"backUpInitialFields")
        if not path.exists(bgPath):
            os.mkdir(bgPath)
        self.execute("cp "+path.join(self.initialDir(),"*[^.ba]")+" "+bgPath+"/")
        #self.execute("cp "+path.join(case.constantDir(),"polyMesh","boundary")+" "+bgPath+"/")

    def restoreInitialFields(self):
        bgPath=path.join(self.name,"backUpInitialFields")
        if not os.path.exists(bgPath):
            logger.error("Cannot restore initial fields, backup directory does not exist")
            sys.exit()
        else:
            try:
                #self.execute("rm -r "+self.initialDir())
                if not os.path.exists(self.initialDir()):
                    self.execute("mkdir "+self.initialDir())    
                self.execute("cp "+path.join(bgPath,"*")+" "+self.initialDir()+"/")
                    
                #self.execute("cp "+path.join(bgPath,"boundary")+" "+path.join(case.constantDir(),"polyMesh","boundary"))
            except:
                logger.warning("Warning: could not restore initial fields, continuing anyway")

    def createMachinesFile(self,serversCPUsDict):
        machinesPath=path.join(self.name,"machines")
        try:
            fid=open(machinesPath,'w')
            for server in serversCPUsDict.keys():
                fid.write(server+" cpu="+str(int(serversCPUsDict[server]))+"\n")
            fid.close()
        except:
            logger.error("Could not write machines file")
            sys.exit()
        self.machinesFile=machinesPath
        
    def getFields(self, time):
        timePath=path.join(self.name,str(time))
        fields=os.listdir(timePath)
        def isGood(f):
            if ".bak" in f:
                return False
            if f[0] == "#":
                return False
            if "~" in f:
                return False
            return True
        
        fields=[f for f in fields if isGood(f) and path.isfile(path.join(timePath,f))]
        return fields
        
    def modWindDir(self,time,newDir):
        boundaryTypes={
                     'dirNBnorth':'patch','dirNBeast':'zeroGradient','dirNBsouth':'patch','dirNBwest':'zeroGradient',
                     'dirNEBnorth':'patch','dirNEBeast':'patch','dirNEBsouth':'patch','dirNEBwest':'patch',
                     'dirEBnorth':'zeroGradient','dirEBeast':'patch','dirEBsouth':'zeroGradient','dirEBwest':'patch',
                     'dirSEBnorth':'patch','dirSEBeast':'patch','dirSEBsouth':'patch','dirSEBwest':'patch',
                     'dirSBnorth':'patch','dirSBeast':'zeroGradient','dirSBsouth':'patch','dirSBwest':'zeroGradient',
                     'dirSWBnorth':'patch','dirSWBeast':'patch','dirSWBsouth':'patch','dirSWBwest':'patch',
                     'dirWBnorth':'zeroGradient','dirWBeast':'patch','dirWBsouth':'zeroGradient','dirWBwest':'patch',
                     'dirNWBnorth':'patch','dirNWBeast':'patch','dirNWBsouth':'patch','dirNWBwest':'patch',
                    }
    
        boundaryPhysTypes={
                     'dirNBnorth':'inlet','dirNBeast':'side','dirNBsouth':'outlet','dirNBwest':'side',
                     'dirNEBnorth':'inlet','dirNEBeast':'inlet','dirNEBsouth':'outlet','dirNEBwest':'outlet',
                     'dirEBnorth':'side','dirEBeast':'inlet','dirEBsouth':'side','dirEBwest':'outlet',
                     'dirSEBnorth':'outlet','dirSEBeast':'inlet','dirSEBsouth':'inlet','dirSEBwest':'outlet',
                     'dirSBnorth':'outlet','dirSBeast':'side','dirSBsouth':'inlet','dirSBwest':'side',
                     'dirSWBnorth':'outlet','dirSWBeast':'outlet','dirSWBsouth':'inlet','dirSWBwest':'inlet',
                     'dirWBnorth':'side','dirWBeast':'outlet','dirWBsouth':'side','dirWBwest':'inlet',
                     'dirNWBnorth':'inlet','dirNWBeast':'outlet','dirNWBsouth':'outlet','dirNWBwest':'inlet',
                    }
        
        dirSymbol="-"
        if newDir== 0 or newDir == 360:            
            dirSymbol= 'N'
        if newDir>0 and newDir<90:
            dirSymbol ='NE'
        if newDir==90:
            dirSymbol ='E'
        if newDir>90 and newDir<180:
            dirSymbol ='SE'
        if newDir==180:
            dirSymbol ='S'
        if newDir>180 and newDir<270:
            dirSymbol ='SW'
        if newDir==270:
            dirSymbol ='W'
        if newDir>270 and newDir<360:
            dirSymbol='NW'
    
        if dirSymbol == '-':
            logger.error("Given new directory is out of range 0-360 degrees")
    
        fileName=os.path.basename(self.name)
    
        boundaryFile=ParsedParameterFile(self.boundaryDict(),debug=False,boundaryDict=True)
        bnd=boundaryFile.content
        if type(bnd)!=list:
            logger.error("Problem with boundary file (not a list)")
            sys.exit()
    
        for boundary in ['north','east','south','west']:
            key='dir'+dirSymbol+'B'+boundary
            boundaryType=boundaryTypes[key]
        
            found=False
            for val in bnd:
                if val==boundary:
                    found=True
                elif found:
                    val["type"]=boundaryType
                    break
    
            if not found:
                logger.error("Boundary"+bName+"not found in"+bnd[::2])
                sys.exit()
        boundaryFile.writeFile()
    
        fields=self.getFields(time)            
        for field in fields:
            
            fieldPath=path.join(self.name,str(time),field)
            for boundary in ['north','east','south','west']:
                key='dir'+dirSymbol+'B'+boundary
                boundaryPhysType=boundaryPhysTypes[key]
                if ".gz" in field:
                    fieldType=self.physTypeToFieldType(boundaryPhysType,field[:-3])
                else:
                    fieldType=self.physTypeToFieldType(boundaryPhysType,field)
                self.modFieldBcType(fieldPath, boundary,fieldType)
    
    
    def physTypeToFieldType(self,physType,fieldName):
        if physType=="symmetryPlane":
            return "symmetryPlane"
        if "spec_" in fieldName:
            fieldName = "scalar"
        
        fields={
            "U":{"wall":"fixedValue", "inlet":"fixedValue","outlet":"zeroGradient","side":"zeroGradient"},
                "p":{"wall":"zeroGradient", "inlet":"zeroGradient", "outlet":"fixedValue","side":"zeroGradient"},
                "epsilon":{"wall":"epsilonWallFunction", "inlet":"fixedValue","outlet":"zeroGradient","side":"zeroGradient"},
                "k":{"wall":"kQRWallFunction", "inlet":"fixedValue","outlet":"zeroGradient","side":"zeroGradient"},
                "nuTilda":{"wall":"zeroGradient", "inlet":"fixedValue","outlet":"zeroGradient","side":"zeroGradient"},
                "R":{"wall":"kQRWallFunction", "inlet":"fixedValue","outlet":"zeroGradient","side":"zeroGradient"},
                "omega":{"wall":"omegaWallFunction", "inlet":"fixedValue","outlet":"zeroGradient","side":"zeroGradient"},
                "nut":{"wall":"nutWallFunction", "inlet":"zeroGradient","outlet":"zeroGradient","side":"zeroGradient"},
                "scalar":{"wall":"zeroGradient", "inlet":"fixedValue","outlet":"zeroGradient","side":"zeroGradient"}
                }
        
        if fieldName not in fields.keys():
            self.logger.warning("Did not find bc rules for field: "+fieldName+", using default zeroGradient")
            return "zeroGradient"
        
        if physType not in fields[fieldName].keys():
            self.logger.error("Handling of boundary condition: "+physType+" not implemented")
            sys.exit()

        return fields[fieldName][physType]
    
    
    def readFieldBcType(self, fieldPath, patch):
        file=ParameterFile(fieldPath)
        file.readFile()
        exp=re.compile("("+patch+r"\s*?\n\s*?\{.*?type)(\s*?)(.*?)(;.*?\})",re.DOTALL)
        
        bcMatch = exp.search(file.content)
    
        if bcMatch==None:
            self.logger.debug("Could not find patch: "+patch+" in file: "+file.name)
    
        try:
            patchType=bcMatch.group(3)
        except:
            self.logger.error("Could not get patch type from file: "+file.name+" check the file!")
            sys.exit()
        return patchType.strip()
        

    def modFieldBcType(self, fieldPath, patch, newBcType):
        file=ParameterFile(fieldPath)
        file.readFile()
        oldBc=self.readFieldBcType(fieldPath,patch)
    
        fieldType=file.readParameter("class")
        fieldName=file.readParameter("object")
        
        if fieldType=="volVectorField":
            valueStr=" uniform (0 0 0);"
        elif fieldType=="volTensorField":
            valueStr=" uniform (0 0 0 0 0 0 0 0 0);"
        elif fieldType=="volSymmTensorField":
            valueStr=" uniform (0 0 0 0 0 0);"
        else:
            if fieldName == "k": 
                valueStr = " uniform 0.1;"
            elif fieldName == "epsilon":
                valueStr = " uniform 0.01;"
            else:
                valueStr = " uniform 0;"
        
        if oldBc=="fixedValue":
            exp=re.compile("("+patch+r".*?type\s*?)(\w*?)(;)(.*?value.*?;)",re.DOTALL)
        else:    
            exp=re.compile("("+patch+r"\s*?\n\s*?\{.*?type\s*?)(\w*?)(\s*?;)",re.DOTALL)
        
        file.readFile()

        if newBcType=="fixedValue" or "WallFunction" in newBcType:
            [newStr, num]=exp.subn(r'\1'+newBcType+r'\3'+'\n        value'+valueStr, file.content)
        else:
            [newStr, num]=exp.subn(r'\1'+newBcType+r'\3', file.content)
        
        
    
        if num==0:
            self.logger.error("Patch: "+patch+"not found in "+file.name+" could not modify bc") 
            sys.exit()
        else:
            file.content=newStr
            file.writeFile()
    
