import json
import pika
import os
import time
from typing import Dict, Any
from dotenv import load_dotenv

from app.labelling_manager import SuperbLabellingManager
from app.repository import LabelTaskRepository, LabelTask, LabellingStatus, PostgresLabelTaskRepository
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
from actverse_common.messaging import (
    get_rabbitmq_connection, 
    publish_event
)
# 로거 설정
logger = setup_logger(service_name="labeling_manager")
load_dotenv()

# 구독할 이벤트
SUBSCRIBE_EVENTS = [EVENT_LABELING_REQUESTED]

label_task_repository: LabelTaskRepository = PostgresLabelTaskRepository(os.getenv("DATABASE_URL"))

def process_frames_extracted(data: Dict[str, Any]):
    """프레임 추출 완료 이벤트 처리"""
    task_id = data.get("task_id")
    frames_path = data.get("frames_path")
    user_id = data.get("user_id")

    superb_labelling_manager = SuperbLabellingManager(
        project_name=os.getenv("LABELING_PROJECT_NAME"),
        team_name=os.getenv("LABELING_TEAM_NAME"),
        superbai_token=os.getenv("SUPERBAI_TOKEN")
    )

    logger.info(f'project name: {os.getenv("LABELING_PROJECT_NAME")}')
    logger.info(f'team name: {os.getenv("LABELING_TEAM_NAME")}')
    logger.info(f'superbai token: {os.getenv("SUPERBAI_TOKEN")}')
    

    # TODO: 테스트 설정
    superb_labelling_manager.upload_images(frames_path, task_id)
    # DB에 라벨 태스크 저장
    # TODO: 리포지토리 초기화 위치 지정.
    label_task_repository.save_label_task(LabelTask(user_id = user_id, task_id=task_id, status=LabellingStatus.INPROGRESS.value, label_url=f"{os.getenv('DATA_STORAGE_PATH')}/{task_id}/labels"))

    try:
        # 라벨링 작업 생성 로직
        logger.info(f"라벨링 작업 생성 중: {frames_path}")
        return True
    except Exception as e:
        logger.error(f"라벨링 작업 생성 중 오류: {str(e)}")
        return False

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
            success = process_frames_extracted(data)
        else:
            logger.warning(f"처리할 수 없는 이벤트 타입: {event_type}")
            success = True  # 모르는 이벤트는 성공으로 처리
        
        if success:
            # 이벤트 처리 성공 로깅
            log_event_processed(logger, event_type, task_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # 이벤트 처리 실패 로깅
            log_event_failed(logger, event_type, task_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        # 예외 발생 로깅
        task_id = "unknown"
        if 'data' in locals() and isinstance(data, dict):
            task_id = data.get("task_id", "unknown")
        log_event_failed(logger, event_type if 'event_type' in locals() else "unknown", 
                         task_id, str(e))
        logger.error(f"이벤트 처리 중 오류 발생: {str(e)}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    """워커 시작"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # 이벤트 교환기 선언
        channel.exchange_declare(
            exchange='events', 
            exchange_type='topic',
            durable=True
        )
        
        # 라벨링 매니저 큐 선언
        queue_name = 'labeling_manager'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # 관심 있는 이벤트에 대해 큐 바인딩
        for event_type in SUBSCRIBE_EVENTS:
            channel.queue_bind(
                exchange='events',
                queue=queue_name,
                routing_key=event_type
            )
        
        # 메시지 처리 설정
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback
        )
        
        logger.info(f"이벤트 구독 중: {', '.join(SUBSCRIBE_EVENTS)}")
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("워커 종료")
        if 'connection' in locals() and connection.is_open:
            connection.close()
    except Exception as e:
        logger.error(f"워커 시작 중 오류 발생: {str(e)}")
        if 'connection' in locals() and connection.is_open:
            connection.close()
        raise
