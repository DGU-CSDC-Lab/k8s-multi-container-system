FROM nvidia/cuda:11.3.1-runtime-ubuntu20.04

RUN apt-get update && apt-get install -y python3 python3-pip procps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY monitor.py /app/monitor.py
WORKDIR /app

EXPOSE 8080
CMD ["python3", "monitor.py"]
