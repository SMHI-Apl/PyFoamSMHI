import sys, re, os, logging, glob
from os import path
from PyFoam.RunDictionary.ParameterFile import ParameterFile

class ExtendedParameterFile(ParameterFile):

    def __init__(self, name, backup=False):
        self.logger=logging.getLogger('ExtendedParameterFile')
        ParameterFile.__init__(self,name,backup)

    def replaceParameterList(self,parameter,newList):
        """writes the list of parameter values

        @param parameter: name of the parameter
        @param newList: the new value list
        """
        self.readFile()
        (fh,fn)=self.makeTemp()
        fh=open(fn,'w')

        exp=re.compile("(.*"+parameter+".*?"+r"\("+")(.*?)("+r"\);.*)",re.DOTALL)
        expMatch=exp.search(self.content)
        self.logger.info(str(newList))

        if expMatch==None:
            logger.error("Missing parameter: "+parameter+" in dictionary: "+self.name)
            sys.exit()
        else:
            listString="\n"
            for val in newList:
                try:
                    listString+=str(val)+"\n"
                except:
                    logger.error("Cannot write parameter: "+parameter+" to dictionary, cannot convert to string...")
                    sys.exit()
            fh.write(expMatch.group(1))
            fh.write(listString)
            fh.write(expMatch.group(3))
            fh.close()
            os.rename(fn,self.name)
