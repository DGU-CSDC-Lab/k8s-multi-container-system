FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.8 python3-pip git \
    ffmpeg libsm6 libxext6 libgl1-mesa-glx \
    wget curl \
    && apt-get clean

RUN pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 \
    -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install mmcv-full==1.5.0 \
    -f https://download.openmmlab.com/mmcv/dist/cu113/torch1.11.0/index.html

WORKDIR /workspace

# Copy requirements first for better caching
COPY requirements.txt setup.py README.md ./
RUN pip install -r requirements.txt

# Copy necessary directories
COPY configs/ ./configs/
COPY tools/ ./tools/
COPY protogcn/ ./protogcn/

RUN pip install -e .

ENV MASTER_ADDR=localhost
ENV MASTER_PORT=12357
ENV RANK=0
ENV WORLD_SIZE=1
ENV LOCAL_RANK=0
ENV CONFIG_FILE=configs/ntu60_xsub/bm.py
ENV ANN_FILE=data/nturgbd/ntu60_3danno.pkl
ENV WORK_DIR=./work_dirs/ntu60_xsub/bm

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["python3 tools/train.py $CONFIG_FILE --validate --test-last --test-best"]
