FROM python:3.9-slim

# pandas 설치
RUN pip install --no-cache-dir pandas

# 코드 복사
COPY index.py /app/index.py

# 작업 디렉토리 지정 (선택)
WORKDIR /app

# 기본 명령 (Argo에서는 override 가능)
CMD ["python", "index.py"]