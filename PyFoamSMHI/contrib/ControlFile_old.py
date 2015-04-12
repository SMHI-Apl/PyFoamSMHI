import re,sys
from string import split
from os import path

class ControlFile:
    def __init__(self,fileName):
        self.name=fileName
        self.content=None
        self.units=None
        self.read()

    def read(self):
        fh=open(self.name,'r')
        self.content=fh.read()
        fh.close()    
        self.removeComments()
                
    def findParam(self,parName,optional=True):
        nameExp=re.compile("("+parName+")(.*)")
        nameMatch = nameExp.search(self.content)
        
        if nameMatch==None and not optional:
                sys.exit("Error: Could not find parameter '"+parName+"' in controlFile")
        elif nameMatch==None and optional:
            return None
        else:
            nameString=nameMatch.group(2)
            namelist=split(nameString)
            if len(namelist)>1:
                return namelist
            elif len(namelist)==1:
                return namelist[0]
            else:
                return None
    
    def findScalar(self,parName,default=None,optional=True):
        par=self.findParam(parName,optional)        
        if par==None :
            if not optional:
                print "No parameter named '", parName, "' found in controlfile"
                sys.exit()
            else:
                return default
        try:
            par=float(par)
            return par
        except:
            print "Error: Parameter named '", parName, "' in controlfile should be a scalar"
            sys.exit()
        
    def findBoolean(self,parName,default=None,optional=True):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print "No parameter named '", parName, "' found in controlfile"
                sys.exit()
            else:
                return default

        if par in ("true","True","TRUE"):
            return True
        elif par in ("false","False","FALSE"):
            return False
        else:
            print "Error: Parameter named '", parName, "' in controlfile should be a either True or False"
            sys.exit()
        
    def findString(self,parName,default=None,optional=True):
        par=self.findParam(parName,optional)
        if par==None:
            if not optional:
                print "No parameter named '", parName, "' found in controlfile"
                sys.exit()
            else:
                return default
        return par        
    
    def findScalarList(self,parName,default=None,optional=True):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print "No parameter named '", parName, "' found in controlfile"
                sys.exit()
            else:
                return default
        if type(par)!=list and par!=None:
            try:
                par=[par]
            except:
                print "Error: Parameter named '", parName, "' in controlfile should be a scalar list"
                sys.exit()
        scalars=[]
        for post in par:
            try:
                scalars.append(float(post))
            except:
                print "Error: Parameter named '", parName, "' in controlfile should be a scalar list"
                sys.exit()
        return scalars
    
    def findStringList(self,parName,default=None,optional=True):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print "No parameter named '", parName, "' found in controlfile"
                sys.exit()
            else:
                return default
            
        if type(par) !=list:
            par=[par]
        return par

    def findExistingPath(self,parName,default=None,optional=True):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print "No parameter named '", parName, "' found in controlfile"
                sys.exit()
            else:
                return default
        try:
            if type(par)==list:
                raise IOError
            if not path.exists(par):
                raise OSError
        except IOError:
            print "Parameter: '", parName, "' in controlFile points out an invalid path (with spaces)"
            print "Found parameter is: ", str(par)
            if not optional:
                sys.exit()
        except OSError:
            print "Parameter: '", parName, "' in controlFile points out a path that does not exist"          
            if not optional:
                sys.exit()
        return par

    def removeComments(self):
        lines=self.content.split("\n")
        unCommented=[]
        for line in lines:
            line=line.strip()
            if len(line)>0:
                if line[0]!="#":
                    unCommented.append(line)
        self.content="\n".join(unCommented)
        
