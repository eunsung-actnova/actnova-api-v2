import json
import threading
import time
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.entities import Task, TaskStep, Base
from actverse_common.logging import setup_logger
from actverse_common.events import (EVENT_VIDEO_DOWNLOAD_REQUESTED, EVENT_VIDEO_DOWNLOADED,
                               EVENT_FRAMES_EXTRACTION_REQUESTED, EVENT_FRAMES_EXTRACTED,
                               EVENT_LABELING_REQUESTED, EVENT_LABELING_COMPLETED,
                               EVENT_MODEL_TRAINING_REQUESTED, EVENT_MODEL_TRAINING_COMPLETED,
                               EVENT_MODEL_DEPLOYMENT_REQUESTED, EVENT_MODEL_DEPLOYMENT_COMPLETED,
                               EVENT_MODEL_INFERENCE_REQUESTED, EVENT_MODEL_INFERENCE_COMPLETED)
# 공유 메시징 라이브러리 대신 직접 pika 사용
import pika
import uuid
import datetime

# 단계별 예상 소요 시간(초)
STEP_DURATIONS = {
    "video_download": 60,
    "frame_extraction": 120,
    "labeling": 300,
    "model_training": 600,
    "model_deployment": 120,
    "inference": 30
}

# 이벤트와 단계 매핑
EVENT_TO_STEP = {
    EVENT_VIDEO_DOWNLOAD_REQUESTED: "video_download",
    EVENT_VIDEO_DOWNLOADED: "video_download",
    EVENT_FRAMES_EXTRACTION_REQUESTED: "frame_extraction",
    EVENT_FRAMES_EXTRACTED: "frame_extraction",
    EVENT_LABELING_REQUESTED: "labeling",
    EVENT_LABELING_COMPLETED: "labeling",
    EVENT_MODEL_TRAINING_REQUESTED: "model_training",
    EVENT_MODEL_TRAINING_COMPLETED: "model_training",
    EVENT_MODEL_DEPLOYMENT_REQUESTED: "model_deployment",
    EVENT_MODEL_DEPLOYMENT_COMPLETED: "model_deployment",
    EVENT_MODEL_INFERENCE_REQUESTED: "inference",
    EVENT_MODEL_INFERENCE_COMPLETED: "inference"
}

# 단계 완료 이벤트
COMPLETION_EVENTS = {
    EVENT_VIDEO_DOWNLOADED,
    EVENT_FRAMES_EXTRACTED,
    EVENT_LABELING_COMPLETED,
    EVENT_MODEL_TRAINING_COMPLETED,
    EVENT_MODEL_DEPLOYMENT_COMPLETED,
    EVENT_MODEL_INFERENCE_COMPLETED
}

# 워크플로우 정의 (순서)
WORKFLOW_STEPS = [
    "video_download",
    "frame_extraction",
    "labeling",
    "model_training",
    "model_deployment",
    "inference"
]

logger = setup_logger(service_name="task_tracker")


# TaskTracker 전용 RabbitMQ 연결 생성 함수
def create_task_tracker_connection(logger):
    """TaskTracker 전용 RabbitMQ 연결 생성 - 매번 새로운 연결 생성"""
    host = os.getenv("RABBITMQ_HOST", "localhost")
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    
    credentials = pika.PlainCredentials(user, password)
    
    max_retries = 5
    retry_delay = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"TaskTracker RabbitMQ 연결 시도... ({retry_count+1}/{max_retries})")
            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host, 
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                    client_properties={
                        'connection_name': f'task_tracker_{uuid.uuid4().hex[:8]}'
                    }
                )
            )
            
            logger.info(f"TaskTracker RabbitMQ 연결 성공: {host}")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"TaskTracker RabbitMQ 연결 실패: {str(e)}")
                raise
            logger.warning(f"연결 실패, 재시도... ({retry_count}/{max_retries})")
            time.sleep(retry_delay)


