#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <config_file> [experiment_name]"
    echo "Example: $0 configs/ntu60_xsub/j.py j_experiment"
    exit 1
fi

CONFIG_FILE=$1
EXPERIMENT_NAME=${2:-$(basename $CONFIG_FILE .py)}
LOG_DIR="/home/eunji/Desktop/project/k8s-multi-container-system/proto-gcn/monitoring_logs"
mkdir -p $LOG_DIR

echo "Starting training experiment: $EXPERIMENT_NAME"
echo "Config: $CONFIG_FILE"
echo "Start time: $(date)"
echo "================================"

start_time=$(date +%s)

# GPU 사용량 모니터링
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw --format=csv -l 1 > ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv &
GPU_PID=$!

# 시스템 전체 자원 사용량 모니터링 (CPU, 메모리)
top -b -d 1 | grep -E "(python|Cpu|Mem)" > ${LOG_DIR}/system_${EXPERIMENT_NAME}.log &
SYSTEM_PID=$!

# 프로세스별 자원 사용량 모니터링
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S')" >> ${LOG_DIR}/process_${EXPERIMENT_NAME}.log
    # Python 프로세스들의 CPU, 메모리 사용량
    ps aux | grep python | grep -v grep >> ${LOG_DIR}/process_${EXPERIMENT_NAME}.log
    echo "---" >> ${LOG_DIR}/process_${EXPERIMENT_NAME}.log
    sleep 5
done &
PROCESS_PID=$!

# 학습 실행 및 시간 측정
echo "Starting training..."
cd /home/eunji/Desktop/project/k8s-multi-container-system/proto-gcn
mkdir -p ${LOG_DIR}

# 분산 학습 환경 변수 설정
export MASTER_ADDR=localhost
export MASTER_PORT=12357
export WORLD_SIZE=1
export RANK=0
export LOCAL_RANK=0

time python tools/train.py $CONFIG_FILE --validate --test-last --test-best 2>&1 | tee ${LOG_DIR}/training_${EXPERIMENT_NAME}.log

# 모니터링 프로세스들 종료
kill $GPU_PID 2>/dev/null
kill $SYSTEM_PID 2>/dev/null  
kill $PROCESS_PID 2>/dev/null

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo "================================"
echo "Training completed!"
echo "End time: $(date)"
echo "Total training time: ${total_time} seconds ($(($total_time / 60)) minutes)"
echo ""
echo "Log files saved in ${LOG_DIR}/"
echo "- GPU usage: ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv"
echo "- System usage: ${LOG_DIR}/system_${EXPERIMENT_NAME}.log"  
echo "- Process usage: ${LOG_DIR}/process_${EXPERIMENT_NAME}.log"
echo "- Training log: ${LOG_DIR}/training_${EXPERIMENT_NAME}.log"

# 간단한 통계 출력
echo ""
echo "=== Quick Stats ==="
if [ -f ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv ]; then
    echo "Average GPU utilization:"
    tail -n +2 ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv | awk -F',' '{sum+=$3; count++} END {if(count>0) print sum/count "%"}'
    
    echo "Peak GPU memory usage:"
    tail -n +2 ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv | awk -F',' '{if($5>max) max=$5} END {print max " MB"}'
fi

echo "Training time: ${total_time} seconds"
