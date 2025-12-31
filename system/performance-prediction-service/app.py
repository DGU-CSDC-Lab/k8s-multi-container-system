from flask import Flask, request, jsonify
import math
import json

app = Flask(__name__)

class GPUPredictor:
    def __init__(self):
        # GPU 모델별 사양 (예시)
        self.gpu_specs = {
            'rtx4090': {'sm_count': 128, 'cores_per_sm': 128, 'memory_gb': 24, 'bandwidth_gbps': 1008},
            'rtx3080': {'sm_count': 68, 'cores_per_sm': 128, 'memory_gb': 10, 'bandwidth_gbps': 760},
            'v100': {'sm_count': 80, 'cores_per_sm': 64, 'memory_gb': 32, 'bandwidth_gbps': 900}
        }
    
    def predict(self, model_features, hardware_spec):
        """GPU SM 사용률 예측"""
        model_type = model_features.get('model_info', {}).get('type', 'unknown')
        batch_size = model_features.get('training_config', {}).get('batch_size', 32)
        
        # 모델별 연산 강도 계산
        compute_intensity = self._calculate_compute_intensity(model_type, batch_size)
        
        # GPU 사양 가져오기
        gpu_model = hardware_spec.get('gpu_model', 'rtx4090').lower()
        gpu_spec = self.gpu_specs.get(gpu_model, self.gpu_specs['rtx4090'])
        
        # SM 사용률 계산 (0-100%)
        max_throughput = gpu_spec['sm_count'] * gpu_spec['cores_per_sm']
        utilization = min(100.0, (compute_intensity / max_throughput) * 100)
        
        return {
            'sm_utilization': round(utilization, 2),
            'sm_utilization_std': round(utilization * 0.1, 2),  # 10% 표준편차
            'bottleneck': 'compute' if utilization > 80 else 'memory'
        }
    
    def _calculate_compute_intensity(self, model_type, batch_size):
        """모델별 연산 강도 계산"""
        base_ops = {
            'protogcn': 1000000,  # 1M ops
            'resnet': 4000000,    # 4M ops  
            'transformer': 8000000, # 8M ops
            'unknown': 2000000    # 2M ops (기본값)
        }
        
        ops_per_sample = base_ops.get(model_type, base_ops['unknown'])
        return ops_per_sample * batch_size

class MemoryPredictor:
    def predict(self, model_features):
        """메모리 사용량 예측"""
        model_type = model_features.get('model_info', {}).get('type', 'unknown')
        batch_size = model_features.get('training_config', {}).get('batch_size', 32)
        num_classes = model_features.get('data_info', {}).get('num_classes', 1000)
        
        # 모델별 기본 메모리 사용량 (MB)
        base_memory = {
            'protogcn': 2048,    # 2GB
            'resnet': 4096,      # 4GB
            'transformer': 8192, # 8GB
            'unknown': 3072      # 3GB
        }
        
        model_memory = base_memory.get(model_type, base_memory['unknown'])
        
        # 배치 크기에 따른 추가 메모리
        batch_memory = batch_size * 64  # 64MB per batch
        
        # 클래스 수에 따른 추가 메모리
        class_memory = num_classes * 4  # 4MB per 1000 classes
        
        total_memory = model_memory + batch_memory + class_memory
        peak_memory = total_memory * 1.3  # 30% 여유분
        
        return {
            'memory_usage_mb': round(total_memory, 2),
            'memory_peak_mb': round(peak_memory, 2),
            'memory_utilization': round((total_memory / 24576) * 100, 2)  # 24GB 기준
        }

class TimePredictor:
    def predict(self, model_features, hardware_spec):
        """학습 시간 예측"""
        model_type = model_features.get('model_info', {}).get('type', 'unknown')
        batch_size = model_features.get('training_config', {}).get('batch_size', 32)
        epochs = model_features.get('training_config', {}).get('epochs', 100)
        
        # 모델별 배치당 기본 시간 (초)
        base_time_per_batch = {
            'protogcn': 0.5,     # 0.5초
            'resnet': 0.3,       # 0.3초
            'transformer': 1.2,  # 1.2초
            'unknown': 0.8       # 0.8초
        }
        
        time_per_batch = base_time_per_batch.get(model_type, base_time_per_batch['unknown'])
        
        # 배치 크기에 따른 시간 조정
        time_per_batch *= math.log(batch_size) / math.log(32)  # 32를 기준으로 스케일링
        
        # GPU 성능에 따른 조정
        gpu_model = hardware_spec.get('gpu_model', 'rtx4090').lower()
        gpu_multiplier = {
            'rtx4090': 1.0,
            'rtx3080': 1.5,
            'v100': 1.2
        }
        time_per_batch *= gpu_multiplier.get(gpu_model, 1.0)
        
        # 전체 학습 시간 계산 (1000 배치/에폭 가정)
        batches_per_epoch = 1000
        total_time = time_per_batch * epochs * batches_per_epoch
        
        return {
            'estimated_time_seconds': round(total_time, 2),
            'time_per_epoch_seconds': round(total_time / epochs, 2),
            'time_per_batch_ms': round(time_per_batch * 1000, 2)
        }

# 예측기 초기화
gpu_predictor = GPUPredictor()
memory_predictor = MemoryPredictor()
time_predictor = TimePredictor()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/predict', methods=['POST'])
def predict_performance():
    try:
        data = request.get_json()
        model_features = data.get('model_features', {})
        hardware_spec = data.get('hardware_spec', {})
        
        # 각 예측기로 성능 예측
        gpu_prediction = gpu_predictor.predict(model_features, hardware_spec)
        memory_prediction = memory_predictor.predict(model_features)
        time_prediction = time_predictor.predict(model_features, hardware_spec)
        
        # 결과 통합
        result = {
            'predictions': {
                **gpu_prediction,
                **memory_prediction,
                **time_prediction
            },
            'confidence': 0.85,  # 85% 신뢰도
            'bottleneck_analysis': {
                'compute': gpu_prediction.get('sm_utilization', 0),
                'memory': memory_prediction.get('memory_utilization', 0),
                'io': 20.0  # 고정값
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
