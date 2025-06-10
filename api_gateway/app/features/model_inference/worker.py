import json
import pika
import os
import time
from typing import Dict, Any
from glob import glob
from app.features.model_inference.inference import YOLOv8KeypointInference
from app.features.model_inference.analysis_notebook import generate_analysis_script
from actverse_common.logging import (
    setup_logger, 
    log_event_received, 
    log_event_processed, 
    log_event_failed, 
)
from actverse_common.events import (
    EVENT_MODEL_INFERENCE_REQUESTED, 
    EVENT_MODEL_INFERENCE_COMPLETED
)
from actverse_common.messaging import publish_event, get_rabbitmq_connection

# 로거 설정
logger = setup_logger(service_name="model_inference")

# 구독할 이벤트
SUBSCRIBE_EVENTS = [EVENT_MODEL_INFERENCE_REQUESTED]


def process_inference_requested(data: Dict[str, Any]):
    """추론 요청 이벤트 처리"""
    task_id = data.get("task_id")
    user_id = data.get("user_id")
    ## TODO: DB에서 추론 영상 경로 가져오기
    
    try:
        # 모델 추론 로직
        download_path = f'inference_results/{task_id}'
        # TODO: 비디오 이름 식별 필요
        video_file = glob(f'{os.getenv("DATA_STORAGE_PATH")}/videos/{task_id}/*.mp4')[0]

        inference = YOLOv8KeypointInference(download_path)

        inference(video_file, task_id)
        
        logger.info(f"모델 추론 중: {task_id}")
        
        # 추론 완료 이벤트 발행
        publish_event(logger, EVENT_MODEL_INFERENCE_COMPLETED, {
            "task_id": task_id,
            "user_id": user_id,
            "status": "completed"
        })
        
        return True
    except Exception as e:
        logger.error(f"모델 추론 중 오류: {str(e)}")
        return False
    
def process_inference_result(data: Dict[str, Any]):
    task_id = data.get("task_id")
    user_id = data.get("user_id")


    # generate notebook
    # user_url은  dropbox 업로드 후 받아오는 url?
    user_url = ''
    generate_analysis_script(task_id, user_url) 
    # generate overlaid video




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
        
        if event_type == EVENT_MODEL_INFERENCE_REQUESTED:
            success = process_inference_requested(data)
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
        
        # 모델 추론 큐 선언
        queue_name = 'model_inference'
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