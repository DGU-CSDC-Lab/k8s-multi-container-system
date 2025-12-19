# k8s-multi-container-system
k8s multi container system

## Dependencies
- kublet (v1.34.0)
- containerd (v1.7.0)
- argo workflow (v3.7.6)
- argo cli (v3.7.6) (Optional)

## Installation
### Argo Workflow

```bash 
kubectl create namespace argo
```

```bash
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.7.6/namespace-install.yaml
```

```bash
kubectl get pods -n argo

# argo-server-xxxxx            Running
# workflow-controller-xxxxx    Running
```

### Argo CLI (Optional, CLI 명령문 사용이 필요한 경우)
```bash
curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.7.6/argo-linux-amd64.gz && gunzip argo-linux-amd64.gz && chmod +x argo-linux-amd64 && sudo mv argo-linux-amd64 /usr/local/bin/argo
```

### Show UI
- workflow apply와 함께 생성되는 argo service 조회
```bash
kubectl get svc -n argo
```

- ui port fowarding
```bash
kubectl port-forward -n argo svc/argo-server 2746:2746
```

## Trouble Shootings
### Argo Workflow Pods Not Working
- describe argo server logs
```bash
kubectl get pods -n argo
# NAME                                   READY   STATUS    RESTARTS   AGE
# argo-server-65c4df468c-6gbnl           0/1     Pending   0          98s
# workflow-controller-679c78d9dd-c64td   0/1     Pending   0          98s

kubectl describe pod -n argo argo-server-65c4df468c-6gbnl
```

#### if Reason is `FailedScheduling` and `0/1 nodes are available: 1 node(s) had untolerated taint(s). no new claims to deallocate, preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.`

- remove controlplane taint (단일 노드 클러스터에서 발생하는 문제)
```bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

### Auth Failed
#### if `Failed to load version/info Error: {"code":16,"message":"token not valid. see https://argo-workflows.readthedocs.io/en/latest/faq/"}` in UI

- argo server를 insecure 모드로 설정
```bash
kubectl patch deployment argo-server -n argo --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--auth-mode=server"}]'
```

- 재시작 대기
```bash
kubectl rollout status deployment/argo-server -n argo
```
