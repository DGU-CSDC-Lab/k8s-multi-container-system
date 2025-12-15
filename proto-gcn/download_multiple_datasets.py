#!/usr/bin/env python3
"""
병렬 처리 테스트를 위한 다양한 데이터셋 다운로드
"""
import os
import pickle
import numpy as np
from pathlib import Path
import torchvision.datasets as datasets
import torchvision.transforms as transforms

def convert_to_protogcn_format(dataset, dataset_name, output_dir):
    """표준 데이터셋을 proto-gcn 포맷으로 변환"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    annotations = []
    split = {"train": [], "test": []}
    
    # Train 데이터 처리
    train_dataset, test_dataset = dataset
    
    for idx, (image, label) in enumerate(train_dataset):
        frame_dir = f"{dataset_name}_train_{idx:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": int(label),
            "img_shape": list(image.shape),
            "original_shape": list(image.shape),
            "total_frames": 1,
            "modality": "RGB",
            "dataset_source": dataset_name
        })
        split["train"].append(frame_dir)
    
    # Test 데이터 처리  
    for idx, (image, label) in enumerate(test_dataset):
        frame_dir = f"{dataset_name}_test_{idx:06d}"
        annotations.append({
            "frame_dir": frame_dir,
            "label": int(label),
            "img_shape": list(image.shape),
            "original_shape": list(image.shape),
            "total_frames": 1,
            "modality": "RGB",
            "dataset_source": dataset_name
        })
        split["test"].append(frame_dir)
    
    # PKL 파일 생성
    data = {
        "annotations": annotations,
        "split": split
    }
    
    output_file = output_dir / f"{dataset_name}.pkl"
    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    
    file_size = output_file.stat().st_size / 1024 / 1024
    print(f"Created: {output_file}")
    print(f"Train: {len(split['train'])}, Test: {len(split['test'])}")
    print(f"Size: {file_size:.1f} MB\n")
    
    return output_file

def download_all_datasets():
    """여러 데이터셋을 병렬로 다운로드"""
    transform = transforms.Compose([transforms.ToTensor()])
    
    datasets_info = [
        {
            "name": "cifar10",
            "loader": lambda: (
                datasets.CIFAR10('./temp_data', train=True, download=True, transform=transform),
                datasets.CIFAR10('./temp_data', train=False, download=True, transform=transform)
            ),
            "description": "10 classes, 32x32 images"
        },
        {
            "name": "cifar100", 
            "loader": lambda: (
                datasets.CIFAR100('./temp_data', train=True, download=True, transform=transform),
                datasets.CIFAR100('./temp_data', train=False, download=True, transform=transform)
            ),
            "description": "100 classes, 32x32 images"
        },
        {
            "name": "fashion_mnist",
            "loader": lambda: (
                datasets.FashionMNIST('./temp_data', train=True, download=True, transform=transform),
                datasets.FashionMNIST('./temp_data', train=False, download=True, transform=transform)
            ),
            "description": "10 fashion classes, 28x28 grayscale"
        },
        {
            "name": "mnist",
            "loader": lambda: (
                datasets.MNIST('./temp_data', train=True, download=True, transform=transform),
                datasets.MNIST('./temp_data', train=False, download=True, transform=transform)
            ),
            "description": "10 digit classes, 28x28 grayscale"
        },
        {
            "name": "svhn",
            "loader": lambda: (
                datasets.SVHN('./temp_data', split='train', download=True, transform=transform),
                datasets.SVHN('./temp_data', split='test', download=True, transform=transform)
            ),
            "description": "10 digit classes, 32x32 street view"
        }
    ]
    
    created_files = []
    
    print("=== 다중 데이터셋 다운로드 시작 ===\n")
    
    for dataset_info in datasets_info:
        print(f"Processing {dataset_info['name']} - {dataset_info['description']}")
        try:
            dataset_pair = dataset_info['loader']()
            output_file = convert_to_protogcn_format(
                dataset_pair, 
                dataset_info['name'], 
                f"data/{dataset_info['name']}"
            )
            created_files.append(output_file)
        except Exception as e:
            print(f"Error with {dataset_info['name']}: {e}\n")
            continue
    
    return created_files

def create_parallel_test_configs(dataset_files):
    """병렬 테스트를 위한 설정 파일들 생성"""
    configs_dir = Path("data/parallel_configs")
    configs_dir.mkdir(exist_ok=True)
    
    # 2개 병렬 조합
    for i in range(len(dataset_files)):
        for j in range(i+1, len(dataset_files)):
            config_name = f"parallel_2_{dataset_files[i].stem}_{dataset_files[j].stem}"
            config_file = configs_dir / f"{config_name}.txt"
            
            with open(config_file, 'w') as f:
                f.write(f"{dataset_files[i]}\n")
                f.write(f"{dataset_files[j]}\n")
    
    # 3개 병렬 조합 (처음 3개)
    if len(dataset_files) >= 3:
        config_file = configs_dir / "parallel_3_mixed.txt"
        with open(config_file, 'w') as f:
            for i in range(3):
                f.write(f"{dataset_files[i]}\n")
    
    # 4개 병렬 조합 (처음 4개)
    if len(dataset_files) >= 4:
        config_file = configs_dir / "parallel_4_mixed.txt"
        with open(config_file, 'w') as f:
            for i in range(4):
                f.write(f"{dataset_files[i]}\n")
    
    print(f"병렬 테스트 설정 파일들이 {configs_dir}에 생성되었습니다.")

if __name__ == "__main__":
    # 다중 데이터셋 다운로드
    dataset_files = download_all_datasets()
    
    # 병렬 테스트 설정 생성
    create_parallel_test_configs(dataset_files)
    
    print("=== 다운로드 완료 ===")
    print("생성된 데이터셋:")
    for i, file in enumerate(dataset_files, 1):
        print(f"{i}. {file}")
    
    print("\n병렬 테스트 예시:")
    print("# 2개 병렬")
    print(f"export DATASET_PKL='{dataset_files[0]}'")
    print(f"export DATASET_PKL_2='{dataset_files[1]}'")
    print("# 동시 실행...")
    
    print("\n# 3개 병렬")
    for i in range(min(3, len(dataset_files))):
        print(f"export DATASET_PKL_{i+1}='{dataset_files[i]}'")
