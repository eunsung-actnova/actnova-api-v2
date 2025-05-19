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

# 로거 설정
logger = setup_logger(service_name="labeling_monitor")

# 구독할 이벤트
SUBSCRIBE_EVENTS = [EVENT_LABELING_REQUESTED]



# DB 연결 정보
DB_URL = os.getenv("DATABASE_URL", 
                  "postgresql://actverse:actverse@postgres:5432/actverse")



def get_pending_labeling_tasks() -> List[Dict[str, Any]]:
    """데이터베이스에서 진행 중인 라벨링 태스크 조회"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # 샘플 쿼리 - 실제로는 DB 스키마에 맞게 구현
        # cursor.execute("""
        #     SELECT task_id, status, progress 
        #     FROM labeling_tasks 
        #     WHERE status = 'IN_PROGRESS'
        # """)
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                "task_id": row[0],
                "status": row[1],
                "progress": row[2]
            })
        
        conn.close()
        return tasks
    except Exception as e:
        logger.error(f"라벨링 태스크 조회 중 오류: {str(e)}")
        # 실패 시 샘플 데이터 반환 (개발 목적)
        return [
            {"task_id": "task1", "status": "in_progress", "progress": 0.9},
            {"task_id": "task2", "status": "in_progress", "progress": 0.5}
        ]


def check_task_completion(task: Dict[str, Any]) -> bool:
    """태스크 완료 여부 확인"""
    # 실제 구현에서는 라벨링 서비스 API 호출 등을 통해 확인
    return task.get("progress", 0) >= 0.9  # 90% 이상이면 완료로 간주


def update_task_status(task_id: str, new_status: str):
    """태스크 상태 업데이트"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # 샘플 쿼리 - 실제로는 DB 스키마에 맞게 구현
        # cursor.execute("""
        #     UPDATE labeling_tasks 
        #     SET status = %s 
        #     WHERE task_id = %s
        # """, (new_status, task_id))
        
        conn.commit()
        conn.close()
        logger.info(f"태스크 상태 업데이트: {task_id} -> {new_status}")
    except Exception as e:
        logger.error(f"태스크 상태 업데이트 중 오류: {str(e)}")


def process_labeling_requested(data: Dict[str, Any]):
    """라벨링 생성 이벤트 처리"""
    task_id = data.get("task_id")
    frames_path = data.get("frames_path")
    
    try:
        # 라벨링 모니터링 로직
        logger.info(f"라벨링 모니터링 중: {frames_path}")
        
        # 실제 구현에서는 라벨링 완료를 감지한 후 이벤트 발행
        # 여기서는 예시로 바로 완료 이벤트 발행
        publish_event(logger, EVENT_LABELING_COMPLETED, {
            "task_id": task_id,
            "status": "completed",
            "data_path": f"/data/labels/{task_id}"
        })
        
        return True
    except Exception as e:
        logger.error(f"라벨링 모니터링 중 오류: {str(e)}")
        return False




def monitor_labeling_tasks():
    """라벨링 태스크 모니터링 및 완료 시 학습 트리거"""
    try:
        # 진행 중인 라벨링 태스크 조회
        tasks = get_pending_labeling_tasks()
        
        for task in tasks:
            task_id = task.get("task_id")
            if check_task_completion(task):
                logger.info(f"라벨링 태스크 완료 감지: {task_id}")
                
                # 상태 업데이트
                update_task_status(task_id, "completed")
                
                # 라벨링 완료 이벤트 발행
                publish_event(logger, EVENT_LABELING_COMPLETED, {
                    "task_id": task_id,
                    "status": "completed",
                    "label_path": f"/data/labels/{task_id}"
                })
    except Exception as e:
        logger.error(f"라벨링 모니터링 중 오류 발생: {str(e)}")


def callback(ch, method, properties, body):
    """메시지 큐 콜백 함수"""
    try:
        message = json.loads(body)
        event_type = message.get("event_type")
        data = message.get("data", {})
        task_id = data.get("task_id", "unknown")
        
        # 이벤트 수신 로깅
        log_event_received(logger, event_type, task_id)
        
        success = False
        
        if event_type == EVENT_LABELING_REQUESTED:
            success = process_labeling_requested(data)
        else:
            logger.warning(f"처리할 수 없는 이벤트 타입: {event_type}")
            success = True
        
        if success:
            log_event_processed(logger, event_type, task_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            log_event_failed(logger, event_type, task_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        task_id = "unknown"
        if 'data' in locals() and isinstance(data, dict):
            task_id = data.get("task_id", "unknown")
        log_event_failed(logger, event_type if 'event_type' in locals() else "unknown", 
                         task_id, str(e))
        logger.error(f"이벤트 처리 중 오류 발생: {str(e)}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
