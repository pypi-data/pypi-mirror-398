#!/bin/bash
#SBATCH -n 30
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=4G
export PYTHONBREAKPOINT=0

mpirun python3 test.py
