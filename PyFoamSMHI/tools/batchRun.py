#!/usr/bin/env python
import os, subprocess, sys
from os import path
from optparse import OptionParser
from PyFoamContrib import ControlFile

usage = "usage: %prog controlFile [options] "
version="%prog 1.0"

        
def main():
    parser=OptionParser(usage= usage, version=version)

    parser.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="Only print warnings and errors")    
    
    parser.add_option("-l", "--logfile",
                      action="store",dest="logfile",default=None,
                      help="Writes output to logfile")
    
    parser.add_option("-d", "--debug",
                      action="store_true",dest="debug",default=False,
                      help="Activates debug output")
    
    parser.add_option("-c", "--case",
                      action="store",dest="case",default=None,
                      help="Specifies case directory")

    (options, args) = parser.parse_args()
            
    if len(args)!=1:
        parser.error("Incorrect number of arguments")
        
    cf=ControlFile.ControlFile(fileName=path.abspath(args[0]))

    jobname=cf.findString("jobname:",optional=False)
    nodes=cf.findScalar("nodes:",optional=True)
    CPUs=cf.findScalar("CPUs:",optional=True)
    walltime=cf.findString("walltime:",optional=False)
    mem=cf.findScalar("mem:",optional=True)
    batchScript=cf.findString("batchScript:",optional=False)

    if nodes==None and CPUs==None:
        sys.exit("Neither CPUs nor nodes specified in batch resource file")
        
    execList=["sbatch","-J",jobname,"-t",walltime]
    if nodes!=None:
        execList.append("-N")
        execList.append(str(int(nodes)))
    if CPUs!=None:
        execList.append("-n")
        execList.append(str(int(CPUs)))
    if mem !=None:
        execList.append("--mem")
        execList.append(str(int(mem)))
    execList.append(batchScript)
                        
    execList+=args

    if options.case!=None:
        execList.append("--case")
        execList.append(options.case)
    if options.debug:
        execList.append("--debug")
    if options.logfile:
        execList.append("--logfile")
        execList.append(options.logfile)
        
    runStr="running: "
    for x in execList:
        print x
        runStr+=" "+x
    print runStr
    subprocess.call(execList)

if __name__ == "__main__":
    main()

