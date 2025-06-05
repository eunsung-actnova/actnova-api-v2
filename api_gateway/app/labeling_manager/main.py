import os
import sys
import logging
from dotenv import load_dotenv

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
    
    from app.worker import start_worker
    from app.repository import PostgresLabelTaskRepository

    db_url = os.getenv("DATABASE_URL")
    label_task_repository = PostgresLabelTaskRepository(db_url)
    label_task_repository.create_tables()

    logger.info("라벨링 매니저 워커 시작")
    start_worker()