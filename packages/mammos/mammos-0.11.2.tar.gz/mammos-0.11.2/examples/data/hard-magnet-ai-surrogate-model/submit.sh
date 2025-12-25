#!/bin/bash -l
#
# Standard output and error
#SBATCH -o ./job.out.%j
#SBATCH -e ./job.err.%j
#
# working directory
#SBATCH -D ./
#
# job name
#SBATCH -J CoFeH-300
#
# job requirements
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=128G
#SBATCH --partition=gpu
#
#SBATCH --mail-type=ALL
# #SBATCH --mail-user=
#SBATCH --time=2:00:00

module purge
mpsd-modules 25c $MPSD_MICROARCH
module load gcc/13.2.0 cuda/12.6.2

unset LD_LIBRARY_PATH

eval "$(/home/fangohr/.pixi/bin/pixi shell-hook)"
time python -u run.py

