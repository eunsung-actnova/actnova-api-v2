FROM python:3.9-slim

WORKDIR /app

# 공통 라이브러리 설치
COPY common /app/common
RUN pip install -e /app/common

# 서비스 특정 종속성 설치
COPY ./model_deployer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 서비스 코드 복사
COPY ./model_deployer/app /app/app
CMD ["python", "-m", "app.main"]