#!/bin/bash

echo "=== Proto-GCN 멀티유저 시스템 설정 ==="

# 1. Docker 이미지 빌드
echo "1. Docker 이미지 빌드 중..."
cd resource-monitor && docker build -t resource-monitor:latest . && cd ..
cd queue-manager && docker build -t queue-manager:latest . && cd ..

# 2. Kubernetes 리소스 배포
echo "2. Kubernetes 리소스 배포 중..."
kubectl apply -f deploy-system.yaml

# 3. 서비스 포트 포워딩 설정
echo "3. 포트 포워딩 설정 중..."
kubectl port-forward -n argo svc/queue-manager 30081:8081 &

# 4. 실행 권한 부여
chmod +x submit_job.sh

echo "=== 설정 완료 ==="
echo ""
echo "사용법:"
echo "  작업 제출: ./submit_job.sh <사용자명> <데이터URL> [설정파일]"
echo "  상태 확인: curl http://localhost:30081/status"
echo "  Argo UI: kubectl port-forward -n argo svc/argo-server 2746:2746"
echo ""
echo "예시:"
echo "  ./submit_job.sh user1 https://example.com/data.pkl"
echo "  ./submit_job.sh user2 '' configs/custom/my_config.py"
