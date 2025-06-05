from .app import celery_app
from app.services import labeling_service
import logging

logger = logging.getLogger("labeling_monitor")

@celery_app.task
def monitor_labeling_status():
    """
    라벨링 플랫폼에서 라벨링 완료 여부를 주기적으로 확인하는 태스크.
    """
    try:
        # 실제 라벨링 상태 모니터링 로직 호출
        labeling_service.check_labeling_status()
        logger.info("라벨링 상태 모니터링 완료")
    except Exception as e:
        logger.error(f"라벨링 모니터링 실패: {e}")