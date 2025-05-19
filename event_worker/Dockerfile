FROM python:3.9-slim

WORKDIR /app

# 공통 라이브러리 설치
COPY common /app/common
RUN pip install -e /app/common

COPY ./event_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY ./event_worker/app /app/app

# 워크플로우 워커 실행
CMD ["python", "-m", "app.worker"] 