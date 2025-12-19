#!/bin/bash

# 0. 사용법 및 경로 설정
if [ $# -eq 0 ]; then
    echo "Usage: $0 <config_file> [experiment_name]"
    echo "Example: $0 configs/ntu60_xsub/bm.py bm_parquet_test"
    exit 1
fi

# 프로젝트 루트 경로 (절대 경로)
PROJECT_ROOT="/home/eunji/Desktop/project/k8s-multi-container-system/proto-gcn"
cd "$PROJECT_ROOT" || exit

RAW_CONFIG=$1
CLEAN_CONFIG=$(echo "$RAW_CONFIG" | sed 's|^proto-gcn/||')
CONFIG_FILE="${PROJECT_ROOT}/${CLEAN_CONFIG}"

# 실험 이름 설정 (Parquet 강조)
EXPERIMENT_NAME=${2:-$(basename "$CLEAN_CONFIG" .py)_parquet}
LOG_DIR="${PROJECT_ROOT}/monitoring_logs"
mkdir -p "$LOG_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

echo "Starting PARQUET-BASED training experiment: $EXPERIMENT_NAME"
echo "Project Root: $PROJECT_ROOT"
echo "Config Path: $CONFIG_FILE"
echo "================================"

# Step 1: 데이터 포맷 최적화 (PKL -> Parquet)
echo "Step 1: Checking Data format (Parquet)..."
PKL_FILE="data/nturgbd/ntu60_3danno.pkl"
PARQUET_FILE="data/nturgbd/ntu60_3danno.parquet"

convert_start=$(date +%s)
# PKL이 Parquet보다 최신이거나 파일이 없으면 변환 실행
if [ ! -f "$PARQUET_FILE" ] || [ "$PKL_FILE" -nt "$PARQUET_FILE" ]; then
    echo "Converting $PKL_FILE to $PARQUET_FILE (Snappy Compression)..."
    if [ ! -f "$PKL_FILE" ]; then
        echo "Error: $PKL_FILE not found!"
        exit 1
    fi
    
    # Parquet 변환 스크립트 실행 (아래 제공되는 Python 코드 사용)
    python tools/convert_data_parquet.py "$PKL_FILE" "$PARQUET_FILE"
    
    convert_end=$(date +%s)
    echo "Data conversion completed in $((convert_end - convert_start)) seconds"
else
    echo "Parquet file is up to date."
fi

# Step 2: 최적화된 Config 생성 (.py -> _parquet.py)
echo "Step 2: Creating Parquet-optimized config..."

OPTIMIZED_CONFIG="${CONFIG_FILE%.*}_parquet.py"
python -c "
import sys
import os
sys.path.append('.')
from mmcv import Config

try:
    cfg = Config.fromfile('$CONFIG_FILE')
    for s in ['train', 'val', 'test']:
        if s in cfg.data:
            # 데이터셋 타입을 Parquet 전용으로 변경
            cfg.data[s].type = 'PoseDatasetParquet'
            cfg.data[s].ann_file = '$PARQUET_FILE'
            if 'split' not in cfg.data[s]:
                cfg.data[s].split = 'xsub_train' if s == 'train' else 'xsub_val'

    cfg.work_dir = cfg.work_dir + '_parquet'
    cfg.dump('$OPTIMIZED_CONFIG')
    print(f'Successfully created: $OPTIMIZED_CONFIG')
except Exception as e:
    print(f'Error modifying config: {e}')
    sys.exit(1)
"

# --- 모니터링 시작 (백그라운드) ---
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 1 > "${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv" &
GPU_PID=$!

# monitor_training_parquet.sh의 하단 Step 3 부분을 이렇게 수정하세요.

# --- Step 3: 학습 실행 (에러 수정 버전) ---
echo "Step 3: Starting Parquet-optimized training..."
training_start=$(date +%s)

# 환경 변수 강제 주입 (단일 GPU 학습 시 필수)
export RANK=0
export WORLD_SIZE=1
export MASTER_ADDR=localhost
export MASTER_PORT=$((12000 + RANDOM % 1000))

# --launcher none을 추가하여 분산 학습 에러 방지
time python tools/train.py "$OPTIMIZED_CONFIG" --validate --test-last --test-best 2>&1 | tee "${LOG_DIR}/training_${EXPERIMENT_NAME}.log"
training_end=$(date +%s)
kill $GPU_PID 2>/dev/null

echo "================================"
echo "PARQUET training completed!"
echo "Total training time: $((training_end - training_start)) seconds"
echo "Logs: ${LOG_DIR}/training_${EXPERIMENT_NAME}.log"
