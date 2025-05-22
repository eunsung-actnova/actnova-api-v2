# NVIDIA 공식 TensorRT 컨테이너(파이썬 포함)
FROM nvcr.io/nvidia/tensorrt:24.03-py3

ENV GITHUB_TOKEN=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

WORKDIR /app

# 공통 라이브러리 복사 및 설치 (필요시)
COPY common /app/common
# COPY ../common /app/common
RUN pip install -e /app/common

RUN apt update && apt install -y \
    git \
    ffmpeg \
    libsm6 libxext6 libx264-dev libx265-dev libvpx-dev \
    libmp3lame-dev libopus-dev libvorbis-dev libtheora-dev \
    python3-venv ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*



# 서비스 종속성 설치
COPY ./model_deployer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
    

# 서비스 코드 복사
COPY ./model_deployer/app /app/app
COPY . /app


CMD ["python", "-m", "app.main"]