class TaskTracker:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, db_url=None):
        with cls._lock:
            if cls._instance is None:
                if db_url is None:
                    db_url = os.getenv("DATABASE_URL", "postgresql://actverse:actverse@postgres:5432/actverse")
                cls._instance = TaskTracker(db_url)
            return cls._instance
    
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.running = False
        self._consumer_thread = None
    
    def create_tables(self):
        Base.metadata.create_all(self.engine)
    
    def _get_producer_channel(self):
        """메시지 발행용 채널 가져오기 - 매번 새 연결 생성"""
        try:
            # 항상 새로운 연결과 채널 생성 - 전용 함수 사용
            connection = create_task_tracker_connection(logger)
            channel = connection.channel()
            
            # 교환기 선언
            channel.exchange_declare(
                exchange='events', 
                exchange_type='topic',
                durable=True
            )
            
            return connection, channel
        except Exception as e:
            logger.error(f"채널 생성 중 오류: {str(e)}")
            return None, None
    
    def start(self):
        """태스크 트래커 시작"""
        if self.running:
            return
        
        self.running = True
        
        # 이벤트 리스닝 스레드 시작
        if self._consumer_thread is None or not self._consumer_thread.is_alive():
            self._consumer_thread = threading.Thread(target=self._listen_events, daemon=True)
            self._consumer_thread.start()
            
        logger.info("태스크 트래커 시작됨")
    
    def _listen_events(self):
        """이벤트 리스닝 전용 스레드 (소비자)"""
        consumer_connection = None
        consumer_channel = None
        
        while self.running:
            try:
                # 이전 연결 정리
                if consumer_channel is not None and consumer_channel.is_open:
                    try:
                        consumer_channel.close()
                    except Exception:
                        pass
                
                if consumer_connection is not None and consumer_connection.is_open:
                    try:
                        consumer_connection.close()
                    except Exception:
                        pass
                
                # 새 소비자 전용 연결 생성
                consumer_connection = create_task_tracker_connection(logger)
                consumer_channel = consumer_connection.channel()
                
                # 이벤트 교환기 선언
                consumer_channel.exchange_declare(
                    exchange='events', 
                    exchange_type='topic',
                    durable=True
                )
                
                # workflow_worker 큐 구독 (event_worker와 동일한 큐 사용)
                queue_name = 'workflow_worker'
                consumer_channel.queue_declare(queue=queue_name, durable=True)
                
                # 워크플로우에 정의된 이벤트만 구독
                for event_type in EVENT_TO_STEP.keys():
                    consumer_channel.queue_bind(
                        exchange='events',
                        queue=queue_name,
                        routing_key=event_type
                    )
                
                def callback(ch, method, properties, body):
                    try:
                        message = json.loads(body)
                        self._process_event(message)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error(f"이벤트 처리 중 오류: {str(e)}")
                        ch.basic_nack(
                            delivery_tag=method.delivery_tag, 
                            requeue=False
                        )
                
                # 한 번에 하나의 메시지만 처리
                consumer_channel.basic_qos(prefetch_count=1)
                
                consumer_channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=callback
                )
                
                logger.info("이벤트 리스닝 시작")
                consumer_channel.start_consuming()
                
            except Exception as e:
                logger.error(f"이벤트 리스닝 중 오류: {str(e)}")
                # 연결 객체 정리
                if consumer_channel is not None:
                    try:
                        consumer_channel.close()
                    except Exception:
                        pass
                
                if consumer_connection is not None:
                    try:
                        consumer_connection.close()
                    except Exception:
                        pass
                
                consumer_channel = None
                consumer_connection = None
                time.sleep(5)  # 오류 발생 시 5초 후 재시도
    
    def publish_task_event(self, event_type, task_id, data=None):
        """태스크 이벤트 발행"""
        if data is None:
            data = {}
        
        data['task_id'] = task_id
        
        connection = None
        try:
            # 매번 새 연결과 채널 사용
            connection, channel = self._get_producer_channel()
            if channel is None:
                logger.error(f"채널을 생성할 수 없어 이벤트를 발행할 수 없습니다: {event_type}")
                return
            
            # 메시지 작성
            message = {
                "event_type": event_type,
                "data": data,
                "timestamp": int(time.time()),
                "message_id": str(uuid.uuid4())
            }
            
            # 발행
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
            
            logger.info(f"태스크 이벤트 발행: {event_type}, task_id: {task_id}")
        except Exception as e:
            logger.error(f"이벤트 발행 중 오류: {str(e)}")
        finally:
            # 사용 후 반드시 연결 종료
            if connection is not None:
                try:
                    connection.close()
                except Exception as e:
                    logger.error(f"연결 종료 중 오류: {str(e)}")
    
    def _process_event(self, message):
        """이벤트 처리 및 태스크 상태 업데이트"""
        event_type = message.get("event_type")
        data = message.get("data", {})
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        
        if not task_id or not user_id:
            return
            
        # 이벤트에 해당하는 단계 확인
        step = EVENT_TO_STEP.get(event_type)
        if not step:
            return
            
        with self.Session() as session:
            # 태스크 정보 조회
            task = session.query(Task).filter(Task.id == task_id).first()
            
            # 신규 태스크면 생성
            if not task:
                task = Task(id=task_id, user_id=user_id, status="created")
                session.add(task)
                session.flush()  # ID 생성
            
            # 현재 단계 조회 또는 생성
            current_step = session.query(TaskStep).filter(
                TaskStep.task_id == task_id,
                TaskStep.step_name == step
            ).first()
            
            if not current_step:
                current_step = TaskStep(
                    task_id=task_id,
                    step_name=step,
                    status="processing",
                    started_at=datetime.datetime.utcnow()
                )
                session.add(current_step)
            
            # 완료 이벤트면 상태 업데이트
            if event_type in COMPLETION_EVENTS:
                current_step.status = "completed"
                current_step.finished_at = datetime.datetime.utcnow()
                
                # 다음 단계 계산
                current_idx = WORKFLOW_STEPS.index(step)
                if current_idx < len(WORKFLOW_STEPS) - 1:
                    task.status = "processing"
                else:
                    task.status = "completed"
            else:
                current_step.status = "processing"
                task.status = "processing"
            
            session.commit()

    def _update_progress_and_time(self, task):
        """진행도 및 남은 시간 계산"""
        if task.status == "completed":
            task.progress = 1.0
            task.estimated_time_remaining = 0
            return
            
        current_step = task.current_step
        step_idx = WORKFLOW_STEPS.index(current_step) if current_step in WORKFLOW_STEPS else 0
        
        # 현재까지 완료된 단계 가중치
        completed_weight = sum(STEP_DURATIONS[step] for step in WORKFLOW_STEPS[:step_idx])
        total_weight = sum(STEP_DURATIONS.values())
        
        # 현재 단계 진행도 (간단하게 50%로 가정)
        current_step_progress = 0.5
        current_step_weight = STEP_DURATIONS[current_step] * current_step_progress
        
        # 전체 진행도
        task.progress = (completed_weight + current_step_weight) / total_weight
        
        # 남은 시간 계산
        remaining_steps = WORKFLOW_STEPS[step_idx:]
        remaining_time = sum(STEP_DURATIONS[step] for step in remaining_steps)
        
        # 현재 단계의 남은 시간은 절반만
        remaining_time -= STEP_DURATIONS[current_step] * current_step_progress
        
        task.estimated_time_remaining = int(remaining_time)
        
    def get_task_status(self, task_id):
        """태스크 상태 조회"""
        with self.Session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return None
                
            # 단계별 상태 정보 조회
            steps = session.query(TaskStep).filter(
                TaskStep.task_id == task_id
            ).order_by(TaskStep.step_name).all()
            
            step_status = {}
            for step in steps:
                step_status[step.step_name] = {
                    "status": step.status,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "finished_at": step.finished_at.isoformat() if step.finished_at else None
                }
            
            return {
                "task_id": task.id,
                "user_id": task.user_id,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "steps": step_status
            }
