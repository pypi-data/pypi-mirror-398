#!/bin/bash
# LightRFT Multi-Modal Training Script for Geo3K Dataset
# Based on Qwen/Qwen2.5-VL-7B-Instruct model with GRPO algorithm
#
# This script uses PURE RULE-BASED REWARD (no reward model required)
# The reward is calculated based on:
# - Format: Does the output follow <think>...</think> and \boxed{} format? (10%)
# - Accuracy: Is the answer correct? (90%)

#############################  Training Hyperparameters  ##########################

# GRPO settings
GROUP_METHOD=normal
N_SAMPLES=8              # Number of samples per prompt (GRPO requires >1)
EPISODE=20               # Number of training episodes
WARMUP=0.03              # Learning rate warmup ratio
RBS=128
TBS=128

# Learning and KL settings
KL=0.01                  # KL coefficient (matching verl)
LR=1e-6                  # Actor learning rate
MAX_LENGTH=3072          # Max sequence length (1024 prompt + 2048 response)
PROMPT_MAX_LEN=1024      # Max prompt length
GENERATE_MAX_LEN=2048    # Max generation length

# Multi-modal settings
limit_mm_image_per_prompt=10  # Max images per prompt for multi-modal model

export IGNORE_EOS=0

#############################  Paths Configuration  #############################

# Dataset path (preprocessed geo3k data)
# DATA_PATH="$HOME/data/geo3k"
DATA_PATH="/mnt/shared-storage-user/puyuan/data/geo3k"

# Evaluation settings
EVAL_SPLIT="test"             # Use test split for evaluation
MAX_EVAL_SAMPLES=700          # Limit eval samples to avoid long eval time

# https://huggingface.co/datasets/hiyouga/geometry3k train-2.1k val-300 test-601

# Model paths
# PRETRAIN_PATH="Qwen/Qwen2.5-VL-7B-Instruct"  # Base model from HuggingFace
PRETRAIN_PATH="/mnt/shared-storage-user/puyuan/model/Qwen2.5-VL-7B-Instruct"

# IMPORTANT: No reward model needed for geo3k (pure rule-based reward)
# Set REWARD_PRETRAIN_PATHS to empty JSON to skip reward model loading
REWARD_PRETRAIN_PATHS='{}'

# vLLM/SGLang engine settings for inference
ENGINE_TP=2  # Tensor parallelism size for 7B model

#############################  Logging and Checkpoint  ##########################

current_time=$(date +"%m%d%H%M")
LOG_BASE=log
mkdir -p $LOG_BASE

NAME="geo3k-1224"

# Checkpoint and logging paths
SAVE_MODEL_NAME=lightrft-geo3k-qwen2.5-vl-7b-grpo-ep_${EPISODE}-sample_${N_SAMPLES}-kl_${KL}-lr_${LR}-${current_time}

mkdir -p results/$NAME/$SAVE_MODEL_NAME

# Create log directory
mkdir -p rft_logs/${NAME}


#############################  Environment Variables  ###########################

# Memory optimization
export TORCH_NCCL_AVOID_RECORD_STREAMS=1
export NCCL_DEBUG=WARN

# Distributed training settings (single node example)
export MLP_WORKER_NUM=1
export MLP_WORKER_GPU=8      # Number of GPUs per node
export MLP_ROLE_INDEX=0
export MLP_WORKER_0_PORT=20091
export MLP_WORKER_0_HOST=localhost  # TODO: Update this to your node's IP

# PyTorch distributed settings
export MASTER_ADDR=$MLP_WORKER_0_HOST
export NNODES=$MLP_WORKER_NUM
export NODE_RANK=$MLP_ROLE_INDEX
export GPUS_PER_NODE=$MLP_WORKER_GPU
export MASTER_PORT=$MLP_WORKER_0_PORT

#############################  Weights & Biases Logging  ########################

export WANDB_MODE="offline"  # Set to "online" if you want real-time logging

