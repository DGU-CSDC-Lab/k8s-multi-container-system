###  시간 딜레이 원인

1. 컨테이너를 Pod 단위로 묶어서 병렬 처리하는 경우, CUDA Build에만 7분 이상 걸림 (약 7-8분 사이)

듬
### UX 개선 문제
데이터 로드. 패키지 설치 등 (나중에는 보지 않겠지만) 의존성과 실제 코드 사이 워크플로우 차이가 없어서 확인이 힘듬
## 트러블슈팅

### GPU 메모리 과다 사용 문제

**문제 상황**:
- 로컬 환경: Proto-GCN 학습 시 776MB GPU 메모리 사용
- 컨테이너 환경: 동일한 코드가 9GB+ GPU 메모리 사용
- 결과: `CUDA out of memory` 에러 발생

**원인 분석**:
```bash
# 로컬에서 PyTorch 메모리 사용량
Memory allocated: 3.7e-05 GB
Memory reserved: 0.002 GB

# 컨테이너에서 PyTorch 메모리 사용량  
Memory allocated: 6.55 GB
Memory reserved: 6.91 GB
```

**근본 원인**:
- Kubernetes에서 `nvidia.com/gpu: 1` 리소스 할당 시
- PyTorch가 "전체 GPU가 내 전용"이라고 판단
- 컨테이너 환경에서 더 aggressive한 메모리 할당 정책 사용

**해결 방법**:

1. **PyTorch 메모리 제한 설정**:
```python
import torch
# GPU 메모리의 20%만 사용 (약 2GB)
torch.cuda.set_per_process_memory_fraction(0.2)
```

2. **환경변수 설정**:
```bash
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:32
```

3. **배치 크기 최소화**:
```python
data = dict(
    videos_per_gpu=1,  # 최소값
    workers_per_gpu=1,
)
```

**검증 방법**:
```bash
# 실행 중 GPU 메모리 모니터링
nvidia-smi

# 컨테이너 vs 로컬 메모리 사용량 비교
# 로컬: 776MB
# 컨테이너 (수정 전): 9800MB  
# 컨테이너 (수정 후): 예상 ~1GB
```

**교훈**:
- 컨테이너 환경에서는 GPU 메모리 관리가 로컬과 다름
- Kubernetes GPU 리소스 할당 시 PyTorch 메모리 정책 고려 필요
- 멀티 유저 GPU 공유를 위해서는 명시적 메모리 제한 필수
