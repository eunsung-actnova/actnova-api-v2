FROM python:3.9-slim

WORKDIR /app

# 공통 라이브러리 설치
COPY ./common /common
RUN pip install -e /common

COPY ./labeling_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 서비스 코드 복사
COPY ./labeling_manager/app /app/app

CMD ["python", "-m", "app.main"]
