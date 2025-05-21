import os
import sys
import logging
from dotenv import load_dotenv
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
    from app.repository import PostgresLabelTaskRepository
    from app.labelling_manager import SuperbLabellingManager

    load_dotenv()
    postgres_label_task_repository = PostgresLabelTaskRepository(os.getenv("DATABASE_URL"))
    postgres_label_task_repository.create_tables()

    superb_labelling_manager = SuperbLabellingManager(
        project_name=os.getenv("LABELING_PROJECT_NAME"),
        team_name=os.getenv("LABELING_TEAM_NAME"),
        superbai_token=os.getenv("SUPERBAI_TOKEN")
    )

    logger.info("라벨링 모니터 워커 시작")
    
    # 주기적으로 모니터링 함수 실행
    try:
        while True:
            monitor_labeling_tasks(postgres_label_task_repository, superb_labelling_manager)
            time.sleep(60)  # 60초마다 모니터링
    except KeyboardInterrupt:
        logger.info("라벨링 모니터 종료")
