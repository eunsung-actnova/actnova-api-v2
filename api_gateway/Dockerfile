FROM python:3.9-slim

WORKDIR /app

# 공통 라이브러리 설치
COPY ./common /app/common
RUN pip install -e /app/common
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 서비스 특정 종속성 설치
COPY ./api_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 서비스 코드 복사
COPY ./api_gateway/app /app/app

CMD ["python", "-m", "app.main"]