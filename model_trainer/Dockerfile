FROM nvcr.io/nvidia/pytorch:24.03-py3

# TODO: dockerfile 테스트용 임시 설정
ENV GITHUB_TOKEN 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

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libx264-dev \
    libx265-dev \
    libvpx-dev \
    libmp3lame-dev \
    libopus-dev \
    libvorbis-dev \
    libtheora-dev \
    python3-venv \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 공통 라이브러리 설치
COPY common /app/common
RUN pip install -e /app/common

# 서비스 특정 종속성 설치
COPY ./model_trainer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install opencv-fixer && \
    python -c "from opencv_fixer import AutoFix; AutoFix()"

# 서비스 코드 복사
COPY ./model_trainer/app /app/app

CMD ["python", "-m", "app.main"]