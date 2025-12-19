#!/bin/bash

# 사용법: ./submit_job.sh <user> <data_url> [config_file]

USER=${1:-"user-$(date +%s)"}
DATA_URL=${2:-""}
CONFIG_FILE=${3:-"configs/ntu60_xsub/bm.py"}

echo "=== Proto-GCN 작업 제출 ==="
echo "사용자: $USER"
echo "데이터 URL: $DATA_URL"
echo "설정 파일: $CONFIG_FILE"

# 큐 매니저에 작업 제출
curl -X POST http://localhost:30081/submit \
  -H "Content-Type: application/json" \
  -d "{
    \"user\": \"$USER\",
    \"data_url\": \"$DATA_URL\",
    \"config_file\": \"$CONFIG_FILE\"
  }"

echo -e "\n작업이 큐에 추가되었습니다."
echo "상태 확인: curl http://localhost:30081/status"
