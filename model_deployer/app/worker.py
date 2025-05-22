import json
import pika
import os
import time
from typing import Dict, Any

from app.model_packaging import ONNXModelPackaging
from app.deployer import TritonModelDeployer

from actverse_common.logging import (
    setup_logger, 
    log_event_received, 
    log_event_processed, 
    log_event_failed, 
    log_event_published
)
from actverse_common.events import (
    EVENT_MODEL_DEPLOYMENT_REQUESTED,
    EVENT_MODEL_DEPLOYMENT_COMPLETED,
)
from actverse_common.messaging import publish_event, get_rabbitmq_connection

# 로거 설정
logger = setup_logger(service_name="model_deployer")

# 구독할 이벤트
SUBSCRIBE_EVENTS = [EVENT_MODEL_DEPLOYMENT_REQUESTED]

model_packaging = ONNXModelPackaging()
triton_model_deployer = TritonModelDeployer()

triton_url = os.getenv("TRITON_SERVER_URL")

def process_model_deployment_requested(data: Dict[str, Any]):
    """모델 배포 요청 이벤트 처리"""
    task_id = data.get("task_id")
    user_id = data.get("user_id")
    model_path = data.get("model_path")
    
    try:
        # 모델 배포 로직
        logger.info(f"모델 배포 중: {model_path}")
        

        # 모델 패키징
        model_packaging(task_id)
        # triton server에 모델 교체
        triton_model_deployer.request_model_update(triton_url=triton_url, 
                                                   task_id=task_id, 
                                                   action="load")

        # 모델 배포 완료 이벤트 발행
        publish_event(logger, EVENT_MODEL_DEPLOYMENT_COMPLETED, {
            "task_id": task_id,
            "user_id": user_id,
            "model_path": model_path,
            "deployment_id": f"deployment_{task_id}",
            "status": "deployed",
            "endpoint": f"/models/{task_id}/inference"
        })
        
        return True
    except Exception as e:
        logger.error(f"모델 배포 중 오류: {str(e)}")
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
        
        if event_type == EVENT_MODEL_DEPLOYMENT_REQUESTED:
            success = process_model_deployment_requested(data)
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
        
        # 모델 배포 큐 선언
        queue_name = 'model_deployer'
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
