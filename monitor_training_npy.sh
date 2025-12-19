#!/bin/bash

# 1. 경로 및 실험 설정
if [ $# -eq 0 ]; then
    echo "❌ 사용법: $0 <설정파일_경로> [실험_이름]"
    echo "💡 예시: $0 configs/ntu60_xsub/bm_npy.py npy_methodology_final"
    exit 1
fi

CONFIG_FILE=$1
EXPERIMENT_NAME=${2:-$(basename $CONFIG_FILE .py)}
PROJECT_ROOT="/home/eunji/Desktop/project/k8s-multi-container-system/proto-gcn"
LOG_DIR="${PROJECT_ROOT}/monitoring_logs"
mkdir -p $LOG_DIR

echo "===================================================="
echo "🚀 방법론 검증 통합 파이프라인 시작"
echo "📅 시작 시간: $(date)"
echo "⚙️  설정 파일: $CONFIG_FILE"
echo "🧪 실험 이름: $EXPERIMENT_NAME"
echo "===================================================="

# --- [단계 1: 데이터 변환 (PKL -> NPY)] ---
DATA_DIR="${PROJECT_ROOT}/data/nturgbd"
TRAIN_NPY="${DATA_DIR}/ntu60_train_data.npy"

echo "🔄 [STEP 1] 데이터 상태를 확인하는 중..."
if [ ! -f "$TRAIN_NPY" ]; then
    echo "⚠️  .npy 데이터가 없습니다. 변환 스크립트를 실행합니다."
    cd ${PROJECT_ROOT}
    # 아까 수정한 tools/convert_pkl_to_npy.py를 호출합니다.
    python tools/convert_pkl_to_npy.py
    if [ $? -ne 0 ]; then
        echo "❌ 데이터 변환에 실패했습니다. pkl 파일 위치를 확인하세요."
        exit 1
    fi
    echo "✅ 데이터 변환 완료!"
else
    echo "✔ .npy 데이터가 이미 존재합니다. 변환 단계를 건너뜁니다."
fi

# --- [단계 2: 모니터링 세션 준비] ---
cd ${PROJECT_ROOT}
echo "📊 [STEP 2] 자원 모니터링을 시작합니다..."

# 1) GPU 모니터링 (1초 간격)
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 1 > ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv &
GPU_PID=$!

# 2) 전체 시스템 메모리 모니터링 (5초 간격)
while true; do
    echo "--- Time: $(date '+%Y-%m-%d %H:%M:%S') ---" >> ${LOG_DIR}/system_mem_${EXPERIMENT_NAME}.log
    free -m >> ${LOG_DIR}/system_mem_${EXPERIMENT_NAME}.log
    sleep 5
done &
SYS_MEM_PID=$!

# 3) 프로세스 상세 메모리(RSS vs VSZ) 모니터링 (5초 간격)
while true; do
    echo "--- Time: $(date '+%Y-%m-%d %H:%M:%S') ---" >> ${LOG_DIR}/process_${EXPERIMENT_NAME}.log
    ps -eo pid,ppid,%cpu,%mem,rss,vsz,cmd --sort=-%cpu | grep python | grep -v grep | head -n 5 >> ${LOG_DIR}/process_${EXPERIMENT_NAME}.log
    echo "" >> ${LOG_DIR}/process_${EXPERIMENT_NAME}.log
    sleep 5
done &
PROCESS_PID=$!

# --- [단계 3: 학습 실행] ---
echo "🏋️  [STEP 3] 학습 프로세스를 시작합니다..."
start_time=$(date +%s)

# 분산 학습 환경 변수 (단일 GPU여도 기본 설정 필요)
export MASTER_ADDR=localhost
export MASTER_PORT=$(shuf -i 10000-65535 -n 1) # 포트 충돌 방지
export WORLD_SIZE=1
export RANK=0
export LOCAL_RANK=0

# 실제 학습 명령 실행 (결과를 화면과 로그 파일에 동시에 기록)
time python tools/train.py $CONFIG_FILE --validate --test-last --test-best 2>&1 | tee ${LOG_DIR}/training_${EXPERIMENT_NAME}.log

# --- [단계 4: 마무리 및 요약] ---
# 백그라운드 모니터링 종료
kill $GPU_PID $SYS_MEM_PID $PROCESS_PID 2>/dev/null

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo "===================================================="
echo "✅ 모든 실험 프로세스가 종료되었습니다!"
echo "⏱️  총 학습 소요 시간: ${total_time} 초 ($(($total_time / 60)) 분)"
echo "📂 로그 저장 위치: ${LOG_DIR}"
echo "===================================================="

# 결과 요약 출력
echo ""
echo "📊 [연구 데이터 요약]"
if [ -f ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv ]; then
    avg_gpu=$(tail -n +2 ${LOG_DIR}/gpu_${EXPERIMENT_NAME}.csv | awk -F',' '{sum+=$3; count++} END {if(count>0) print sum/count}')
    echo "✔ 평균 GPU 활용률: ${avg_gpu}%"
fi

# VSZ 수치 출력 (npy memmap이 정상 작동하면 이 수치가 매우 높아야 함)
echo "✔ 메모리 매핑 지표 (마지막 기록):"
tail -n 20 ${LOG_DIR}/process_${EXPERIMENT_NAME}.log | grep python | tail -n 1 | awk '{print "   - RSS (실제 RAM 사용): " $5/1024 " MB"}'
tail -n 20 ${LOG_DIR}/process_${EXPERIMENT_NAME}.log | grep python | tail -n 1 | awk '{print "   - VSZ (가상 메모리 매핑): " $6/1024 " MB"}'
echo "----------------------------------------------------"
echo "💡 VSZ가 데이터셋 크기만큼(예: 10GB 이상) 높게 나오면 방법론이 성공한 것입니다!"
