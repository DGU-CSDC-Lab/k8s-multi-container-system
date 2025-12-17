#!/bin/bash
echo "Starting training at $(date)"
start_time=$(date +%s)

# GPU 모니터링 시작
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used --format=csv -l 1 > gpu_${1}.log &
GPU_PID=$!

# 학습 실행
time python tools/train.py $1 --validate --test-last --test-best

# 정리
kill $GPU_PID
end_time=$(date +%s)
echo "Total time: $((end_time - start_time)) seconds"