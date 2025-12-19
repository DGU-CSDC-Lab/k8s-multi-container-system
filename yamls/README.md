# Workflow Comparison

## 직렬 vs 병렬 처리 비교

### 직렬 워크플로 (workflow-serial.yaml)
- **구조**: 1개 컨테이너에서 77개 실험 순차 실행
- **실행**: `argo submit workflow-serial.yaml -n argo --serviceaccount argo-server -p user=serial-test`
- **특징**: 
  - 리소스 효율적
  - 총 시간 = 77 × 개별실험시간
  - 하나 실패시 전체 중단 가능

### 병렬 워크플로 (workflow-parallel.yaml)  
- **구조**: 17개 컨테이너가 각각 1개 실험씩 동시 실행
- **실행**: `argo submit workflow-parallel.yaml -n argo --serviceaccount argo-server -p user=parallel-test`
- **특징**:
  - 빠른 실행 (이론적으로 17배 빠름)
  - 총 시간 = max(개별실험시간들)
  - 독립적 실패 처리
  - 더 많은 리소스 사용

## 성능 비교 포인트
1. **실행 시간**: 직렬 vs 병렬 속도 차이
2. **리소스 사용량**: CPU/GPU/메모리 효율성
3. **스케줄링 오버헤드**: K8s 팟 생성/관리 비용
4. **실패 처리**: 개별 실험 실패 시 영향 범위
5. **확장성**: 실험 수 증가 시 성능 변화

## 실행 예시
```bash
# 직렬 실행
argo submit workflow-serial.yaml -n argo --serviceaccount argo-server -p user=serial-$(date +%s)

# 병렬 실행  
argo submit workflow-parallel.yaml -n argo --serviceaccount argo-server -p user=parallel-$(date +%s)

# 결과 비교
argo list -n argo
```
