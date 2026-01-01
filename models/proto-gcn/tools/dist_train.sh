#!/usr/bin/env bash

export MASTER_PORT=$((12000 + $RANDOM % 20000))
set -x

CONFIG=$1
GPUS=$2

# CPU 모드인지 확인 (CUDA_VISIBLE_DEVICES가 빈 문자열이면 CPU 모드)
if [ -z "$CUDA_VISIBLE_DEVICES" ]; then
    echo "Running in CPU mode"
    MKL_SERVICE_FORCE_INTEL=1 PYTHONPATH="$(dirname $0)/..":$PYTHONPATH \
    python $(dirname "$0")/train.py $CONFIG ${@:3}
else
    echo "Running in GPU mode"
    MKL_SERVICE_FORCE_INTEL=1 PYTHONPATH="$(dirname $0)/..":$PYTHONPATH \
    CUDA_VISIBLE_DEVICES=0 python -m torch.distributed.launch --nproc_per_node=$GPUS --master_port=$MASTER_PORT \
        $(dirname "$0")/train.py $CONFIG --launcher pytorch ${@:3}
fi
