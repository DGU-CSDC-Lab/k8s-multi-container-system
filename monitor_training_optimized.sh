#!/bin/bash

# 0. 사용법 및 경로 설정
if [ $# -eq 0 ]; then
    echo "Usage: $0 <config_file> [experiment_name]"
    echo "Example: $0 configs/ntu60_xsub/bm.py bm_optimized"
    exit 1
fi

# 프로젝트 루트 경로 (절대 경로)
PROJECT_ROOT="/home/eunji/Desktop/project/k8s-multi-container-system/proto-gcn"
cd "$PROJECT_ROOT" || exit

# 입력된 경로에서 'proto-gcn/' 접두사가 있다면 제거하여 중복 방지
RAW_CONFIG=$1
CLEAN_CONFIG=$(echo "$RAW_CONFIG" | sed 's|^proto-gcn/||')
CONFIG_FILE="${PROJECT_ROOT}/${CLEAN_CONFIG}"

EXPERIMENT_NAME=${2:-$(basename "$CLEAN_CONFIG" .py)_optimized}
LOG_DIR="${PROJECT_ROOT}/monitoring_logs"
mkdir -p "$LOG_DIR"

# 파일 존재 여부 확인
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    echo "Please check the path."
    exit 1
fi

echo "Starting ZERO-COPY training experiment: $EXPERIMENT_NAME"
echo "Project Root: $PROJECT_ROOT"
echo "Config Path: $CONFIG_FILE"
echo "Start time: $(date)"
echo "================================"

# Step 1: 데이터 포맷 최적화 (PKL -> Feather)
echo "Step 1: Checking Data format (Feather)..."
PKL_FILE="data/nturgbd/ntu60_3danno.pkl"
FEATHER_FILE="data/nturgbd/ntu60_3danno.feather"

convert_start=$(date +%s)
# PKL이 Feather보다 최신이거나 Feather가 없으면 변환 실행
if [ ! -f "$FEATHER_FILE" ] || [ "$PKL_FILE" -nt "$FEATHER_FILE" ]; then
    echo "Converting $PKL_FILE to $FEATHER_FILE..."
    if [ ! -f "$PKL_FILE" ]; then
        echo "Error: $PKL_FILE not found!"
        exit 1
    fi
    
    # 메모리 여유 공간 확인
    AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    echo "Available memory: ${AVAILABLE_MEM}MB"
    
    # 이전에 작성한 '메모리 초절약형(Streaming)' convert_data.py 실행
    python tools/convert_data.py "$PKL_FILE" "$FEATHER_FILE"
    
    convert_end=$(date +%s)
    convert_time=$((convert_end - convert_start))
    echo "Data conversion completed in ${convert_time} seconds"
else
    echo "Feather file is up to date."
    convert_time=0
fi

# Step 2: 최적화된 Config 생성 (.py -> _arrow.py)
echo "Step 2: Creating optimized config..."

if [[ "$CONFIG_FILE" == *"_arrow.py" ]]; then
    OPTIMIZED_CONFIG="$CONFIG_FILE"
    echo "Using existing optimized config: $OPTIMIZED_CONFIG"
else
    OPTIMIZED_CONFIG="${CONFIG_FILE%.*}_arrow.py"
    # PoseDatasetArrow 사용 및 Feather 경로 지정을 위해 Config 수정
    python -c "
import sys
import os
sys.path.append('.')
from mmcv import Config

try:
    cfg = Config.fromfile('$CONFIG_FILE')
    # 모든 데이터셋 설정을 PoseDatasetArrow로 변경
    for s in ['train', 'val', 'test']:
        if s in cfg.data:
            cfg.data[s].type = 'PoseDatasetArrow'
            cfg.data[s].ann_file = '$FEATHER_FILE'
            # 기존에 있던 불필요한 필드 정리 (선택사항)
            if 'split' not in cfg.data[s]:
                if s == 'train': cfg.data[s].split = 'xsub_train'
                else: cfg.data[s].split = 'xsub_val'

    cfg.work_dir = cfg.work_dir + '_arrow'
    cfg.dump('$OPTIMIZED_CONFIG')
    print(f'Successfully created: $OPTIMIZED_CONFIG')
except Exception as e:
    print(f'Error modifying config: {e}')
    sys.exit(1)
"
fi

# --- 모니터링 시작 (백그라운드) ---
start_time=$(date +%s)

# 1. GPU 모니터링
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 1 > "${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv" &
GPU_PID=$!

# 2. 시스템 자원 모니터링
top -b -d 1 | grep -E "(python|Cpu|Mem)" > "${LOG_DIR}/system_${EXPERIMENT_NAME}.log" &
SYSTEM_PID=$!

# 3. 프로세스별 상세 모니터링
(
  while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S')" >> "${LOG_DIR}/process_${EXPERIMENT_NAME}.log"
    ps aux | grep python | grep -v grep >> "${LOG_DIR}/process_${EXPERIMENT_NAME}.log"
    echo "---" >> "${LOG_DIR}/process_${EXPERIMENT_NAME}.log"
    sleep 5
  done
) &
PROCESS_PID=$!

# --- Step 3: 학습 실행 ---
# 분산 학습 환경 변수 (단일 GPU 기준)
export MASTER_ADDR=localhost
export MASTER_PORT=$((12000 + RANDOM % 1000))
export WORLD_SIZE=1
export RANK=0
export LOCAL_RANK=0

echo "Step 3: Starting optimized training..."
training_start=$(date +%s)

# 학습 시작
time python tools/train.py "$OPTIMIZED_CONFIG" --validate --test-last --test-best 2>&1 | tee "${LOG_DIR}/training_${EXPERIMENT_NAME}.log"

training_end=$(date +%s)
training_time=$((training_end - training_start))

# --- 모니터링 종료 ---
kill $GPU_PID 2>/dev/null
kill $SYSTEM_PID 2>/dev/null  
kill $PROCESS_PID 2>/dev/null

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo "================================"
echo "OPTIMIZED training completed!"
echo "Total time: ${total_time} seconds ($(($total_time / 60)) minutes)"
echo "Logs: ${LOG_DIR}/training_${EXPERIMENT_NAME}.log"

# 간단한 결과 통계
if [ -f "${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv" ]; then
    echo ""
    echo "=== Quick GPU Stats ==="
    tail -n +2 "${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv" | awk -F',' '{sum+=$3; count++} END {if(count>0) print "Avg GPU Util: " sum/count "%"}'
    tail -n +2 "${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv" | awk -F',' '{if($5>max) max=$5} END {print "Peak GPU Mem: " max " MB"}'
fi