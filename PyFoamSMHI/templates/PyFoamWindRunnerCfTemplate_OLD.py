defaultCf="""
#===============Template for controlfile================== 
#--------------Meteorology---------------
z0: 0.1
wspeeds: 3.0
wdirs: 0 45 90 135 180 225 275 315

#---------------Numerics-----------------
iterations: 20
solver: windFoam
initialize: setWindInlet

#---------------Archives-----------------
#----flow calculations----
flowArchiveDirName: flowArchive
fieldsToArchive: U p epsilon k

#----disperison calculations----
concArchiveDirName: concArchive

#---general archive settings----
archiveVTK: True
VTKArchiveDir: /data/proj/Ml-data/miljosakerhet_ml/CFD/projekt/...


#--------------Computation----------------
#List of server names
servers: lxserv58
#Number of CPUs for each server given as a list with posts matching the server list
CPUs: 2

#----------------Output-------------------
outputFormat: ascii
comression: False

#=========================================================
"""
