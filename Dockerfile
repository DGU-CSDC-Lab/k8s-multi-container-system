FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies + python3.8
RUN apt-get update && apt-get install -y \
    python3.8 python3.8-dev python3-pip \
    ffmpeg libsm6 libxext6 libgl1-mesa-glx \
    git curl unzip nano \
    && apt-get clean

# Set python & pip symlinks
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch 1.11.0 + torchvision + torchaudio for CUDA 11.3
RUN pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 torchaudio==0.11.0 \
    -f https://download.pytorch.org/whl/torch_stable.html

# Install mmcv-full (precompiled for torch 1.11.0 + cu113)
RUN pip install mmcv-full==1.5.0 -f https://download.openmmlab.com/mmcv/dist/cu113/torch1.11.0/index.html

# Copy requirements and install remaining packages
COPY requirements.txt /workspace/requirements.txt
WORKDIR /workspace
RUN pip install -r requirements.txt

CMD ["/bin/bash"]
