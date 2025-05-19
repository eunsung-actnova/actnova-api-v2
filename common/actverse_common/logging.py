import logging
import os
from .events import get_event_description

def setup_logger(service_name=None):
    """서비스 로거 설정
    
    Args:
        service_name: 서비스 이름 (로그에 표시됨)
    
    Returns:
        구성된 로거 인스턴스
    """
    # 로그 레벨 설정 (환경변수로 조정 가능)
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # 로그 포맷 설정
    log_format = '[%(asctime)s]'
    if service_name:
        log_format += f' [{service_name}]'
    log_format += ' [%(levelname)s] %(message)s'
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.getLevelName(log_level),
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 로거 생성
    logger = logging.getLogger("app")
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logger


def log_event_received(logger, event_type, task_id="unknown"):
    """이벤트 수신 로깅"""
    event_desc = get_event_description(event_type)
    logger.info(f"[EVENT_RECEIVED] {event_type} ({event_desc}) | task_id: {task_id}")


def log_event_processed(logger, event_type, task_id="unknown"):
    """이벤트 처리 완료 로깅"""
    logger.info(f"[EVENT_PROCESSED] {event_type} | task_id: {task_id}")


def log_event_failed(logger, event_type, task_id="unknown", error=None):
    """이벤트 처리 실패 로깅"""
    error_msg = f" | error: {error}" if error else ""
    logger.error(f"[EVENT_FAILED] {event_type} | task_id: {task_id}{error_msg}")


def log_event_published(logger, event_type, task_id="unknown"):
    """이벤트 발행 로깅"""
    event_desc = get_event_description(event_type)
    logger.info(f"[EVENT_PUBLISHED] {event_type} ({event_desc}) | task_id: {task_id}")