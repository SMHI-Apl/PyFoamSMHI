import os,sys,glob,math
import pdb
class ConvergenceTable:
    def __init__(self,caseDir):
        self.probes={}
        self.residuals={}
        self.caseDir=caseDir
        self.resDir=os.path.join(self.caseDir,"convergence")
        if not os.path.exists(self.resDir):
            os.mkdir(self.resDir)

    def addProbes(self,runId,fieldName,runIndex):
        runId=str(runIndex)+"_"+runId
        probeDirs=[]
        probeDir=os.path.join(self.caseDir,"probes")
        if os.path.exists(probeDir):
            probeDirs.append(probeDir)

#        processors=glob.glob(os.path.join(self.caseDir,"processor*"))
#        for proc in processors:
#            probeDir=os.path.join(proc,"probes")
#            if os.path.exists(probeDir):
#                probeDirs.append(probeDir)
        print str(probeDirs)
        records={}
        for pdir in probeDirs:
            times=glob.glob(os.path.join(pdir,"*"))
            for i in range(len(times)):
                times[i]=os.path.basename(times[i])
            time=0
            for t in times:
                if int(t)>time:
                    time=int(t)

            probeFile=os.path.join(probeDir,str(time),fieldName)
            if os.path.exists(probeFile):
                try:
                    pf=open(probeFile,'r')
                    lines=pf.readlines()
                    pf.close()
                except:
                    print "Could not read probe file"
                    sys.exit("Could not read probe file")     
                nprobes=len(lines[0].split()[2:])

                for pInd in range(nprobes):
                    probeCoordinates=""
                    probeCoordinates+=lines[0].split()[pInd+2]+"_"
                    probeCoordinates+=lines[1].split()[pInd+2]+"_"
                    probeCoordinates+=lines[2].split()[pInd+2]        
                    record=[]
                    for line in lines[4:len(lines)]:
                        if '(' in line:
                            line=line.replace('(','')
                            line=line.replace(')','')
                            line=line.split()
                            vec=line[1+pInd*3:4+pInd*3]
                            Ux= float(vec[0])
                            Uy= float(vec[1])
                            Uz= float(vec[2])
                            #Calculating Umag
                            data=math.sqrt(pow(Ux,2)+pow(Uy,2)+pow(Uz,2))
                        else:
                            line=line.split()
                            data=float(line[1+pInd])
                        record.append(data)                        
                    records[probeCoordinates]=record
        
        
        for probe in records.keys():
            key=fieldName+"_"+probe
            if key in self.probes:
                fieldProbeDict=self.probes[key]
            else:
                fieldProbeDict={}
            fieldProbeDict[runId]=records[probe]
            self.probes[key]=fieldProbeDict
    
    
    def addResidual(self,runId,solverName,fieldName,runIndex):
        runId=str(runIndex)+"_"+runId
        residualFile=os.path.join(self.caseDir,solverName+".analyzed",fieldName)
        if os.path.exists(residualFile):
            try:
                pf=open(residualFile,'r')
                lines=pf.readlines()
                pf.close()
            except:
                print "Could not read residual file"
                sys.exit("Could not read residual file")     
        
            record=[]
            for line in lines[1:len(lines)]:
                line=line.split('\t')
                data=float(line[1])
                record.append(data)
        
        
            key=fieldName+"_"+solverName
            if key in self.residuals:
                fieldSolverDict=self.residuals[key]
            else:
                fieldSolverDict={}
            fieldSolverDict[runId]=record
            self.residuals[key]=fieldSolverDict
        
    def writeProbes(self):
        for key in self.probes.keys():
            #Creating a list of runs sorted by run index
            sortList=[]
            for runId in self.probes[key].keys():
                sortList.append(int(runId.split("_")[0]))
            sortList.sort()
            runKeys=[]
            for post in sortList:     
                for runId in self.probes[key].keys():
                    if int(runId.split("_")[0])==post:
                        runKeys.append(runId)
            
            #Opening a output file specifik for field and probe
            fileName=os.path.join(self.resDir,key+"_probe.asc")
            try:
                fid=open(fileName,'w')
                fid.write("Time\t")
                for run in runKeys[:-1]:
                    fid.write(run+"\t")  
                fid.write(runKeys[-1]+"\n")
            except:
                print "Could not write probe table"
                sys.exit("Could not write probe table") 
                
            data=[]
            nrows=0
            time=1
            for run in runKeys:
                data.append(self.probes[key][run])
                nrows=max(len(self.probes[key][run]),nrows)
            for row in range(nrows):
                fid.write(str(time)+"\t")
                time+=1
                for col in range(len(data)-1):
                    if row<len(data[col]):
                        value=data[col][row]
                        fid.write(str(value)+"\t")
                    else:
                        fid.write("\t")
                if row<len(data[-1]):
                    value=data[-1][row]
                    fid.write(str(value)+"\n")
                else:
                    fid.write("\n")
            fid.close()
            
    def writeResiduals(self):
        for key in self.residuals.keys():
            #Creating a list of runs sorted by run index
            sortList=[]
            for runId in self.residuals[key].keys():
                sortList.append(int(runId.split("_")[0]))
            sortList.sort()
            runKeys=[]
            for post in sortList:     
                for runId in self.residuals[key].keys():
                    if int(runId.split("_")[0])==post:
                        runKeys.append(runId)
            
            #Opening a output file specifik for field and solver
            fileName=os.path.join(self.resDir,key+"_residual.asc")
            try:
                fid=open(fileName,'w')
                fid.write("Time\t")
                for run in runKeys[:-1]:
                    fid.write(run+"\t")
                fid.write(runKeys[-1]+"\n")
            except:
                print "Could not write residual table"
                sys.exit("Could not write residual table") 
                
            data=[]
            nrows=0
            time=1
            for run in runKeys:
                data.append(self.residuals[key][run])
                nrows=max(len(self.residuals[key][run]),nrows)
            for row in range(nrows):
                fid.write(str(time)+"\t")
                time+=1
                for col in range(len(data)-1):
                    if row<len(data[col]):
                        value=data[col][row]
                        fid.write(str(value)+"\t")
                    else:
                        fid.write("\t")
                if row<len(data[-1]):
                    value=data[-1][row]
                    fid.write(str(value)+"\n")
                else:
                    fid.write("\n")
            fid.close()
                      
            
            
