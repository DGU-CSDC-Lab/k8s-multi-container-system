#!/usr/bin/env python3
"""
표준 데이터셋을 proto-gcn 포맷으로 변환하는 스크립트
"""
import os
import pickle
import numpy as np
from pathlib import Path
import torchvision.datasets as datasets
import torchvision.transforms as transforms

def create_cifar10_pkl(output_dir="data/cifar10"):
    """CIFAR-10을 proto-gcn PKL 포맷으로 변환"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading CIFAR-10...")
    
    # CIFAR-10 다운로드
    transform = transforms.Compose([transforms.ToTensor()])
    
    train_dataset = datasets.CIFAR10('./temp_cifar', train=True, download=True, transform=transform)
    test_dataset = datasets.CIFAR10('./temp_cifar', train=False, download=True, transform=transform)
    
    print("Converting to proto-gcn format...")
    
    # proto-gcn 포맷으로 변환
    annotations = []
    split = {"train": [], "test": []}
    
    # Train 데이터 처리
    for idx, (image, label) in enumerate(train_dataset):
        frame_dir = f"train_{idx:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": int(label),
            "img_shape": list(image.shape),  # [3, 32, 32]
            "original_shape": list(image.shape),
            "total_frames": 1,
            "modality": "RGB"
        })
        split["train"].append(frame_dir)
    
    # Test 데이터 처리  
    for idx, (image, label) in enumerate(test_dataset):
        frame_dir = f"test_{idx:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": int(label),
            "img_shape": list(image.shape),
            "original_shape": list(image.shape),
            "total_frames": 1,
            "modality": "RGB"
        })
        split["test"].append(frame_dir)
    
    # PKL 파일 생성
    data = {
        "annotations": annotations,
        "split": split
    }
    
    output_file = output_dir / "cifar10.pkl"
    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"Created: {output_file}")
    print(f"Train samples: {len(split['train'])}")
    print(f"Test samples: {len(split['test'])}")
    print(f"File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    return output_file

def create_synthetic_small_pkl(output_dir="data/synthetic_small"):
    """소규모 테스트용 합성 데이터셋 생성 (~5MB)"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating small synthetic dataset (~5MB)...")
    
    annotations = []
    split = {"train": [], "test": []}
    
    # 소규모: 1000개 샘플
    n_train = 800
    n_test = 200
    
    # Train 데이터
    for i in range(n_train):
        frame_dir = f"small_train_{i:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": i % 10,  # 10개 클래스
            "img_shape": [3, 64, 64],
            "original_shape": [3, 64, 64],
            "total_frames": 1,
            "modality": "RGB",
            "features": np.random.rand(50).tolist()
        })
        split["train"].append(frame_dir)
    
    # Test 데이터
    for i in range(n_test):
        frame_dir = f"small_test_{i:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": i % 10,
            "img_shape": [3, 64, 64],
            "original_shape": [3, 64, 64],
            "total_frames": 1,
            "modality": "RGB",
            "features": np.random.rand(50).tolist()
        })
        split["test"].append(frame_dir)
    
    data = {
        "annotations": annotations,
        "split": split
    }
    
    output_file = output_dir / "synthetic_small.pkl"
    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    
    actual_size = output_file.stat().st_size / 1024 / 1024
    print(f"Created: {output_file}")
    print(f"Train samples: {len(split['train'])}")
    print(f"Test samples: {len(split['test'])}")
    print(f"File size: {actual_size:.1f} MB")
    
    return output_file

