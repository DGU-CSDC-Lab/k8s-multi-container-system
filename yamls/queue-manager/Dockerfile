FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl && \
    curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.7.6/argo-linux-amd64.gz && \
    gunzip argo-linux-amd64.gz && \
    chmod +x argo-linux-amd64 && \
    mv argo-linux-amd64 /usr/local/bin/argo && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install requests redis

COPY queue_manager.py /app/queue_manager.py
WORKDIR /app

EXPOSE 8081
CMD ["python3", "queue_manager.py"]
