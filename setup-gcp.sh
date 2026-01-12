#!/bin/bash

# GCP 프로젝트 설정 스크립트

set -e

echo "=== GCP 프로젝트 설정 시작 ==="

# 프로젝트 ID 입력
read -p "GCP 프로젝트 ID를 입력하세요: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "프로젝트 ID가 필요합니다."
    exit 1
fi

echo "프로젝트 설정: $PROJECT_ID"
gcloud config set project $PROJECT_ID

echo "=== API 활성화 ==="
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com

echo "=== 서비스 계정 생성 ==="
SERVICE_ACCOUNT_NAME="github-actions"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 기존 서비스 계정 확인
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL >/dev/null 2>&1; then
    echo "서비스 계정이 이미 존재합니다: $SERVICE_ACCOUNT_EMAIL"
else
    echo "서비스 계정 생성 중..."
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --description="GitHub Actions deployment" \
        --display-name="GitHub Actions"
fi

echo "=== 역할 부여 ==="
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin"

echo "=== 서비스 계정 키 생성 ==="
KEY_FILE="gcp-service-account-key.json"

if [ -f "$KEY_FILE" ]; then
    echo "기존 키 파일을 백업합니다..."
    mv "$KEY_FILE" "${KEY_FILE}.backup.$(date +%s)"
fi

gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

echo "=== 설정 완료 ==="
echo ""
echo "다음 정보를 GitHub Secrets에 추가하세요:"
echo ""
echo "1. GCP_PROJECT_ID: $PROJECT_ID"
echo "2. GCP_SA_KEY: $(cat $KEY_FILE)"
echo "3. OPENAI_API_KEY: your-openai-api-key"
echo ""
echo "키 파일이 생성되었습니다: $KEY_FILE"
echo "⚠️  보안을 위해 키 파일을 안전한 곳에 보관하고 Git에 커밋하지 마세요!"
echo ""
echo "GitHub Repository > Settings > Secrets and variables > Actions에서 설정하세요."
