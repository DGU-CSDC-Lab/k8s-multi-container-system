from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio

app = FastAPI()

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kubernetes PV의 실제 hostPath와 동일하게 변경
UPLOAD_DIR = "/run/desktop/mnt/host/wsl/protogcn/uploads"
RESULT_DIR = "/run/desktop/mnt/host/wsl/protogcn/results"

ARGO_PATH = "/usr/local/bin/argo"
WORKFLOW_PATH = "/home/eunji/project/k8s-multi-container-system/k8s/workflow.yaml"

# --- kubeconfig 환경변수 설정 ---
os.environ["KUBECONFIG"] = "/home/eunji/.kube/config"

@app.post("/upload-multi")
async def upload_multi(user: str = Form(...), files: list[UploadFile] = File(...)):
    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)
    uploaded = []
    for file in files:
        dest_path = os.path.join(user_dir, file.filename)
        with open(dest_path, "wb") as f:
            f.write(await file.read())
        uploaded.append(file.filename)
    return {"status": "uploaded", "files": uploaded}


@app.post("/run")
async def run_workflow(user: str = Form(...)):
    cmd = [
        ARGO_PATH,
        "submit",
        WORKFLOW_PATH,
        "-n", "argo",                    # 워크플로 네임스페이스 고정
        "--serviceaccount", "argo-server",  # 권한 있는 SA로 실행
        "-p", f"user={user}"
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "KUBECONFIG": "/home/eunji/.kube/config"},
        )
        stdout, stderr = await process.communicate()
        return {
            "status": "submitted" if process.returncode == 0 else "failed",
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Argo CLI(argo)를 찾을 수 없습니다. 절대 경로를 확인하세요.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/summary/{user}")
def get_summary(user: str):
    path = os.path.join(RESULT_DIR, user, "summary.csv")
    if os.path.exists(path):
        return PlainTextResponse(open(path).read(), media_type="text/csv")
    return PlainTextResponse("Summary not found.", status_code=404)
