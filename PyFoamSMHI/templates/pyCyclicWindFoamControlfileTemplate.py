defaultCf="""
#===============Template for controlfile================== 
#--------------Landuse--------------
z0List: 0.01 0.05 0.1 0.15 0.2 0.3 0.4
LAIList: 1.5
CdList: 1.0
heightList: 6
#---------------Numerics-----------------
iterations: 20
solver: cyclicWindFoam
#---------------Archives-----------------
#----flow calculations----
flowArchiveDirName: flowArchive
fieldsToArchive: U epsilon k

#---general archive settings----
archiveVTK: False
archiveSamples: True
VTKArchiveDir: /data/proj/Ml-data/miljosakerhet_ml/CFD/projekt/...
sampleArchiveDir: /data/proj/Ml-data/miljosakerhet_ml/CFD/projekt/2008/GBG_Hamn/landuse/tester/samples

#=========================================================
"""
