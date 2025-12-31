from flask import Flask, request, jsonify
import docker
import tarfile
import tempfile
import os
import json
import requests
from pathlib import Path

app = Flask(__name__)

class ImageExtractor:
    def __init__(self):
        self.client = docker.from_env()
    
    def extract_files(self, image_name):
        """Docker 이미지에서 모든 코드 파일 추출"""
        try:
            # 컨테이너 생성 (실행하지 않음)
            container = self.client.containers.create(image_name)
            
            # 전체 파일시스템 추출
            tar_stream, _ = container.get_archive('/')
            all_files = self._extract_all_code_files(tar_stream)
            
            container.remove()
            
            # AI가 중요한 파일 식별
            important_files = self._identify_important_files(all_files)
            
            return important_files
            
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_all_code_files(self, tar_stream):
        """TAR 스트림에서 모든 코드 파일 추출"""
        code_extensions = ['.py', '.yaml', '.yml', '.json', '.txt', '.cfg', '.conf']
        files = {}
        
        with tempfile.NamedTemporaryFile() as tmp:
            for chunk in tar_stream:
                tmp.write(chunk)
            tmp.flush()
            
            with tarfile.open(tmp.name, 'r') as tar:
                for member in tar.getmembers():
                    if member.isfile() and any(member.name.endswith(ext) for ext in code_extensions):
                        # 시스템 파일 제외
                        if self._is_system_file(member.name):
                            continue
                            
                        f = tar.extractfile(member)
                        if f:
                            try:
                                content = f.read().decode('utf-8')
                                if len(content) < 100000:  # 100KB 미만 파일만
                                    files[member.name] = content
                            except:
                                continue
                                
        return files
    
    def _is_system_file(self, filepath):
        """시스템 파일인지 확인"""
        system_paths = ['/usr/', '/lib/', '/bin/', '/sbin/', '/etc/passwd', '/etc/shadow']
        return any(filepath.startswith(path) for path in system_paths)
    
    def _identify_important_files(self, all_files):
        """AI가 학습 관련 중요 파일 식별"""
        if not all_files:
            return {}
            
        # 파일 목록을 AI에게 전달
        file_list = list(all_files.keys())[:50]  # 처음 50개만
        
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return self._fallback_file_selection(all_files)
        
        prompt = f"""
다음 파일 목록에서 딥러닝/머신러닝 학습과 관련된 중요한 파일들을 최대 10개 선택하세요:

{file_list}

다음 기준으로 선택하세요:
- 학습 스크립트 (train.py, main.py 등)
- 설정 파일 (config.py, .yaml 등)  
- 모델 정의 파일
- requirements.txt

JSON 배열 형태로만 응답하세요:
["파일경로1", "파일경로2", ...]
"""
        
        try:
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", 
                                   headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # JSON 파싱
            import json
            selected_files = json.loads(ai_response)
            
            return {path: all_files[path] for path in selected_files if path in all_files}
            
        except Exception as e:
            print(f"AI 파일 선택 실패: {e}")
            return self._fallback_file_selection(all_files)
    
    def _fallback_file_selection(self, all_files):
        """AI 실패 시 휴리스틱 기반 파일 선택"""
        important_patterns = [
            'train', 'main', 'run', 'config', 'model', 'requirements', 
            'setup', 'app', 'server', 'client'
        ]
        
        selected = {}
        for filepath, content in all_files.items():
            filename = filepath.split('/')[-1].lower()
            if any(pattern in filename for pattern in important_patterns):
                selected[filepath] = content
                if len(selected) >= 10:  # 최대 10개
                    break
                    
        return selected

class AICodeAnalyzer:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_url = "https://api.openai.com/v1/chat/completions"
    
    def analyze_code(self, files):
        """AI를 사용하여 코드 분석"""
        if not self.openai_api_key:
            return self._fallback_analysis(files)
        
        # 코드 파일들을 하나의 텍스트로 결합
        code_content = self._prepare_code_for_ai(files)
        
        # AI 분석 요청
        ai_result = self._call_openai_api(code_content)
        
        return ai_result if ai_result else self._fallback_analysis(files)
    
    def _prepare_code_for_ai(self, files):
        """AI 분석을 위한 코드 준비"""
        content_parts = []
        
        for path, content in files.items():
            if isinstance(content, str) and len(content) > 0:
                # 파일 경로와 내용을 명확히 구분
                content_parts.append(f"=== FILE: {path} ===\n{content[:5000]}\n")  # 파일당 5KB 제한
        
        return "\n".join(content_parts[:15])  # 최대 15개 파일
    
    def _is_code_file(self, filepath):
        """코드 파일인지 확인 (사용하지 않음 - 호환성 유지)"""
        return True
    
    def _call_openai_api(self, code_content):
        """OpenAI API 호출"""
        prompt = f"""
다음 딥러닝 프로젝트 코드를 분석하여 정확한 JSON 형태로 응답하세요.

코드:
{code_content}

다음 형태의 JSON만 응답하세요 (다른 텍스트 없이):
{{
  "model_type": "모델 종류 (protogcn, resnet, transformer, lstm, yolo, 등)",
  "framework": "프레임워크 (pytorch, tensorflow, 등)",
  "batch_size": 배치 크기 (숫자),
  "learning_rate": 학습률 (숫자),
  "epochs": 에폭 수 (숫자),
  "optimizer": "옵티마이저 (adam, sgd, 등)",
  "dataset": "데이터셋 이름",
  "num_classes": 클래스 수 (숫자),
  "input_shape": "입력 형태",
  "model_architecture": "모델 아키텍처 세부사항"
}}

코드에서 찾을 수 없는 값은 null로 설정하세요.
"""
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.openai_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # JSON 파싱 시도
            return json.loads(ai_response)
            
        except Exception as e:
            print(f"AI API 호출 실패: {e}")
            return None
    
    def _fallback_analysis(self, files):
        """AI 실패 시 기본 분석"""
        return {
            "model_type": "unknown",
            "framework": "unknown", 
            "batch_size": None,
            "learning_rate": None,
            "epochs": None,
            "optimizer": None,
            "dataset": None,
            "num_classes": None,
            "input_shape": None,
            "model_architecture": None
        }

class ConfigParser:
    def to_json(self, ai_features):
        """AI 분석 결과를 표준 JSON 형태로 변환"""
        return {
            'model_info': {
                'type': ai_features.get('model_type', 'unknown'),
                'framework': ai_features.get('framework', 'unknown'),
                'architecture': ai_features.get('model_architecture')
            },
            'training_config': {
                'batch_size': ai_features.get('batch_size'),
                'learning_rate': ai_features.get('learning_rate'),
                'epochs': ai_features.get('epochs'),
                'optimizer': ai_features.get('optimizer')
            },
            'data_info': {
                'dataset': ai_features.get('dataset'),
                'input_shape': ai_features.get('input_shape'),
                'num_classes': ai_features.get('num_classes')
            }
        }

# 서비스 초기화
extractor = ImageExtractor()
analyzer = AICodeAnalyzer()
parser = ConfigParser()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/analyze', methods=['POST'])
def analyze_image():
    try:
        data = request.get_json()
        image_url = data.get('image_url')
        
        if not image_url:
            return jsonify({'error': 'image_url is required'}), 400
        
        # 1. 이미지에서 파일 추출
        files = extractor.extract_files(image_url)
        
        if 'error' in files:
            return jsonify({'error': files['error']}), 500
        
        # 2. AI로 코드 분석
        ai_features = analyzer.analyze_code(files)
        
        # 3. JSON 변환
        result = parser.to_json(ai_features)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
