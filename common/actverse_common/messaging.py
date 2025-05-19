import json
import pika
import os
import time
import uuid
from typing import Dict, Any

# 싱글톤 연결 관리 클래스
class RabbitMQManager:
    _instance = None
    _connection = None
    _logger = None
    
    @classmethod
    def get_instance(cls, logger=None):
        if cls._instance is None:
            cls._instance = RabbitMQManager()
            cls._logger = logger
        return cls._instance
    
    def get_connection(self, max_retries=5, retry_delay=5):
        """연결 객체 가져오기 (없으면 생성)"""
        if self._connection is None or self._connection.is_closed:
            self._connection = self._create_connection(max_retries, retry_delay)
        return self._connection
    
    def _create_connection(self, max_retries=5, retry_delay=5):
        """RabbitMQ 연결 생성"""
        host = os.getenv("RABBITMQ_HOST", "localhost")
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")
        
        credentials = pika.PlainCredentials(user, password)
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                if self._logger:
                    self._logger.info(f"RabbitMQ 연결 시도... ({retry_count+1}/{max_retries})")
                
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=host, 
                        credentials=credentials,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                )
                
                if self._logger:
                    self._logger.info(f"RabbitMQ 연결 성공: {host}")
                return connection
            except pika.exceptions.AMQPConnectionError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    if self._logger:
                        self._logger.error(f"RabbitMQ 연결 실패: {str(e)}")
                    raise
                if self._logger:
                    self._logger.warning(f"연결 실패, 재시도... ({retry_count}/{max_retries})")
                time.sleep(retry_delay)

# 유틸리티 함수들
def get_rabbitmq_connection(logger=None, max_retries=5, retry_delay=5):
    """RabbitMQ 연결 가져오기 (연결 풀링 사용)"""
    manager = RabbitMQManager.get_instance(logger)
    return manager.get_connection(max_retries, retry_delay)

def publish_event(logger, event_type: str, data: Dict[str, Any]):
    """이벤트 발행"""
    from actverse_common.logging import log_event_published
    
    task_id = data.get("task_id", "unknown")
    
    try:
        # 공유 연결 사용
        connection = get_rabbitmq_connection(logger)
        channel = connection.channel()
        
        # 교환기 선언
        channel.exchange_declare(
            exchange='events', 
            exchange_type='topic',
            durable=True
        )
        
        # 메시지 작성
        message = {
            "event_type": event_type,
            "data": data,
            "timestamp": int(time.time()),
            "message_id": str(uuid.uuid4())
        }
        
        # 이벤트 발행
        channel.basic_publish(
            exchange='events',
            routing_key=event_type,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                message_id=message["message_id"]
            )
        )
        
        # 로깅
        log_event_published(logger, event_type, task_id)
        
        # 채널만 닫고 연결은 유지
        channel.close()
    except Exception as e:
        logger.error(f"이벤트 발행 중 오류: {str(e)}")
        raise