# W&B configuration (optional)
export WANDB_API_KEY="968275bc822c87ac741ecce2f06cdfb54dbc1608"  # Replace with your key
WANDB_PROJECT="LightRFT-Geo3K-GRPO"
WANDB_RUN_NAME="Qwen2.5-VL-7B-geo3k-grpo-${current_time}"

#############################  Instruction Template  ############################

# NOTE: System prompt is now included in the dataset itself (in the 'prompt' field)
# to avoid duplication. See examples/data_preprocess/geo3k.py for the format.
# Do NOT set --system_prompt in the training command to avoid instruction duplication.

#############################  Training Command  ################################

set -x


torchrun \
    --nnodes $NNODES \
    --nproc-per-node $GPUS_PER_NODE \
    --node_rank $NODE_RANK \
    --master-port $MASTER_PORT \
    --master-addr $MASTER_ADDR \
    examples/gsm8k_geo3k/train_colocate.py \
    --pretrain ${PRETRAIN_PATH} \
    --save_trajectories \
    --print_replay_buffer_stats \
    --loss_agg_mode seq-mean-token-mean \
    --fsdp \
    --rm_use_engine \
    --mixed_mm_data \
    --reward_pretrain "${REWARD_PRETRAIN_PATHS}" \
    --save_path results/$NAME/$SAVE_MODEL_NAME \
    --ckpt_path results/$NAME/$SAVE_MODEL_NAME \
    --micro_train_batch_size 4 \
    --train_batch_size ${TBS} \
    --micro_rollout_batch_size 8 \
    --rollout_batch_size ${RBS} \
    --advantage_estimator group_norm \
    --max_epochs 1 \
    --num_episodes ${EPISODE} \
    --lr_warmup_ratio ${WARMUP} \
    --n_samples_per_prompt $N_SAMPLES \
    --prompt_max_len $PROMPT_MAX_LEN \
    --generate_max_len $GENERATE_MAX_LEN \
    --zero_stage 3 \
    --bf16 \
    --actor_learning_rate $LR \
    --use_kl_loss \
    --init_kl_coef $KL \
    --kl_estimator k3 \
    --prompt_data $DATA_PATH \
    --input_key prompt \
    --images_key images \
    --label_key label \
    --eval_split $EVAL_SPLIT \
    --apply_chat_template \
    --flash_attn \
    --gradient_checkpointing \
    --save_steps 20 \
    --max_ckpt_num 2 \
    --engine_mem_util 0.6 \
    --engine_tp_size $ENGINE_TP \
    --enable_engine_sleep \
    --system_prompt 'A conversation between the User and Assistant. The User asks a question, and the Assistant provides a solution. The Assistant first thinks through the reasoning process internally with self-reflection and consistency check and then gives the final analysis and answer. The reasoning process should be enclosed within <think></think>, followed directly by the final thought and answer, the final answer MUST BE put in \\boxed{}, like this: <think> reasoning process here </think> final thought and \\boxed{answer} here.' \
    --l2 1.0e-2 \
    --freeze_prefix \
    --adam_offload \
    --limit_mm_image_per_prompt $limit_mm_image_per_prompt \
    --use_wandb "${WANDB_API_KEY}" \
    --wandb_project "${WANDB_PROJECT}" \
    --wandb_run_name "${WANDB_RUN_NAME}" \
    2>&1 | tee "rft_logs/${NAME}/geo3k_qwen2.5_vl_7b_node${NODE_RANK}_$(date +%Y%m%d_%H%M%S).log"


#############################  Usage Instructions  ##############################
#
# Step 1: Preprocess the geo3k dataset
#   python ./examples/data_preprocess/geo3k.py --local_save_dir ./data/geo3k
#
# Step 2: Download the base model (optional, will auto-download if not present)
#   python3 -c "import transformers; transformers.pipeline(model='Qwen/Qwen2.5-VL-7B-Instruct')"
#
# Step 3: Run this training script
#   cd LightRFT
#   bash examples/openrlhf_v/run_grpo_geo3k_qwen2.5_vl_7b.sh
#
# Note: This script uses PURE RULE-BASED REWARD, no reward model is required.
# The reward is calculated based on format correctness and answer accuracy.
#
################################################################################
