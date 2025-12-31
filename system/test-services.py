#!/usr/bin/env python3

import requests
import json

def test_image_analysis():
    """Image Analysis Service 테스트"""
    url = "http://localhost:5000/analyze"
    
    # 테스트 데이터
    test_data = {
        "image_url": "proto-gcn:latest"
    }
    
    try:
        response = requests.post(url, json=test_data)
        print("=== Image Analysis Service Test ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error testing Image Analysis Service: {e}")
        return None

def test_performance_prediction(model_features=None):
    """Performance Prediction Service 테스트"""
    url = "http://localhost:5001/predict"
    
    # 기본 테스트 데이터 또는 이전 단계 결과 사용
    if model_features is None:
        model_features = {
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
    
    test_data = {
        "model_features": model_features,
        "hardware_spec": {
            "gpu_model": "RTX4090",
            "gpu_memory": "24GB"
        }
    }
    
    try:
        response = requests.post(url, json=test_data)
        print("\n=== Performance Prediction Service Test ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error testing Performance Prediction Service: {e}")
        return None

def test_full_pipeline():
    """전체 파이프라인 테스트"""
    print("=== Full Pipeline Test ===")
    
    # 1. Image Analysis
    analysis_result = test_image_analysis()
    
    # 2. Performance Prediction (분석 결과 사용)
    if analysis_result:
        prediction_result = test_performance_prediction(analysis_result)
    else:
        prediction_result = test_performance_prediction()
    
    print("\n=== Pipeline Complete ===")

if __name__ == "__main__":
    test_full_pipeline()
