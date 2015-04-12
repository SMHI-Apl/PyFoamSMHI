defaultQf="""
#===============Template for SbatchFile================== 
#!/bin/bash
#SBATCH -N nodes
#SBATCH -t walltime
#SBATCH -J jobname

cd arenastaden/mesh5_open_short

#setLanduse
#setWindInlet
#foamToVTK -time 0
#foamToVTK -faceSet wall.roof_set_2
#decomposePar
#mpprun `which potentialFoam` -parallel
mpprun `which windFoam` -parallel >& windFoam.log #Runs windFoam in parallel
reconstructPar
foamToVTK -latestTime

#rm -rf processor*

# End of script

"""
