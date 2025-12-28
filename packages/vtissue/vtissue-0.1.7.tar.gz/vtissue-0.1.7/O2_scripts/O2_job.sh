#!/bin/bash
#SBATCH -J vtissue_preprocess
#SBATCH -p gpu
#SBATCH --gres=gpu:1,vram:48G
#SBATCH -c 4
#SBATCH --mem=32G
#SBATCH -t 32:00:00
#SBATCH -o logs/vtissue_preprocess.%j.out
#SBATCH -e logs/vtissue_preprocess.%j.err
#SBATCH --mail-type=END
#SBATCH --mail-user=anirmal@bwh.harvard.edu

set -euo pipefail
mkdir -p logs

module load gcc/14.2.0
module load cuda/12.8
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vtissue


# ---- Paths (edit these) ----
INPUT_H5AD="/n/scratch/users/a/ajn16/vtissue/data/data.h5ad"
INPUT_LAYER="log"

TRAIN_CONFIG="/n/scratch/users/a/ajn16/vtissue/config/train_config.yaml"
INFER_CONFIG="/n/scratch/users/a/ajn16/vtissue/config/infer_config.yaml"

# If preprocess writes a different filename, set it here (or keep as-is if you know it)
PREPROCESSED_H5AD="/n/scratch/users/a/ajn16/vtissue/data/data_preprocessed.h5ad"

OUTDIR="/n/scratch/users/a/ajn16/vtissue/results/"

UMAP_RUN="/n/scratch/users/a/ajn16/vtissue/plot_scripts/umap-spatial.py"
UMAP_TOOL="/n/scratch/users/a/ajn16/vtissue/plot_scripts/umap_tool.py"
UMAP_PLOT="/n/scratch/users/a/ajn16/vtissue/plot_scripts/umap_plot.py"
SPATIAL_PLOT="/n/scratch/users/a/ajn16/vtissue/plot_scripts/spatial_scatterPlot_withplotly_sparse.py"

SPATIAL_GENES="SOX10,ITGAX,CD3D,KRT18"
SPATIAL_LAYER="vt_expr_pred"

# ---- Step 1: preprocess ----
python -m vtissue.preprocessing.preprocess --input "${INPUT_H5AD}" --input-layer "${INPUT_LAYER}" #--norm-method zscore

# ---- Step 2: training ----
python -m vtissue.run_training --config "${TRAIN_CONFIG}"

# ---- Step 3: inference ----
python -m vtissue.inference.run_inference --config "${INFER_CONFIG}"

# ---- Step 4: UMAP + spatial plots ----
python "${UMAP_RUN}" --h5ad "${PREPROCESSED_H5AD}" --outdir "${OUTDIR}" --umap-tool "${UMAP_TOOL}" --umap-plot "${UMAP_PLOT}" --spatial-plot "${SPATIAL_PLOT}" --spatial-genes "${SPATIAL_GENES}" --spatial-layer "${SPATIAL_LAYER}"

echo "DONE"