def create_synthetic_medium_pkl(output_dir="data/synthetic_medium"):
    """중간 크기 테스트용 합성 데이터셋 생성 (~50MB)"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating medium synthetic dataset (~50MB)...")
    
    annotations = []
    split = {"train": [], "test": []}
    
    # 중간 크기: 10000개 샘플
    n_train = 8000
    n_test = 2000
    
    # Train 데이터
    for i in range(n_train):
        frame_dir = f"medium_train_{i:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": i % 100,  # 100개 클래스
            "img_shape": [3, 128, 128],
            "original_shape": [3, 128, 128],
            "total_frames": 1,
            "modality": "RGB",
            "features": np.random.rand(200).tolist(),
            "metadata": {
                "augmented": i % 2 == 0,
                "difficulty": np.random.choice(["easy", "medium", "hard"])
            }
        })
        split["train"].append(frame_dir)
    
    # Test 데이터
    for i in range(n_test):
        frame_dir = f"medium_test_{i:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": i % 100,
            "img_shape": [3, 128, 128],
            "original_shape": [3, 128, 128],
            "total_frames": 1,
            "modality": "RGB",
            "features": np.random.rand(200).tolist(),
            "metadata": {
                "augmented": False,
                "difficulty": np.random.choice(["easy", "medium", "hard"])
            }
        })
        split["test"].append(frame_dir)
    
    data = {
        "annotations": annotations,
        "split": split
    }
    
    output_file = output_dir / "synthetic_medium.pkl"
    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    
    actual_size = output_file.stat().st_size / 1024 / 1024
    print(f"Created: {output_file}")
    print(f"Train samples: {len(split['train'])}")
    print(f"Test samples: {len(split['test'])}")
    print(f"File size: {actual_size:.1f} MB")
    
    return output_file

def create_synthetic_large_pkl(output_dir="data/synthetic_large"):
    """대용량 테스트용 합성 데이터셋 생성 (~200MB)"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating large synthetic dataset (~200MB)...")
    
    annotations = []
    split = {"train": [], "test": []}
    
    # 대용량: 50000개 샘플
    n_train = 40000
    n_test = 10000
    
    # Train 데이터
    for i in range(n_train):
        frame_dir = f"large_train_{i:08d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": i % 1000,  # 1000개 클래스
            "img_shape": [3, 224, 224],
            "original_shape": [3, 224, 224],
            "total_frames": 1,
            "modality": "RGB",
            "features": np.random.rand(512).tolist(),
            "embeddings": np.random.rand(128).tolist(),
            "metadata": {
                "augmented": i % 3 != 0,
                "difficulty": np.random.choice(["easy", "medium", "hard", "expert"]),
                "source": f"batch_{i // 1000}",
                "timestamp": f"2024-12-{(i % 30) + 1:02d}"
            }
        })
        split["train"].append(frame_dir)
    
    # Test 데이터
    for i in range(n_test):
        frame_dir = f"large_test_{i:08d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": i % 1000,
            "img_shape": [3, 224, 224],
            "original_shape": [3, 224, 224],
            "total_frames": 1,
            "modality": "RGB",
            "features": np.random.rand(512).tolist(),
            "embeddings": np.random.rand(128).tolist(),
            "metadata": {
                "augmented": False,
                "difficulty": np.random.choice(["easy", "medium", "hard", "expert"]),
                "source": f"test_batch_{i // 1000}",
                "timestamp": f"2024-12-{(i % 30) + 1:02d}"
            }
        })
        split["test"].append(frame_dir)
    
    data = {
        "annotations": annotations,
        "split": split
    }
    
    output_file = output_dir / "synthetic_large.pkl"
    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    
    actual_size = output_file.stat().st_size / 1024 / 1024
    print(f"Created: {output_file}")
    print(f"Train samples: {len(split['train'])}")
    print(f"Test samples: {len(split['test'])}")
    print(f"File size: {actual_size:.1f} MB")
    
    return output_file

if __name__ == "__main__":
    print("=== 벤치마크 데이터셋 생성 시작 ===\n")
    
    # 1. CIFAR-10 (실제 데이터)
    cifar_file = create_cifar10_pkl()
    print()
    
    # 2. 소규모 합성 데이터
    small_file = create_synthetic_small_pkl()
    print()
    
    # 3. 중간 크기 합성 데이터
    medium_file = create_synthetic_medium_pkl()
    print()
    
    # 4. 대용량 합성 데이터  
    large_file = create_synthetic_large_pkl()
    print()
    
    print("=== 생성 완료 ===")
    print(f"1. 실제 데이터 (CIFAR-10): {cifar_file}")
    print(f"2. 소규모 (~5MB): {small_file}")
    print(f"3. 중간 크기 (~50MB): {medium_file}")
    print(f"4. 대용량 (~200MB): {large_file}")
    print("\n사용법:")
    print(f"export DATASET_PKL='{cifar_file}'")
    print("python auto_protogcn.py")
