import os
import sys
import logging
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    from app.worker import monitor_labeling_tasks
    
    logger.info("라벨링 모니터 워커 시작")
    
    # 주기적으로 모니터링 함수 실행
    try:
        while True:
            monitor_labeling_tasks()
            time.sleep(60)  # 60초마다 모니터링
    except KeyboardInterrupt:
        logger.info("라벨링 모니터 종료")
