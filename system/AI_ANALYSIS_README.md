# AI-Powered Container Analysis System

## 주요 개선사항

### ✅ AI 기반 코드 분석
- **OpenAI GPT-4o-mini** 활용한 실제 AI 분석
- 하드코딩된 패턴 매칭 제거
- 새로운 모델 자동 감지 가능

### ✅ 범용성 확보
- ProtoGCN, ResNet, BERT, YOLO 등 모든 모델 지원
- 코드 수정 없이 새로운 모델 추가 가능
- 프레임워크 무관 (PyTorch, TensorFlow 등)

## 사용법

### 1. OpenAI API 키 설정
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 2. 서비스 실행
```bash
./run-services.sh
```

### 3. 테스트
```bash
# 다양한 모델 테스트 가능
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_url": "any-model:latest"}'
```

## AI 분석 예시

### Input: 임의의 딥러닝 코드
```python
# 컨테이너 내부의 코드
model = YOLOv8(num_classes=80)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
train_loader = DataLoader(dataset, batch_size=16)
```

### Output: AI 자동 분석 결과
```json
{
  "model_info": {
    "type": "yolo",
    "framework": "pytorch",
    "architecture": "YOLOv8 object detection model"
  },
  "training_config": {
    "batch_size": 16,
    "learning_rate": 0.001,
    "optimizer": "adam"
  },
  "data_info": {
    "num_classes": 80
  }
}
```

## 핵심 차이점

### Before (패턴 매칭)
```python
if 'protogcn' in code:
    model_type = 'protogcn'  # 하드코딩
```

### After (AI 분석)
```python
ai_response = openai.analyze(code)
model_type = ai_response['model_type']  # AI가 자동 감지
```

## 장점
- **확장성**: 새로운 모델 자동 지원
- **정확성**: AI의 코드 이해 능력 활용
- **유연성**: 복잡한 코드 구조도 분석 가능
- **미래 지향**: 아직 나오지 않은 모델도 분석 가능
