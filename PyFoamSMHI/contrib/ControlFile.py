# -*- coding: utf-8 -*-
import re
import sys
import codecs
from os import path


def generateCf(filename,template):
    if not path.exists(path.dirname(filename)):
        print "Error, path for controlfile does not exist"
    if path.exists(filename):
        answer=raw_input("File already exists, replace? (y/n)")
        if answer=="n":
            sys.exit()
        elif answer=="y":
            fid=open(filename,"w")
            fid.write(template)
            fid.close()
        else:
            print "Invalid answer (should be y or n)"
            sys.exit()
    else:
        fid=open(filename,"w")
        fid.write(template)
        fid.close()


class ControlFile:
    def __init__(self,fileName,codec="HP Roman8",removeComments=None):
        self.name=fileName
        self.content=None
        self.units=None
        self.codec=codec
        if removeComments==None or removeComments:
            self.read(removeComments=True)
        elif not removeComments:
            self.read(removeComments=False)

    def read(self,removeComments=True):
        fh=codecs.open(self.name,"r",self.codec)
        self.content=fh.read()
        fh.close()
        if removeComments:
            self.removeComments()

    def write(self):
        fh=codecs.open(self.name,"w",self.codec)
        fh.write(self.content)
        fh.close()            
                
    def findParam(self,parName,optional=False,findAll=False):
        parName=parName.replace(".","\.")
        parName=parName.replace("(","\(")
        parName=parName.replace(")","\)")
        
        if findAll:
            nameExp=re.compile("(\s*?"+parName+")(.*)")
            nameMatch = nameExp.findall(self.content)
        else:
            nameExp=re.compile(r"(\n\s*?)("+parName+")(.*)")
            nameMatch = nameExp.search("\n"+self.content)
        
        if nameMatch==None and not optional:
            print("Error: Could not find parameter '"+parName+"' in controlFile")
            sys.exit()
        elif nameMatch==None and optional:
            return None

        elif findAll:
            res=[]
            for match in nameMatch:
                nameString=match[1]
                nameString=nameString.strip()
                if nameString=="":
                    if optional:
                        res.append(None)
                    else:
                        print("Error: No value given for parameter "+parName+" in template")
                        sys.exit()
                else:
                    res.append(nameString)
            return res
        else:   
            nameString=nameMatch.group(3)
            nameString=nameString.strip()        
            if nameString=="":
                if optional:
                    return None
                else:
                    print("Error: No value given for parameter "+parName+" in template")
                    sys.exit()
            else:
                return nameString

    def findInt(self,parName,default=None,optional=False):
        par=self.findParam(parName,optional)        
        if par==None :
            if not optional:
                print("Error: No parameter named '"+ parName+ "' found in controlfile")
                sys.exit()
            else:
                return default
        try:
            par=int(par)
            return par
        except:
            print("Error: Parameter named '"+ parName+ "' in controlfile should be a scalar")
            sys.exit()

    def findFloat(self,parName,default=None,optional=False):
        par=self.findParam(parName,optional)        
        if par==None :
            if not optional:
                print("Error: No parameter named '"+ parName+ "' found in controlfile")
                sys.exit()
            else:
                return default
        try:
            par=float(par)
            return par
        except:
            print("Error: Parameter named '"+ parName+ "' in controlfile should be a scalar")
            sys.exit()


    def findScalar(self,parName,default=None,optional=False):
        return self.findFloat(parName,default,optional)
        
    def findBoolean(self,parName,default=None,optional=False):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print("Error: No parameter named '"+ parName+ "' found in controlfile")
                sys.exit()
            else:
                return default

        if par.lower() =="true":
            return True
        elif par.lower() =="false":
            return False
        else:
            print("Error: Parameter named '"+ parName+ "' in controlfile should be a either True or False")
            sys.exit()
        
    def findString(self,parName,default=None,optional=False):
        par=self.findParam(parName,optional)
        if par==None:
            if not optional:
                print("Error: No parameter named '"+ parName+ "' found in controlfile")
                sys.exit()
            else:
                return default
        if "\"" in par:
            par=par.replace("\"","")
        return par        

    def findAllString(self,parName,default=None,optional=False):
        matchList=self.findParam(parName,findAll=True)
        if matchList[0]==None:
            return default
        return matchList

    def findAllInt(self,parName,default=None,optional=False):
        matchList=self.findParam(parName,optional=optional,findAll=True)
        if matchList[0]==None:
            return default
        return map(int,matchList)

    def findScalarList(self,parName,default=None,optional=False,sep=None):
        return self.findFloatList(parName,default,optional,sep)
    
    def findFloatList(self,parName,default=None,optional=False,sep=None):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print("Error: No parameter named '"+ parName+ "' found in controlfile")
                sys.exit()
            else:
                return default
        if sep==None:
            stringList=par.split()
        else:
            stringList=par.split(sep)
            
        floats=[]
        for post in stringList:
            try:
                floats.append(float(post))
            except TypeError:
                print("Error: Parameter: "+parName+" in controlFile should be a list of numbers")
                sys.exit()
        return floats

    def findIntList(self,parName,default=None,optional=False,sep=None):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print("Error: No parameter named '"+ parName+ "' found in controlfile")
                sys.exit()
            else:
                return default

        if sep==None:
            stringList=par.split()
        else:
            stringList=par.split(sep)

        floats=[]
        for post in stringList:
            try:
                floats.append(int(post))
            except TypeError:
                print("Error: Parameter: "+parName+" in controlFile should be a list of numbers")
                sys.exit()
        return floats
    
    def findStringList(self,parName,default=None,optional=False,sep=None):
        par=self.findParam(parName,optional)
        if par==None :
            if not optional:
                print("Error: No parameter named '"+ parName+ "' found in controlfile")
                sys.exit()
            else:
                return default
            
        if "\"" in par:            
            par=par.replace(" ","__*__")#temporarily replacing spaces with a rare symbol, not to have clashes with symbols in string
            par=par.replace("\""," ")
            stringList=par.split() #Splitting on spaces, not to have empty strings when there are multiple separators
            result=[]
            for i in range(len(stringList)):
                stringList[i]=stringList[i].replace("__*__"," ")
                if not stringList[i].isspace():
                    result.append(stringList[i])
        else:
            if sep==None:
                result=par.split()
            else:
                result=par.split(sep)
        return result

    def findExistingPath(self,parName,default=None,optional=False):
        par=self.findString(parName,default=default,optional=optional)
        if par==None :
            if not optional:
                print("Error: No parameter named '"+parName+ "' found in controlfile")
                sys.exit()
            else:
                return default
        if not path.exists(par): 
            if not optional:
                print("Error: Parameter: '"+ parName+ "' in controlFile points out a path that does not exist")
                sys.exit()
            else:
                print("Warning: Optional parameter: '"+ parName+ "' in controlFile points out a path that does not exist")
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


    def setParam(self,parName,val):
        valStr=""
        if isinstance(val,str):
            valStr=val
        elif isinstance(val,list):
            for v in val:
                valStr+=" "+str(v)
        else:
            valStr=str(val)
        
        nameExp=re.compile("("+parName+")(.*)")
        self.content = re.sub(nameExp,r'\1'+" "+valStr,self.content)
        self.write()
        
