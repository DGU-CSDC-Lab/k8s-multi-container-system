#!/bin/bash

# OpenAI API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY 환경변수가 설정되지 않았습니다."
    echo "AI 분석 대신 기본 분석을 사용합니다."
fi

# Image Analysis Service 빌드 및 실행
echo "=== Building Image Analysis Service ==="
cd image-analysis-service
docker build -t image-analysis-service:latest .
docker run -d -p 5000:5000 --name image-analysis-service \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  image-analysis-service:latest

echo "=== Building Performance Prediction Service ==="
cd ../performance-prediction-service
docker build -t performance-prediction-service:latest .
docker run -d -p 5001:5001 --name performance-prediction-service \
  performance-prediction-service:latest

echo "=== Services Started ==="
echo "Image Analysis Service: http://localhost:5000"
echo "Performance Prediction Service: http://localhost:5001"

echo "=== Health Check ==="
sleep 5
curl http://localhost:5000/health
curl http://localhost:5001/health
