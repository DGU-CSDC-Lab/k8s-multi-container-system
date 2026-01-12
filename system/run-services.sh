#!/bin/bash

# 환경변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# OpenAI API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY 환경변수가 설정되지 않았습니다."
    echo "AI 분석 대신 기본 분석을 사용합니다."
    echo "사용법: .env 파일에 OPENAI_API_KEY=your-key-here 설정"
fi

# 기존 컨테이너 정리
echo "=== Cleaning up existing containers ==="
docker rm -f image-analysis-service performance-prediction-service 2>/dev/null || true

# Image Analysis Service 빌드 및 실행
echo "=== Building Image Analysis Service ==="
cd image-analysis-service
docker build -t image-analysis-service:latest .
docker run -d -p ${IMAGE_ANALYSIS_PORT:-5000}:5000 --name image-analysis-service \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e AI_MODEL="$AI_MODEL" \
  -e AI_TEMPERATURE="$AI_TEMPERATURE" \
  -e AI_MAX_TOKENS="$AI_MAX_TOKENS" \
  -e AI_TIMEOUT="$AI_TIMEOUT" \
  -e MAX_FILES_TO_ANALYZE="$MAX_FILES_TO_ANALYZE" \
  -e MAX_FILE_SIZE_KB="$MAX_FILE_SIZE_KB" \
  -e MAX_TOTAL_FILES_SCAN="$MAX_TOTAL_FILES_SCAN" \
  -e LOG_LEVEL="$LOG_LEVEL" \
  -e DEBUG="$DEBUG" \
  image-analysis-service:latest

echo "=== Building Performance Prediction Service ==="
cd ../performance-prediction-service
docker build -t performance-prediction-service:latest .
docker run -d -p ${PERFORMANCE_PREDICTION_PORT:-5001}:5001 --name performance-prediction-service \
  -e LOG_LEVEL="$LOG_LEVEL" \
  -e DEBUG="$DEBUG" \
  performance-prediction-service:latest

echo "=== Services Started ==="
echo "Image Analysis Service: http://localhost:${IMAGE_ANALYSIS_PORT:-5000}"
echo "Performance Prediction Service: http://localhost:${PERFORMANCE_PREDICTION_PORT:-5001}"

echo "=== Health Check ==="
sleep 5
curl -f http://localhost:${IMAGE_ANALYSIS_PORT:-5000}/health || echo "Image Analysis Service not ready"
curl -f http://localhost:${PERFORMANCE_PREDICTION_PORT:-5001}/health || echo "Performance Prediction Service not ready"

echo "=== Setup Complete ==="
