import os
import sys
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    from app.worker import start_worker
    
    try:
        logger.info("모델 추론 워커 시작")
        start_worker()
    except Exception as e:
        logger.error(f"모델 추론 워커 실행 중 오류 발생: {str(e)}")
        # 오류 발생 시에도 docker-compose의 restart: always 설정으로 재시작됨
        sys.exit(1)