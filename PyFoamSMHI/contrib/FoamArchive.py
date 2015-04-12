import os, sys, logging
from os import path, popen4

logger = logging.getLogger('foamArchive')

class FoamArchive:
    """Archive for storage of Foam-fields from batch runs"""

    def __init__(self, archivePath, name, compress=False):
        """Creates a new archive object
        @param archivePath: The directory to create the archive in
        @param name: the name of the archive directory to be created"""
        self.compress = compress
        if not path.exists(archivePath):
            logger.error("Path for foamArchive: " + name + "does not exist")
            sys.exit(1)
        self.path = path.join(archivePath, name)
        if not path.exists(self.path):
            os.mkdir(self.path)
        logger.debug("Path for archiving is: " + path.join(archivePath, name))

    def addFile(self, inFilePath, dirName=None, fileName=None):
        """copy the specified file to the archive given the specified name
        @param inFilePath: path to the file to be copied
        @param dirName: optional name of the directory within the archive to hold the file
        @param fileName: optional name of the file to be created in the archive"""
        logger.debug("1. Adding file: " + inFilePath)
        if not path.exists(inFilePath):
            logger.error("File to be archived does not exist")
            sys.exit(1)
        if dirName!=None:
            dirPath = path.join(self.path, dirName)
            if not path.exists(dirPath):
                self.execute("mkdir " + dirPath)
        else:
            dirPath = self.path
        resultPath = path.join(dirPath, path.basename(inFilePath))
        self.execute("cp " + inFilePath + " " + resultPath)
        if self.compress:
            tmp = self.execute("gzip -f " + resultPath)
        logger.debug("Added file: " + inFilePath)

    def getFile(self, outputFile, fileName, archiveDirName=None):
        """copy the specified file from the archive given the specified name
        @param outputFile: name of the field/file to be copied
        @param fileName: name of the file to copy
        @param archiveDirName: name of the directory within the archive containing the file to be copied
        """

        if archiveDirName is not None:
            filePath = path.join(self.path, archiveDirName, fileName)
        else:
            filePath = path.join(self.path, fileName)

        if path.exists(filePath):
            compressed = False
        elif path.exists(filePath + ".gz"):
            filePath = filePath+".gz"
            compressed = True
            if '.gz' not in outputFile:
                outputFile = outputFile + ".gz"
        else:
            logger.error("File: " + filePath + " to get from archive does not exist")
            sys.exit(1)

        if not path.exists(path.dirname(outputFile)):
            logger.error(
                "Destination directory: " + path.dirname(outputFile) +
                " when fetching an archived file does not exist"
            )
            sys.exit(1)
        self.execute("cp " + filePath + " " + outputFile)
        if compressed:
           tmp = self.execute("gunzip -f "+outputFile)

    def inArchive(self, dirName=None, filename=None):
        """Test if a file, directory or a file within a directory exist in the archive
        @param dirName: optional, name of the directory in the archive
        @param filename: optional, name of the file to look for """
        if dirName is None and filename is None:
            logger.warning("No file or directory given as parameter for inArchive function")
            return True
        testPath = self.path
        if dirName is not None and filename is None:
            testPath = path.join(testPath, dirName)
        if filename is not None:
            testPath = path.join(testPath, filename)
        if path.exists(testPath):
           return True
        else:
           return False

    def filesInArchive(self, dirName, fileNames):
        """Test if a file, directory or a file within a directory exist in the archive
        @param dirName:  name of the directory in the archive
        @param fileNames: list of names of the files to look for """
        for fileName in fileNames:
            if not self.inArchive(dirName, fileName):
                return False
        return True

    def listDirs(self):
        """Returns a list of all directories in archive"""
        dirs = [d for d in os.listdir(self.path) if path.isdir(path.join(self.path, d))]
        return dirs

    def listFiles(self):
        """Returns a list of all files in archive root directory"""
        return [f for f in os.listdir(self.path) if path.isfile(f)]

    def listFilesInDir(self, dirName):
        """Return a list of files located in a given directory in the archive
        @param dirName: Name of directory in archive"""
        files=[f for f in os.listdir(path.join(self.path,dirName)) if ".bak" not in f and "~" not in f and "#" not in f]
        return files

    def listFilesInDirs(self, prefix=None):
        """Returns a list of all files in directories within the archive
        @param prefix: optional, only list the files with prefix in the filename"""
        files = []
        for d in self.listDirs():
            dirPath = path.join(self.path, d)
            dirFiles = [path.join(dirPath, f) for f in os.listdir(dirPath) if path.isfile(path.join(dirPath, f))]
            dirFiles = [f for f in dirFiles if ".bak" not in f and "~" not in f and "#" not in f]
            if prefix is not None:
                dirFiles = [f for f in dirFiles if prefix in path.basename(f)]
            files += dirFiles
        return files

    def execute(self, cmd):
        """Execute the command cmd

        Currently no error-handling is done
        @return: A list with all the output-lines of the execution"""
        #        print cmd

        rein, raus = popen4(cmd)
        tmp = raus.readlines()

        return tmp

    def restore(self, dirName, fileNames, destinationDir):
        """Copies the given files from archive to a given directory
        @param dirName: name of directory in archive
        @param fileNames: list of names for files to be copied
        @param destinationDir: path to destination directory
        """
        if self.filesInArchive(dirName, fileNames):
            for fileName in fileNames:
                outFile = path.join(destinationDir,fileName)
                self.getFile(outFile, fileName, dirName)

