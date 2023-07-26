#!/bin/bash -l
#SBATCH --job-name=regresson_tangent
 
#SBATCH --nodes=1
#SBATCH --exclusive
#SBATCH --time=0-120:00:00
#SBATCH --partition compute
#SBATCH --output=/home/sheczko/logs/%j.out

 
module add singularity

export SINGULARITY_BIND="/run,/ptmp,/scratch,/tmp,/opt/ohpc,${HOME}"

singularity exec /ptmp/containers/datascience-python_latest.sif  python /home/sheczko/code1/MastersThesis/gabys_tangnet_no_feat_select_tangent_200_folds


exit 0
