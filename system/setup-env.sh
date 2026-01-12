#!/bin/bash

# 환경변수 설정 가이드
echo "=== 환경변수 설정 가이드 ==="

# .env 파일이 없으면 생성
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ".env 파일이 생성되었습니다."
else
    echo ".env 파일이 이미 존재합니다."
fi

echo ""
echo "다음 단계를 따라 설정하세요:"
echo ""
echo "1. OpenAI API 키 발급:"
echo "   - https://platform.openai.com/api-keys 방문"
echo "   - 새 API 키 생성"
echo ""
echo "2. .env 파일 수정:"
echo "   - nano .env 또는 원하는 에디터로 열기"
echo "   - OPENAI_API_KEY=your-actual-key-here 수정"
echo ""
echo "3. 서비스 실행:"
echo "   - ./run-services.sh"
echo ""
echo "현재 .env 파일 내용:"
echo "========================"
cat .env
echo "========================"
echo ""
echo "OpenAI API 키가 설정되었는지 확인하세요!"

# API 키 확인
if grep -q "your-openai-api-key-here" .env; then
    echo ""
    echo "⚠️  WARNING: OpenAI API 키가 아직 설정되지 않았습니다!"
    echo "   .env 파일에서 OPENAI_API_KEY를 실제 키로 변경하세요."
else
    echo ""
    echo "✅ OpenAI API 키가 설정된 것 같습니다."
fi
