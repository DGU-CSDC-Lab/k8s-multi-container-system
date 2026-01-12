# AI-Powered Container Analysis System

## 빠른 시작

### 1. 환경 설정
```bash
# 환경변수 설정 도우미 실행
./setup-env.sh

# .env 파일에서 OpenAI API 키 설정
nano .env
# OPENAI_API_KEY=your-actual-api-key-here
```

### 2. 서비스 실행
```bash
./run-services.sh
```

### 3. 테스트
```bash
python3 test-comprehensive.py
```

## 환경변수 설명

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 (필수) | - |
| `IMAGE_ANALYSIS_PORT` | 이미지 분석 서비스 포트 | 5000 |
| `PERFORMANCE_PREDICTION_PORT` | 성능 예측 서비스 포트 | 5001 |
| `AI_MODEL` | 사용할 AI 모델 | gpt-4o-mini |
| `MAX_FILES_TO_ANALYZE` | 분석할 최대 파일 수 | 15 |
| `MAX_FILE_SIZE_KB` | 파일당 최대 크기 (KB) | 5 |

## 구조

```
system/
├── .env                    # 환경변수 설정
├── .env.example           # 환경변수 예시
├── setup-env.sh           # 환경설정 도우미
├── run-services.sh        # 서비스 실행
├── test-comprehensive.py  # 포괄적 테스트
├── image-analysis-service/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── performance-prediction-service/
    ├── app.py
    ├── requirements.txt
    └── Dockerfile
```

## 주요 개선사항

### ✅ 전체 파일시스템 스캔
- 하드코딩된 경로 제거
- 모든 컨테이너 구조 지원

### ✅ AI 기반 중요 파일 식별
- AI가 학습 관련 파일 자동 선별
- 불필요한 시스템 파일 제외

### ✅ 환경변수 기반 설정
- 유연한 설정 관리
- 프로덕션 환경 대응

### ✅ 범용 모델 지원
- ProtoGCN, ResNet, BERT, YOLO 등
- 새로운 모델 자동 감지

## API 사용법

### Image Analysis Service (Port 5000)

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_url": "any-model:latest"}'
```

### Performance Prediction Service (Port 5001)

```bash
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_features": {...},
    "hardware_spec": {"gpu_model": "RTX4090"}
  }'
```
