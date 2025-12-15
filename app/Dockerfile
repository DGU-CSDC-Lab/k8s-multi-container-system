# Multi-stage build for React + FastAPI
FROM node:18-alpine as frontend

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM python:3.9-slim

# 필수 도구 설치
RUN apt-get update && apt-get install -y curl unzip \
 && curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.7.3/argo-linux-amd64.gz \
 && gunzip argo-linux-amd64.gz \
 && chmod +x argo-linux-amd64 \
 && mv argo-linux-amd64 /usr/local/bin/argo \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY --from=frontend /app/dist ./static

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
