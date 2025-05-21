import json
import pika
import os
import time
import logging
import psycopg2
from typing import Dict, Any, List

from actverse_common.logging import (
    setup_logger, 
    log_event_received, 
    log_event_processed, 
    log_event_failed, 
    log_event_published
)
from actverse_common.events import (
    EVENT_LABELING_REQUESTED, 
    EVENT_LABELING_COMPLETED
)
from actverse_common.messaging import publish_event
from app.repository import PostgresLabelTaskRepository, LabelTask, LabellingStatus
from app.labelling_manager import SuperbLabellingManager

from dotenv import load_dotenv

load_dotenv()

# 로거 설정
logger = setup_logger(service_name="labeling_monitor")

# 구독할 이벤트
SUBSCRIBE_EVENTS = [EVENT_LABELING_REQUESTED]



# DB 연결 정보
DB_URL = os.getenv("DATABASE_URL")

label_task_repository = PostgresLabelTaskRepository(DB_URL)

def get_pending_labeling_tasks(label_task_repository: PostgresLabelTaskRepository) -> List[Dict[str, Any]]:
    """데이터베이스에서 진행 중인 라벨링 태스크 조회"""
    try:
        tasks: LabelTask = label_task_repository.get_label_tasks_by_status(LabellingStatus.INPROGRESS.value)
        return tasks
    except Exception as e:
        logger.error(f"라벨링 태스크 조회 중 오류: {str(e)}")
        

def check_task_completion(task: Dict[str, Any], labelling_manager: SuperbLabellingManager) -> bool:
    """태스크 완료 여부 확인"""
    labeling_status = labelling_manager.get_labelling_status(task.task_id)
    
    return labeling_status


def update_task_status(task_id: str, new_status: str, label_task_repository: PostgresLabelTaskRepository):
    """태스크 상태 업데이트"""
    label_task_repository.update_label_task_status(task_id, new_status)


def download_labels(task_id: str, 
                    save_dir: str,
                    labelling_manager: SuperbLabellingManager) -> str:
    labelling_manager.download_labels(task_id, save_dir)
    


# def process_labeling_requested(data: Dict[str, Any], label_task_repository: PostgresLabelTaskRepository):
#     """라벨링 생성 이벤트 처리"""
#     task_id = data.get("task_id")
#     user_id = data.get("user_id")
#     frames_path = data.get("frames_path")

#     try:
#         # 라벨링 모니터링 로직
#         logger.info(f"라벨링 모니터링 중: {frames_path}")
#         publish_event(logger, EVENT_LABELING_COMPLETED, {
#             "task_id": task_id,
#             "user_id": user_id,
#             "status": "completed",
#             "data_path": f"/data/labels/{task_id}"
#         })
        
#         return True
#     except Exception as e:
#         logger.error(f"라벨링 모니터링 중 오류: {str(e)}")
#         return False




def monitor_labeling_tasks(label_task_repository: PostgresLabelTaskRepository, labelling_manager: SuperbLabellingManager):
    """라벨링 태스크 모니터링 및 완료 시 학습 트리거"""
    try:
        # 진행 중인 라벨링 태스크 조회
        tasks = get_pending_labeling_tasks(label_task_repository)
        
        for task in tasks:
            task_id = task.task_id
            user_id = task.user_id
            if check_task_completion(task, labelling_manager).status == LabellingStatus.COMPLETE:
                logger.info(f"라벨링 태스크 완료 감지: {task_id}")
                
                download_labels(task_id=task_id, 
                                save_dir=f'{os.getenv("DATA_STORAGE_PATH")}',
                                labelling_manager=labelling_manager)
                # 상태 업데이트
                update_task_status(task_id, LabellingStatus.COMPLETE.value, label_task_repository)
                
                # 라벨링 완료 이벤트 발행
                publish_event(logger, EVENT_LABELING_COMPLETED, {
                    "task_id": task_id,
                    "user_id": user_id,
                    "status": "completed",
                    "label_path": f"{os.getenv('DATA_STORAGE_PATH')}/labels/{task_id}"
                })
    except Exception as e:
        logger.error(f"라벨링 모니터링 중 오류 발생: {str(e)}")


# def callback(ch, method, properties, body):
#     """메시지 큐 콜백 함수"""
#     try:
#         message = json.loads(body)
#         event_type = message.get("event_type")
#         data = message.get("data", {})
#         task_id = data.get("task_id", "unknown")
        
#         # 이벤트 수신 로깅
#         log_event_received(logger, event_type, task_id)
        
#         success = False
    
    #     if event_type == EVENT_LABELING_REQUESTED:
    #         success = process_labeling_requested(data, label_task_repository)
    #     else:
    #         logger.warning(f"처리할 수 없는 이벤트 타입: {event_type}")
    #         success = True
        
    #     if success:
    #         log_event_processed(logger, event_type, task_id)
    #         ch.basic_ack(delivery_tag=method.delivery_tag)
    #     else:
    #         log_event_failed(logger, event_type, task_id)
    #         ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        task_id = "unknown"
        if 'data' in locals() and isinstance(data, dict):
            task_id = data.get("task_id", "unknown")
        log_event_failed(logger, event_type if 'event_type' in locals() else "unknown", 
                         task_id, str(e))
        logger.error(f"이벤트 처리 중 오류 발생: {str(e)}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
