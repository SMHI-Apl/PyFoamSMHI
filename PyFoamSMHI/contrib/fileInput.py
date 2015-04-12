#File readers module, David Segersson, 051219
#Reads columns from files and stores data in a list indexed as [][]
#Uses seperator given by second argument sep with default tabseparated

from string import split, rstrip
import sys

def file2list(filename, sep='\t'):

    try:
        in_fid=open(filename)
        lineList=in_fid.readlines()
        in_fid.close()
        
        for row in range(len(lineList)):
            lineList[row]=split(lineList[row],sep)                
            lineList[row][-1]=lineList[row][-1].rstrip('\n')
            lineList[row][-1]=lineList[row][-1].rstrip()
            
        return lineList
    
    except:
        print 'Error in fileInput: Could not open file: '+filename
        sys.exit('Error in fileInput: Could not open file: '+filename)


def list2file(List,filename, sep='\t',header=""):

    try:
        out_fid=open(filename,'w')
        if header != "":
            out_fid.write(header+'\n')
        for celli in List:
            if str(type(celli))== "<type 'list'>":
                for cellj in celli:
                    out_fid.write(str(cellj)+sep)
                out_fid.write('\n')
            else:
                out_fid.write(str(celli)+'\n')

        out_fid.close()
    
    except:
        print "Error when trying to write to file:"+filename
        sys.exit("Error when trying to write to file:"+filename)
