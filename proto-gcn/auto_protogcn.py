import os
import re
import sys
import json
import time
import glob
import math
import pickle
import shutil
import random
import subprocess
from pathlib import Path
from datetime import datetime
from itertools import product
from typing import Optional

import numpy as np
import pandas as pd

# ===================== USER CONFIG =====================
BASE_CONFIG         = os.environ.get("BASE_CONFIG", "configs/ntu60_xsub/j.py")
# 폴더 또는 와일드카드 패턴 허용 (예: "data/per_camera/out/*.pkl" 또는 "data/per_camera/out")
DATASET_PKL         = os.environ.get("DATASET_PKL", "data/per_camera/out/*.pkl")
DIST_TRAIN_SH       = os.environ.get("DIST_TRAIN_SH","tools/dist_train.sh")
DIST_TEST_SH        = os.environ.get("DIST_TEST_SH", "tools/dist_test.sh")
GPUS                = int(os.environ.get("GPUS", 1))

# Search space
EPOCHS_LIST         = [10, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
CLIP_LEN_LIST       = [10]

# Test metrics + result.pkl save path
TEST_EVALS          = ["top_k_accuracy", "mean_class_accuracy"]
AVERAGE_CLIPS       = None                   # None | "score" | "prob"

# Root directory for all sweep artifacts
RUNS_ROOT           = Path(os.environ.get("RUNS_ROOT", "results"))

# Whether to also parse min val_loss from logs (best effort)
PARSE_VAL_LOSS_FROM_LOG = True

# =======================================================


def now_tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write_text(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def parse_fn_tokens_from_dataset(dataset_pkl: str):
    """파일명에 f####_n#### 토큰이 있으면 그걸, 없으면 파일 스템(stem)을 반환."""
    m = re.search(r"f(\d+)_n(\d+)", dataset_pkl)
    if m:
        return f"f{m.group(1)}_n{m.group(2)}"
    try:
        return Path(dataset_pkl).stem or "dataset"
    except Exception:
        return "dataset"


def make_temp_config(base_cfg: str, out_cfg: Path, epochs: int, clip_len: int, dataset_pkl: str, run_work_dir: Path):
    """
    Run-specific config 생성:
      - ann_file, total_epochs, clip_len, work_dir 오버라이드
    """
    txt = read_text(Path(base_cfg))

    # ann_file replacement
    txt = re.sub(
        r"(?m)^(ann_file\s*=\s*).*$",
        rf'\1{repr(dataset_pkl)}',
        txt
    )

    # total_epochs replacement
    txt = re.sub(
        r"(?m)^(total_epochs\s*=\s*)(\d+)",
        rf"\g<1>{epochs}",
        txt
    )

    # clip_len replacement (all occurrences)
    def repl_cliplen(m):
        return f"{m.group(1)}{clip_len}"
    txt = re.sub(r"(clip_len\s*=\s*)(\d+)", repl_cliplen, txt)

    # work_dir override (force literal path)
    if "work_dir" in txt:
        txt = re.sub(
            r"(?m)^(work_dir\s*=).*$",
            rf'work_dir = {repr(str(run_work_dir))}',
            txt
        )
    else:
        txt += f"\nwork_dir = {repr(str(run_work_dir))}\n"

    write_text(out_cfg, txt)


def run_cmd(cmd, env=None, cwd=None, log_path: Optional[Path] = None):
    """Shell command 실행, stdout을 콘솔+파일에 동시에 기록."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd,
        env=env,
        bufsize=1,
        universal_newlines=True,
    )
    lines = []
    for line in proc.stdout:
        print(line, end="")
        lines.append(line)
    proc.wait()
    rc = proc.returncode
    content = "".join(lines)
    if log_path:
        write_text(log_path, content)
    if rc != 0:
        raise RuntimeError(f"Command failed (rc={rc}): {' '.join(cmd)}")
    return content


def _ms(start_t: float, end_t: float) -> int:
    return int(round((end_t - start_t) * 1000))


def train_once_cpu(cfg_path: Path, log_dir: Path, extra_flags=None):
    """CPU 모드 단일 프로세스 학습 실행"""
    if extra_flags is None:
        extra_flags = ["--validate", "--test-last", "--test-best"]
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "train_stdout.log"
    
    # 환경 변수 설정
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["MKL_SERVICE_FORCE_INTEL"] = "1"
    # 분산 학습 관련 환경 변수 설정
    env["RANK"] = "0"
    env["WORLD_SIZE"] = "1"
    env["LOCAL_RANK"] = "0"
    env["MASTER_ADDR"] = "localhost"
    env["MASTER_PORT"] = "12345"
    
    cmd = ["python", "tools/train.py", str(cfg_path)] + extra_flags
    t0 = time.perf_counter()
    out = run_cmd(cmd, log_path=log_path, env=env)
    t1 = time.perf_counter()
    train_ms = _ms(t0, t1)
    return out, log_path, train_ms, 0  # val_ms는 0으로 설정


def train_once(dist_train_sh: str, cfg_path: Path, gpus: int, log_dir: Path, extra_flags=None):
    """학습 실행 + 전체 소요시간(ms) 반환. 검증 시간은 로그에서 추정."""
    if extra_flags is None:
        extra_flags = ["--validate", "--test-last", "--test-best"]
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "train_stdout.log"
    cmd = ["bash", dist_train_sh, str(cfg_path), str(gpus), *extra_flags]
    t0 = time.perf_counter()
    out = run_cmd(cmd, log_path=log_path)
    t1 = time.perf_counter()
    train_ms = _ms(t0, t1)
    # 검증 시간(best-effort) 파싱
    val_ms = parse_val_wall_ms_from_train_log(log_path)
    return out, log_path, train_ms, val_ms


def find_best_ckpt(work_dir: Path) -> Optional[Path]:
    # Prefer best_val_loss
    cands = sorted(work_dir.glob("best_val_loss_epoch_*.pth"))
    if cands:
        return cands[-1]
    # Next best Top-1
    cands = sorted(work_dir.glob("best_top1_acc_epoch_*.pth"))
    if cands:
        return cands[-1]
    # Fallback to latest
    last = work_dir / "latest.pth"
    if last.exists():
        return last
    # Any .pth at all
    allp = sorted(work_dir.glob("*.pth"))
    return allp[-1] if allp else None


def test_once(dist_test_sh: str, cfg_path: Path, ckpt_path: Path, gpus: int, out_pkl: Path, evals=None, average_clips=None, log_dir: Optional[Path] = None):
    """테스트 실행 + 전체 소요시간(ms) 반환."""
    if evals is None:
        evals = TEST_EVALS
    args = ["--eval"] + evals + ["--out", str(out_pkl)]
    if average_clips:
        args += ["--average-clips", str(average_clips)]
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "test_stdout.log"
    else:
        log_path = None
    cmd = ["bash", dist_test_sh, str(cfg_path), str(ckpt_path), str(gpus), *args]
    t0 = time.perf_counter()
    out = run_cmd(cmd, log_path=log_path)
    t1 = time.perf_counter()
    test_ms = _ms(t0, t1)
    return out, log_path, test_ms


def parse_top1_from_stdout(text: str) -> Optional[float]:
    # Try variations
    m = re.search(r"(?:^|\s)(?:top1|top\-1|top1_acc)\s*[:=]\s*([0-9]*\.?[0-9]+)", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        return val/100.0 if val > 1.0 else val
    m2 = re.search(r"Top\-1\s*Accuracy\s*:\s*([0-9]*\.?[0-9]+)\s*%?", text, re.IGNORECASE)
    if m2:
        val = float(m2.group(1))
        return val/100.0 if val > 1.0 else val
    return None


def safe_div(a, b):
    return a / b if b else 0.0


def labels_from_dataset(dataset_pkl: str, split="test", frame_order=None):
    with open(dataset_pkl, "rb") as f:
        data = pickle.load(f)
    anns = data.get("annotations", [])
    split_map = data.get("split", {})
    label_by_fd = {ann["frame_dir"]: int(ann["label"]) for ann in anns}
    if frame_order:
        y_true = [label_by_fd[x] for x in frame_order if x in label_by_fd]
        return np.array(y_true, dtype=int), True
    if isinstance(split_map, dict) and split in split_map:
        order = split_map[split]
        y_true = [label_by_fd[x] for x in order if x in label_by_fd]
        return np.array(y_true, dtype=int), True
    y_true = np.array([int(ann["label"]) for ann in anns], dtype=int)
    return y_true, False


def load_preds_and_labels(result_pkl: Path, dataset_pkl: str, split="test"):
    with open(result_pkl, "rb") as f:
        obj = pickle.load(f)
    # Case A
    if isinstance(obj, dict):
        pred = obj.get("pred") or obj.get("scores") or obj.get("logits")
        labels = obj.get("label") or obj.get("labels")
        frame_dirs = obj.get("frame_dir") or obj.get("frame_dirs")
        if pred is not None:
            y_score = np.asarray(pred)
            y_pred = y_score.argmax(axis=1)
            if labels is not None:
                y_true = np.asarray(labels).astype(int)
                return y_true, y_pred, y_score
            else:
                y_true, _ = labels_from_dataset(dataset_pkl, split=split, frame_order=frame_dirs)
                n = min(len(y_true), len(y_pred))
                return y_true[:n], y_pred[:n], y_score[:n]
    # Case B
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        scores, order = [], []
        for it in obj:
            if "scores" in it:
                scores.append(it["scores"])
            elif "pred" in it:
                scores.append(it["pred"])
            elif "logits" in it:
                scores.append(it["logits"])
            if "frame_dir" in it:
                order.append(it["frame_dir"])
        y_score = np.asarray(scores)
        y_pred = y_score.argmax(axis=1)
        y_true, _ = labels_from_dataset(dataset_pkl, split=split, frame_order=order if order else None)
        n = min(len(y_true), len(y_pred))
        return y_true[:n], y_pred[:n], y_score[:n]
    # Case C
    if isinstance(obj, list) and obj and not isinstance(obj[0], dict):
        y_score = np.asarray(obj)
        y_pred = y_score.argmax(axis=1)
        y_true, _ = labels_from_dataset(dataset_pkl, split=split, frame_order=None)
        n = min(len(y_true), len(y_pred))
        return y_true[:n], y_pred[:n], y_score[:n]
    raise ValueError("Unsupported format of result.pkl. Please inspect the file structure.")


def compute_binary_metrics(y_true: np.ndarray, y_pred: np.ndarray):
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
    acc = safe_div(tp + tn, len(y_true))
    return dict(tp=tp, tn=tn, fp=fp, fn=fn, precision=precision, recall=recall, f1=f1, acc=acc)


def parse_min_val_loss_from_logs(work_dir: Path) -> Optional[float]:
    logs = sorted(work_dir.glob("*.log"))
    if not logs:
        return None
    best = None
    patts = [
        r"\bval[_/ ]loss[:=]\s*([0-9]*\.?[0-9]+)",
        r"\bval\.loss[:=]\s*([0-9]*\.?[0-9]+)",
        r"\bloss\(val\)[:=]\s*([0-9]*\.?[0-9]+)",
    ]
    for lp in logs:
        try:
            text = read_text(lp)
        except Exception:
            continue
        for m in re.finditer("|".join(patts), text, flags=re.IGNORECASE):
            for p in patts:
                mm = re.search(p, m.group(0), flags=re.IGNORECASE)
                if mm:
                    val = float(mm.group(1))
                    best = val if (best is None or val < best) else best
    return best


def parse_val_wall_ms_from_train_log(log_path: Path) -> Optional[int]:
    """
    학습 로그에서 검증 시간(초)을 best-effort로 추정해 ms로 반환.
    지원 패턴(대/소문자 무시):
      - 'val time: 12.34s', 'validation time: 1.23 s', 'evaluation time=4.56s'
    여러 번 나오면 모두 합산.
    """
    if not log_path or not log_path.exists():
        return None
    text = read_text(log_path)

    # 다양한 포맷을 커버하는 정규식들
    patterns = [
        r"val(?:idation)?\s*time\s*[:=]\s*([0-9]*\.?[0-9]+)\s*s",
        r"evaluation\s*time\s*[:=]\s*([0-9]*\.?[0-9]+)\s*s",
        r"eval\s*time\s*[:=]\s*([0-9]*\.?[0-9]+)\s*s",
    ]
    total_sec = 0.0
    found = False
    for patt in patterns:
        for m in re.finditer(patt, text, flags=re.IGNORECASE):
            try:
                total_sec += float(m.group(1))
                found = True
            except Exception:
                pass
    if found:
        return int(round(total_sec * 1000))
    return None


def main():
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    # --- (1) DATASET_PKL 해석: 폴더/와일드카드/단일 파일 모두 지원 ---
    ds_spec = DATASET_PKL
    dataset_list = []
    p = Path(ds_spec)
    if p.is_dir():
        dataset_list = sorted(p.glob("*.pkl"))
    else:
        matches = glob.glob(ds_spec)
        dataset_list = sorted(map(Path, matches)) if matches else ([p] if p.exists() else [])

    if not dataset_list:
        raise FileNotFoundError(f"No PKL files found for spec: {ds_spec}")

    # --- (2) sweep 루트 디렉토리 ---
    sweep_tag = now_tag()
    sweep_dir = RUNS_ROOT / f"multi_{len(dataset_list)}_{sweep_tag}"
    sweep_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    # --- (3) dataset × epochs × clip_len 모든 조합 실행 ---
    for dataset_path in dataset_list:
        ds_tag = parse_fn_tokens_from_dataset(str(dataset_path))
        ds_stem = dataset_path.stem

        for epochs, clip_len in product(EPOCHS_LIST, CLIP_LEN_LIST):
            run_name = f"{ds_stem}_e{epochs}_cl{clip_len}"
            run_dir  = sweep_dir / run_name
            cfg_dir  = run_dir / "cfg"
            log_dir  = run_dir / "logs"
            out_dir  = run_dir / "outs"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            log_dir.mkdir(parents=True, exist_ok=True)
            out_dir.mkdir(parents=True, exist_ok=True)

            # work_dir도 데이터셋/파라미터별로 분리
            work_dir = Path(f"./work_dirs/synthetic/{ds_tag}_e{epochs}_cl{clip_len}_vl_es")

            # Config 생성 (해당 데이터셋 파일 경로 주입)
            temp_cfg = cfg_dir / f"{Path(BASE_CONFIG).stem}_{run_name}.py"
            make_temp_config(BASE_CONFIG, temp_cfg, epochs, clip_len, str(dataset_path), work_dir)

            # --- Train ---
            print(f"\n==== TRAIN [{run_name}] ====")
            try:
                # CPU 모드인지 확인
                if os.environ.get("CUDA_VISIBLE_DEVICES") == "":
                    train_stdout, train_log_path, train_ms, val_ms = train_once_cpu(temp_cfg, log_dir)
                else:
                    train_stdout, train_log_path, train_ms, val_ms = train_once(DIST_TRAIN_SH, temp_cfg, GPUS, log_dir)
            except Exception as e:
                print(f"[ERROR] Training failed for {run_name}: {e}")
                summary_rows.append(dict(
                    dataset=ds_stem, dataset_path=str(dataset_path),
                    run_name=run_name, epochs=epochs, clip_len=clip_len,
                    train_ms=None, val_ms=None, test_ms=None,
                    status="train_failed"
                ))
                continue

            # --- Best checkpoint ---
            ckpt_path = find_best_ckpt(work_dir)
            if not ckpt_path or not ckpt_path.exists():
                print(f"[ERROR] Best checkpoint not found for {run_name}")
                summary_rows.append(dict(
                    dataset=ds_stem, dataset_path=str(dataset_path),
                    run_name=run_name, epochs=epochs, clip_len=clip_len,
                    train_ms=train_ms, val_ms=val_ms, test_ms=None,
                    status="no_ckpt_found"
                ))
                continue

            best_epoch = None
            m = re.search(r"epoch_(\d+)\.pth", ckpt_path.name)
            if m:
                best_epoch = int(m.group(1))

            # --- Test ---
            print(f"\n==== TEST  [{run_name}] ====")
            out_pkl = out_dir / f"result_{run_name}.pkl"
            try:
                test_stdout, test_log_path, test_ms = test_once(
                    DIST_TEST_SH, temp_cfg, ckpt_path, GPUS, out_pkl,
                    evals=TEST_EVALS, average_clips=AVERAGE_CLIPS, log_dir=log_dir
                )
            except Exception as e:
                print(f"[ERROR] Testing failed for {run_name}: {e}")
                summary_rows.append(dict(
                    dataset=ds_stem, dataset_path=str(dataset_path),
                    run_name=run_name, epochs=epochs, clip_len=clip_len,
                    train_ms=train_ms, val_ms=val_ms, test_ms=None,
                    status="test_failed", ckpt=str(ckpt_path)
                ))
                continue

            top1 = parse_top1_from_stdout(test_stdout)

            # 라벨/예측 로딩도 해당 데이터셋 파일로
            try:
                y_true, y_pred, y_score = load_preds_and_labels(out_pkl, str(dataset_path), split="test")
                metrics = compute_binary_metrics(y_true, y_pred)
                n_test = int(len(y_true))
            except Exception as e:
                print(f"[WARN] Could not compute confusion metrics for {run_name}: {e}")
                metrics = dict(tp=None, tn=None, fp=None, fn=None,
                               precision=None, recall=None, f1=None, acc=None)
                n_test = None

            min_val_loss = parse_min_val_loss_from_logs(work_dir) if PARSE_VAL_LOSS_FROM_LOG else None

            row = dict(
                dataset=ds_stem, dataset_path=str(dataset_path),
                run_name=run_name, epochs=epochs, clip_len=clip_len,
                best_epoch=best_epoch, top1_acc=top1, min_val_loss=min_val_loss,
                n_test=n_test,
                tp=metrics['tp'], tn=metrics['tn'], fp=metrics['fp'], fn=metrics['fn'],
                precision=metrics['precision'], recall=metrics['recall'],
                f1=metrics['f1'], acc=metrics['acc'],
                train_ms=train_ms, val_ms=val_ms, test_ms=test_ms,
                work_dir=str(work_dir), ckpt=str(ckpt_path), result_pkl=str(out_pkl),
                status="ok"
            )
            summary_rows.append(row)

    # Save summary to CSV and XLSX
    df = pd.DataFrame(summary_rows)
    csv_path = sweep_dir / "summary.csv"
    xlsx_path = sweep_dir / "summary.xlsx"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="summary", index=False)

    print("\n=== DONE ===")
    print(f"Summary CSV : {csv_path}")
    print(f"Summary XLSX: {xlsx_path}")
    print(f"Sweep root  : {sweep_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())