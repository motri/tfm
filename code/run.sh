#!/bin/bash
#SBATCH -J daiedge
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=130:00:00
#SBATCH --partition=vicomtech
#SBATCH --mem=16GB
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mail-type=ALL
#SBATCH --qos=qos_di13
#SBATCH --mail-user=gpaolini@vicomtech.org
# SBATCH --nodelist=abacus-[005-006]

# module load Miniconda3/4.9.2
# conda create env from requirements.yml
# conda env create -f requirements.yml -n daiedge_conda
cd ./sea-ice
# source activate igarss_t2
source .venv/bin/activate
# srun python training_unet.py
srun python training_lightning.py --config_file ./configs/training_balanced.yaml
# srun python /gpfs/VICOMTECH/proiektuak/DI13/DIVINE/other_data_sentinel1_gpaolini/CODE/sea-ice/training_unet2.py
# srun python /gpfs/VICOMTECH/proiektuak/DI13/DIVINE/other_data_sentinel1_gpaoli