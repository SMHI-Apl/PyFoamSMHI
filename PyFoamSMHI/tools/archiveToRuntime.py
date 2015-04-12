#!/usr/bin/env python
#Python standard modules
from os import path
import os, glob, time,sys, logging, shutil
from optparse import OptionParser

#import pdb

usage = "usage: %prog -a <archiveDirectory> -d <destination> [options]"
version="%prog 1.0"

#sys.argv=[sys.argv[0],"-a","/home/openfoam/projekt/sthlmArenan/vindkomfort/case_1/flowArchive","-d","/home/openfoam/projekt/sthlmArenan/vindkomfort/case_1/2001"]


def main():
    parser=OptionParser(usage= usage, version=version)
    
    parser.add_option("-d", "--destination",
                      action="store",dest="dest",default=None,
                      help="Directory to write archived fields to")
    
    parser.add_option("-a", "--archive",
                      action="store",dest="archive",default=None,
                      help="Specifies archive directory")

    parser.add_option("--copy",
                      action="store_true",dest="copy",default=False,
                      help="Copy files instead of creating symbolic links")
    
    (options, args) = parser.parse_args()
    
    rootLogger=logging.getLogger('')
    logger=logging.getLogger('archive2Runtime')
    reportLevel=logging.INFO
    rootLogger.setLevel(reportLevel)

    console=logging.StreamHandler()
    console.setLevel(reportLevel)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)    
    rootLogger.addHandler(console)
                
    if len(args)!=0:
        parser.error("Incorrect number of arguments")

    if options.dest is None:
        parser.error("Needs to specify destination")

    if options.archive is None:
        parser.error("Needs to specify archive directory")
        
    archiveDir=path.abspath(options.archive)
    dest=path.abspath(options.dest)
    if not path.exists(archiveDir):
        print "Archive directory does not exist"
        sys.exit()

    if not path.exists(dest):
        print "Destination directory does not exist"
        sys.exit()

    #pdb.set_trace()
    for fieldDirName in os.listdir(archiveDir):
        for field in os.listdir(path.join(archiveDir,fieldDirName)):
            base,ext=path.splitext(field)
            src=path.join(archiveDir,fieldDirName,field)
            dst=path.join(dest,base+"_"+fieldDirName+ext)
            if not options.copy:
                os.symlink(src,dst)
            else:
                shutil.copy(src,dst)


    logger.info("Successfully transferred archived fields to destination directory")


if __name__ == "__main__":
    main()
