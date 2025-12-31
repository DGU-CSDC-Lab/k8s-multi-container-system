#!/usr/bin/env python3

import requests
import json

def test_comprehensive_analysis():
    """개선된 전체 파일시스템 분석 테스트"""
    url = "http://localhost:5000/analyze"
    
    # 다양한 이미지 테스트
    test_images = [
        "proto-gcn:latest",
        "pytorch/pytorch:latest", 
        "tensorflow/tensorflow:latest",
        "nginx:latest"  # 비 ML 이미지도 테스트
    ]
    
    for image in test_images:
        print(f"\n=== Testing {image} ===")
        
        test_data = {"image_url": image}
        
        try:
            response = requests.post(url, json=test_data, timeout=60)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Model Type: {result.get('model_info', {}).get('type', 'unknown')}")
                print(f"Framework: {result.get('model_info', {}).get('framework', 'unknown')}")
                print(f"Batch Size: {result.get('training_config', {}).get('batch_size', 'N/A')}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")

def test_performance_prediction():
    """성능 예측 테스트"""
    url = "http://localhost:5001/predict"
    
    # 다양한 모델 타입 테스트
    test_cases = [
        {
            "name": "ProtoGCN",
            "model_features": {
                "model_info": {"type": "protogcn", "framework": "pytorch"},
                "training_config": {"batch_size": 32, "epochs": 100},
                "data_info": {"num_classes": 60}
            }
        },
        {
            "name": "ResNet50",
            "model_features": {
                "model_info": {"type": "resnet", "framework": "pytorch"},
                "training_config": {"batch_size": 64, "epochs": 200},
                "data_info": {"num_classes": 1000}
            }
        },
        {
            "name": "BERT",
            "model_features": {
                "model_info": {"type": "transformer", "framework": "pytorch"},
                "training_config": {"batch_size": 16, "epochs": 10},
                "data_info": {"num_classes": 2}
            }
        }
    ]
    
    hardware_spec = {
        "gpu_model": "RTX4090",
        "gpu_memory": "24GB"
    }
    
    for case in test_cases:
        print(f"\n=== Testing {case['name']} Performance Prediction ===")
        
        test_data = {
            "model_features": case["model_features"],
            "hardware_spec": hardware_spec
        }
        
        try:
            response = requests.post(url, json=test_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                predictions = result.get('predictions', {})
                print(f"SM Utilization: {predictions.get('sm_utilization', 'N/A')}%")
                print(f"Memory Usage: {predictions.get('memory_usage_mb', 'N/A')} MB")
                print(f"Training Time: {predictions.get('estimated_time_seconds', 'N/A')} seconds")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    print("=== Comprehensive System Test ===")
    test_comprehensive_analysis()
    test_performance_prediction()
