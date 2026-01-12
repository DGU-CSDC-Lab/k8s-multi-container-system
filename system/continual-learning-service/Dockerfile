FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# 데이터베이스 볼륨 마운트 포인트
VOLUME ["/app/data"]

EXPOSE 5002

CMD ["python", "app.py"]
