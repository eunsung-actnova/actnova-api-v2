import json
import os
from typing import Dict, Any

from actverse_common.logging import (
    setup_logger, 
    log_event_received, 
    log_event_processed, 
    log_event_failed
)
from actverse_common.messaging import (
    publish_event, 
    get_rabbitmq_connection
)
from actverse_common.event_workflow import EVENT_WORKFLOW

# 로깅 설정
logger = setup_logger(service_name="event_worker")


def process_event(data: Dict[str, Any], event_type: str) -> bool:
    """이벤트 처리 및 다음 이벤트 발행"""
    logger.info(f"이벤트 처리: {event_type}, 데이터: {data}")
    
    # 필수 필드 검증
    task_id = data.get("task_id")
    user_id = data.get("user_id")
    
    if not task_id or not user_id:
        logger.error(f"필수 필드 누락: task_id={task_id}, user_id={user_id}")
        return False
    
    # 이벤트 워크플로우에서 다음 이벤트 정보 가져오기
    next_event = EVENT_WORKFLOW.get(event_type)
    if not next_event:
        logger.info(f"이벤트 {event_type}에 대한 워크플로우 정의가 없습니다.")
        return True  # 워크플로우 정의가 없는 이벤트는 성공으로 처리
    
    try:
        # 다음 이벤트 발행 (기존 데이터 그대로 전달)
        # publish_event(logger, next_event, data)
        logger.info(f"다음 이벤트 발행: {next_event}, 데이터: {data}")
        
        return True
    except Exception as e:
        logger.error(f"이벤트 처리 중 오류: {str(e)}")
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
        
        # 이벤트 처리
        success = process_event(data, event_type)
        
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
        log_event_failed(logger, event_type, data.get("task_id", "unknown"), str(e))
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
        
        # 워크플로우 워커 큐 선언
        queue_name = 'workflow_worker'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # 워크플로우에 정의된 모든 이벤트에 대해 큐 바인딩
        for event_type in EVENT_WORKFLOW.keys():
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
        
        logger.info(f"이벤트 구독 중: {', '.join(EVENT_WORKFLOW.keys())}")
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


if __name__ == "__main__":
    start_worker()