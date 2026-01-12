from flask import Flask, request, jsonify
import json
import sqlite3
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)

class ContinualLearningDNNAbacus:
    """지속적 학습이 가능한 DNNAbacus 구현"""
    
    def __init__(self, db_path="performance_data.db"):
        self.db_path = db_path
        self.init_database()
        
        # 학습 가능한 파라미터들
        self.efficiency_factors = self.load_efficiency_factors()
        self.hardware_corrections = self.load_hardware_corrections()
        
    def init_database(self):
        """성능 데이터 저장용 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 실행 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS execution_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_hash TEXT,
                hardware_spec TEXT,
                predicted_time REAL,
                actual_time REAL,
                predicted_memory REAL,
                actual_memory REAL,
                predicted_utilization REAL,
                actual_utilization REAL,
                timestamp DATETIME,
                model_features TEXT
            )
        ''')
        
        # 학습된 효율성 계수 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS efficiency_factors (
                operation_type TEXT PRIMARY KEY,
                efficiency_factor REAL,
                confidence REAL,
                update_count INTEGER,
                last_updated DATETIME
            )
        ''')
        
        # 하드웨어별 보정 계수 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hardware_corrections (
                gpu_model TEXT,
                operation_type TEXT,
                correction_factor REAL,
                confidence REAL,
                PRIMARY KEY (gpu_model, operation_type)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def predict_with_learning(self, model_features, hardware_spec):
        """학습된 파라미터를 사용한 예측"""
        # 기본 DNNAbacus 예측
        base_prediction = self.base_predict(model_features, hardware_spec)
        
        # 학습된 보정 계수 적용
        corrected_prediction = self.apply_learned_corrections(
            base_prediction, model_features, hardware_spec
        )
        
        return corrected_prediction
    
    def record_actual_performance(self, model_features, hardware_spec, 
                                actual_time, actual_memory, actual_utilization):
        """실제 실행 결과 기록 및 학습"""
        
        # 예측값 계산
        prediction = self.predict_with_learning(model_features, hardware_spec)
        
        # 데이터베이스에 기록
        self.store_execution_record(
            model_features, hardware_spec, prediction,
            actual_time, actual_memory, actual_utilization
        )
        
        # 온라인 학습 수행
        self.update_learned_parameters(
            model_features, hardware_spec, prediction,
            actual_time, actual_memory, actual_utilization
        )
        
        return {
            'recorded': True,
            'prediction_error': {
                'time_error': abs(prediction['time'] - actual_time) / actual_time,
                'memory_error': abs(prediction['memory'] - actual_memory) / actual_memory,
                'utilization_error': abs(prediction['utilization'] - actual_utilization) / actual_utilization
            }
        }
    
    def update_learned_parameters(self, model_features, hardware_spec, 
                                prediction, actual_time, actual_memory, actual_utilization):
        """온라인 학습으로 파라미터 업데이트"""
        
        # 1. 효율성 계수 업데이트
        self.update_efficiency_factors(model_features, prediction, actual_time)
        
        # 2. 하드웨어 보정 계수 업데이트
        self.update_hardware_corrections(hardware_spec, prediction, actual_utilization)
        
        # 3. 메모리 예측 모델 업데이트
        self.update_memory_model(model_features, prediction, actual_memory)
    
    def update_efficiency_factors(self, model_features, prediction, actual_time):
        """연산별 효율성 계수 학습"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 계산 그래프에서 각 연산의 기여도 분석
        computation_graph = self.parse_model_graph(model_features)
        
        for node in computation_graph['nodes']:
            operation_type = node['operation']
            
            # 현재 효율성 계수
            current_efficiency = self.efficiency_factors.get(operation_type, 0.7)
            
            # 실제 성능 기반 새로운 효율성 계산
            predicted_contrib = prediction.get(f'{operation_type}_time', 0)
            if predicted_contrib > 0:
                actual_contrib = actual_time * (predicted_contrib / prediction['total_time'])
                new_efficiency = current_efficiency * (predicted_contrib / actual_contrib)
                
                # 지수 이동 평균으로 업데이트 (학습률 0.1)
                learning_rate = 0.1
                updated_efficiency = (1 - learning_rate) * current_efficiency + learning_rate * new_efficiency
                
                # 데이터베이스 업데이트
                cursor.execute('''
                    INSERT OR REPLACE INTO efficiency_factors 
                    (operation_type, efficiency_factor, confidence, update_count, last_updated)
                    VALUES (?, ?, ?, 
                           COALESCE((SELECT update_count FROM efficiency_factors WHERE operation_type = ?) + 1, 1),
                           ?)
                ''', (operation_type, updated_efficiency, 0.8, operation_type, datetime.now()))
                
                self.efficiency_factors[operation_type] = updated_efficiency
        
        conn.commit()
        conn.close()
    
    def update_hardware_corrections(self, hardware_spec, prediction, actual_utilization):
        """하드웨어별 보정 계수 학습"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        gpu_model = hardware_spec.get('gpu_model', 'unknown')
        
        # 예측 사용률 vs 실제 사용률 비교
        predicted_utilization = prediction.get('utilization', 50.0)
        
        if predicted_utilization > 0:
            correction_factor = actual_utilization / predicted_utilization
            
            # 기존 보정 계수 조회
            cursor.execute('''
                SELECT correction_factor FROM hardware_corrections 
                WHERE gpu_model = ? AND operation_type = 'general'
            ''', (gpu_model,))
            
            result = cursor.fetchone()
            current_correction = result[0] if result else 1.0
            
            # 지수 이동 평균으로 업데이트
            learning_rate = 0.05
            updated_correction = (1 - learning_rate) * current_correction + learning_rate * correction_factor
            
            cursor.execute('''
                INSERT OR REPLACE INTO hardware_corrections 
                (gpu_model, operation_type, correction_factor, confidence)
                VALUES (?, 'general', ?, 0.9)
            ''', (gpu_model, updated_correction))
            
            self.hardware_corrections[(gpu_model, 'general')] = updated_correction
        
        conn.commit()
        conn.close()
    
    def get_prediction_accuracy(self, days=30):
        """최근 예측 정확도 분석"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                AVG(ABS(predicted_time - actual_time) / actual_time) as time_mape,
                AVG(ABS(predicted_memory - actual_memory) / actual_memory) as memory_mape,
                AVG(ABS(predicted_utilization - actual_utilization) / actual_utilization) as util_mape,
                COUNT(*) as sample_count
            FROM execution_records 
            WHERE timestamp > datetime('now', '-{} days')
        '''.format(days))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'time_accuracy': 1 - (result[0] or 0),
            'memory_accuracy': 1 - (result[1] or 0), 
            'utilization_accuracy': 1 - (result[2] or 0),
            'sample_count': result[3] or 0,
            'confidence': min(1.0, (result[3] or 0) / 100)  # 100개 샘플 기준
        }

# 지속적 학습 API 엔드포인트
continual_learner = ContinualLearningDNNAbacus()

@app.route('/predict-with-learning', methods=['POST'])
def predict_with_learning():
    """학습된 모델로 예측"""
    data = request.get_json()
    model_features = data.get('model_features', {})
    hardware_spec = data.get('hardware_spec', {})
    
    prediction = continual_learner.predict_with_learning(model_features, hardware_spec)
    accuracy = continual_learner.get_prediction_accuracy()
    
    return jsonify({
        'prediction': prediction,
        'model_accuracy': accuracy,
        'learning_enabled': True
    })

@app.route('/record-performance', methods=['POST'])
def record_performance():
    """실제 성능 기록 및 학습"""
    data = request.get_json()
    
    result = continual_learner.record_actual_performance(
        data.get('model_features', {}),
        data.get('hardware_spec', {}),
        data.get('actual_time', 0),
        data.get('actual_memory', 0),
        data.get('actual_utilization', 0)
    )
    
    return jsonify(result)

@app.route('/learning-stats', methods=['GET'])
def learning_stats():
    """학습 통계 조회"""
    accuracy = continual_learner.get_prediction_accuracy()
    return jsonify(accuracy)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
