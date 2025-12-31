# AI-Powered Container Analysis System

## 구조

```
system/
├── image-analysis-service/
│   ├── app.py              # 이미지 분석 서비스
│   ├── requirements.txt    # 의존성
│   └── Dockerfile         # 컨테이너 이미지
├── performance-prediction-service/
│   ├── app.py              # 성능 예측 서비스  
│   ├── requirements.txt    # 의존성
│   └── Dockerfile         # 컨테이너 이미지
├── run-services.sh         # 서비스 실행 스크립트
└── test-services.py        # 테스트 스크립트
```

## 실행 방법

### 1. 서비스 시작
```bash
./run-services.sh
```

### 2. 테스트 실행
```bash
python3 test-services.py
```

## API 사용법

### Image Analysis Service (Port 5000)

```bash
# 이미지 분석 요청
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "proto-gcn:latest"
  }'
```

**응답 예시:**
```json
{
  "model_info": {
    "type": "protogcn",
    "framework": "pytorch"
  },
  "training_config": {
    "batch_size": 32,
    "learning_rate": 0.001,
    "epochs": 100,
    "optimizer": "adam"
  },
  "data_info": {
    "dataset": "ntu60",
    "num_classes": 60
  }
}
```

### Performance Prediction Service (Port 5001)

```bash
# 성능 예측 요청
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_features": {
      "model_info": {"type": "protogcn", "framework": "pytorch"},
      "training_config": {"batch_size": 32, "epochs": 100}
    },
    "hardware_spec": {
      "gpu_model": "RTX4090",
      "gpu_memory": "24GB"
    }
  }'
```

**응답 예시:**
```json
{
  "predictions": {
    "sm_utilization": 85.2,
    "memory_usage_mb": 4096.0,
    "estimated_time_seconds": 7200.0
  },
  "confidence": 0.85,
  "bottleneck_analysis": {
    "compute": 85.2,
    "memory": 16.7,
    "io": 20.0
  }
}
```

## 주요 기능

### Image Analysis Service
- Docker 이미지에서 코드 파일 추출
- Python 코드 정적 분석
- 모델 타입 자동 감지
- 하이퍼파라미터 추출

### Performance Prediction Service  
- GPU SM 사용률 예측
- 메모리 사용량 예측
- 학습 시간 예측
- 병목 지점 분석

## 확장 가능성
- 다른 딥러닝 프레임워크 지원
- 더 정교한 AI 분석 모델 적용
- 실시간 성능 모니터링 연동
