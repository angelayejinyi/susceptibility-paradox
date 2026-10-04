#!/bin/bash
#SBATCH --job-name=sus-exposure
#SBATCH --array=0-9
#SBATCH --cpus-per-task=1
#SBATCH --mem=72G
#SBATCH --time=06:00:00

set -euo pipefail

# Submit from the repository root after adapting DATASET, DATA_DIR, and the
# array range. Each task processes CHUNK_SIZE target users.
DATASET="${DATASET:-covid}"
DATA_DIR="${DATA_DIR:-data/processed}"
CHUNK_SIZE="${CHUNK_SIZE:-5000}"
START=$((SLURM_ARRAY_TASK_ID * CHUNK_SIZE))
STOP=$((START + CHUNK_SIZE))

python scripts/compute_exposures.py \
  --first-adoptions "${DATA_DIR}/target_users_first_adoptions_${DATASET}.csv" \
  --first-interactions "${DATA_DIR}/target_users_first_interaction_${DATASET}.csv" \
  --all-adoptions "${DATA_DIR}/over10_adoptions_${DATASET}.csv" \
  --target-users "${DATA_DIR}/target_users_${DATASET}.csv" \
  --start "${START}" \
  --stop "${STOP}" \
  --output "outputs/exposure_${DATASET}/part_${SLURM_ARRAY_TASK_ID}.csv"
