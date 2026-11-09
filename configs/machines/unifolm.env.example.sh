#!/usr/bin/env bash
# Source to use the default directory layout. Export variables first to override it.
# Directory defaults are independent of the optional machine JSON file.
export CVPR_DATA_ROOT="${CVPR_DATA_ROOT:-${HOME}/sigma0/data}"
export CVPR_MODEL_ROOT="${CVPR_MODEL_ROOT:-${HOME}/sigma0/models}"
export CVPR_RUN_ROOT="${CVPR_RUN_ROOT:-${HOME}/sigma0/runs}"

# Prepare the VLM weights and train MotionExpert before running joint training.
export EGO_DEX_VLM_PATH="${EGO_DEX_VLM_PATH:-${CVPR_MODEL_ROOT}/egodex-vlm}"
export MOTION_EXPERT_CHECKPOINT="${MOTION_EXPERT_CHECKPOINT:-${CVPR_RUN_ROOT}/motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch/final.ckpt}"
export MOTION_USE_EMA="${MOTION_USE_EMA:-1}"
export UNIFOLM_DINO_ROOT="${UNIFOLM_DINO_ROOT:-${CVPR_DATA_ROOT}/UnifoLM}"
export UNIFOLM_DINO_TRAIN_ID="${UNIFOLM_DINO_TRAIN_ID:-unifolm_sonic_lerobot_train}"
export UNIFOLM_DINO_VAL_ID="${UNIFOLM_DINO_VAL_ID:-unifolm_sonic_lerobot_val}"
export UNIFOLM_DINO_CACHE="${UNIFOLM_DINO_CACHE:-${UNIFOLM_DINO_ROOT}/dino/256x320}"
export UNIFOLM_RUN_ROOT="${UNIFOLM_RUN_ROOT:-${CVPR_RUN_ROOT}/unifolm}"
# Use the active, prepared Python 3.11 environment unless explicitly overridden.
export PSI_PYTHON="${PSI_PYTHON:-python3}"

# If using an initialization receipt, set UNIFOLM_INIT_WEIGHTS_RECORD to this
# machine's verified record. Do not copy a different machine's hashes or mtimes.
# Inspect before any launch (from repository root):
# bash VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh --dry-run
