# mcgridprep
Helper tool to easily run 2D grids for H2O using OpenMolcas.

## Installation
```
cd [where you wan't to install it]
git clone https://github.com/eljost/mcgridprep
cd mcgridparse
python setup.py develop
```

## Overview
mcgridprep provides four commands:
1. mcgridprep # Prepares all input files
2. mcgridrun [job_inputs] [--cpus N] # Runs OpenMolcas with the generated inputs
3. mcgridparse #  Parses all data from the log files and/or HDF5 files
4. mcgridplot # Plots the parsed data (PES, polarizabilities, ...)

## Configuration
mcgridprep reads the grid configuration from a `.yaml` file called `mcgrid.yaml`.
```
# Optional.  Will be used to name the files generated by mcgridprep
#name: wasser_grid
charge: 0
spin: 1
# Supported methods are: [hf, mp2, cas, caspt2, loprop]
# If loprop is set it will be called with the method before it
methods: [cas, caspt2]
basis: aug-cc-pvtz
# If using method cas this should be set to an INPORB file with the appropriate basis.
# Ideally this file was created by a &rasscf calculation at the starting point coord_eq.
inporb: /scratch/molcas_jobs/water_rigid/backup/07_rasscf_augtz/water_rigid.RasOrb
# Optional. Set this if you want to include excited states.
#ciroot: 2
# Path were the RasOrb/JobIph/moldens/h5 files are saved. Can be left at it's default value.
backup_path: backup
# Specification of 2D grid axes. They are given as [start, end, step].
coord1: [110, 90, 5]
coord2: [0.7, 1.1, 0.1]
# Axes labels for the plots. Can be left at their default values if coord1 is the angle
# and coord2 is the symmetric stretch.
coord1_lbl: "∠(H-O-H) / deg"
coord2_lbl: "r(O-H)_sym / Å"
# The starting point of the grid. Ideally this  point lies on the grid and corresponds
# to the equilibrium geometry. The inporb fil specified above should have been generated
# at this geometry.
coord_eq: [101, 1.0]
```
**To be able to run `mcgridrun` all appropriate variables for OpenMolcas have to be set!** This usually involves sourcing a little shell scrip with the appropriate environment variables before running `mcgridrun`. An example is provided below.
```
#!/bin/bash

# Load all appropriate libraries/modules here

export MOLCAS_NPROCS=1
export MOLCAS_PRINT=2
export MOLCAS_MEM=4000
export MOLCAS_MOLDEN=ON
export MOLCAS_OUTPUT=$CurrDir
export OMP_NUM_THREADS=1
# This should be adapted to your installation
export MOLCAS=/scratch/programme/openmolcas_serial
```
So before you run `mcgridrun` just source the above bash script with `source setmolcas.sh`. This assumes you saved the shellscript as `setmolcas.sh`.

## Running calculations
To setup a calculation you just have to decide on the two grid coordinates (`coord1`, `coord2`), select an appropriate starting point (`coord_eq`) and prepare an INPORB (`inporb`) file if you want to use the &rasscf module. A template for the `mcgrid.yaml` file can be found in the mcgridprep subfolder of the git repository ([mcgrid.yaml template](https://github.com/eljost/mcgridprep/blob/master/mcgridprep/mcgrid.yaml)).

### Basic steps
1. Create a folder and prepare `mcgrid.yaml` in it. This folder will be called `[root]`.
2. Run `mcgridprep` in `[root]`. This creates all OpenMolcas inputs and a file called `job_inputs` containing a list of all generated inputs.
3. Excecute `mcgridrun job_inputs --cpus 4` to run all jobs stored in `job_inputs` with four calculations in parallel. --cpus should be set to an appropriate number.
4. After or while the calculations are running you can call `mcgridparse` to extract the calculated informations. The command should be run from the `[root]` folder.
5. To plot the data run `mcgridplot` in `[root]`.

## Working example
A working example can be found in the `tests/01_example` subfolder. You just have to adapt the `inporb` path in `mcgrid.yaml` and the `MOLCAS` variable in setmolcas.sh.
To run everything:
```
cd tests/01_example
mcgridprep
source setmolcas.sh
mcgridrun job_inputs --cpus 4
mcgridparse
mcgridplot
```
