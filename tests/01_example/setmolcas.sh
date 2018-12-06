#!/bin/bash

export MOLCAS_NPROCS=1
export MOLCAS_PRINT=2
export MOLCAS_MEM=4000
export MOLCAS_MOLDEN=ON
export MOLCAS_OUTPUT=$CurrDir
# Set to /beegfs on ara
#export MOLCAS_WORKDIR=/scratch/molcas_jobs/scratch
export OMP_NUM_THREADS=1
export MOLCAS=/scratch/programme/openmolcas_serial
