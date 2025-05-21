import os
import sys
import logging
from dotenv import load_dotenv
from app.worker import start_worker

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # 환경 변수 로드
    load_dotenv()
    
    # 워커 시작
    start_worker()