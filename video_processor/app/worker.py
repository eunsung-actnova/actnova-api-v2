import json
import pika
import os
import time
import logging
from typing import Dict, Any
from datetime import datetime

from app.video_downloader import VercelVideoDownloader
from app.videoframe_handler import VideoFrameHandler, NaiveVideoFrameCurator

from actverse_common.logging import (
    setup_logger, 
    log_event_received, 
    log_event_processed, 
    log_event_failed
)
from actverse_common.events import (
    EVENT_VIDEO_DOWNLOAD_REQUESTED,
    EVENT_VIDEO_DOWNLOADED,
    EVENT_FRAMES_EXTRACTION_REQUESTED,
    EVENT_FRAMES_EXTRACTED
)
from actverse_common.messaging import (
    publish_event, 
    get_rabbitmq_connection
)

# 구독할 이벤트
SUBSCRIBE_EVENTS = [
    EVENT_VIDEO_DOWNLOAD_REQUESTED,  # 비디오 다운로드 요청 이벤트 구독
    EVENT_FRAMES_EXTRACTION_REQUESTED  # 프레임 추출 요청 이벤트 구독
]

# 로깅 설정                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
logger = setup_logger(service_name="video_processor")


def process_video_download_request(data: Dict[str, Any]):
    """비디오 다운로드 요청 이벤트 처리"""
    task_id = data.get("task_id")
    original_video_path = data.get("video_path")
    download_path = data.get("download_path", f"/app/data/videos/{task_id}")
    
    try:
        vercel_downloader = VercelVideoDownloader()
        downloaded_file_name = vercel_downloader.download(original_video_path, download_path)
        
        
        # 메타데이터 저장
        metadata = {
            "task_id": task_id,
            "original_video_path": original_video_path,
            "downloaded_video_path": downloaded_file_name,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
        
        # 다운로드 완료되면 이벤트 발행
        publish_event(logger, EVENT_VIDEO_DOWNLOADED, {
            "task_id": task_id,
            "downloaded_video_path": downloaded_file_name,
            "original_video_path": original_video_path,
            "status": "completed"
        })
        
        return True
    except Exception as e:
        logger.error(f"비디오 다운로드 처리 중 오류: {str(e)}")
        return False


def process_frames_extraction_request(data: Dict[str, Any]):
    """프레임 추출 요청 이벤트 처리"""
    logger.info(f"프레임 추출 요청 이벤트 처리: {data}")
    
    task_id = data.get("task_id")
    downloaded_video_path = data.get("downloaded_video_path")
    num_frames = data.get("num_frames", 30)
    
    try:
        # frame 추출 경로도 actverse-api에서 지정한 값으로 설정
        frames_path = f"/app/data/frames/{task_id}"
        video_frame_handler = VideoFrameHandler()
        frame_curator = NaiveVideoFrameCurator(num_frames)

        # 프레임 추출
        frames = video_frame_handler.extract(downloaded_video_path)
        logger.info(f"프레임 추출 중: {downloaded_video_path} -> {frames_path}, 요청 프레임 수: {num_frames}")

        # video frame curation 적용
        curated_frames = video_frame_handler.curate(frames, frame_curator)

        # 프레임 저장
        video_frame_handler.save(curated_frames, frames_path)
        
        
        
        # 프레임 추출 완료 이벤트 발행
        publish_event(logger, EVENT_FRAMES_EXTRACTED, {
            "task_id": task_id,
            "frames_path": frames_path,
            "num_frames": num_frames,
            "status": "completed"
        })
        
        return True
    except Exception as e:
        logger.error(f"프레임 추출 처리 중 오류: {str(e)}")
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
        if event_type == EVENT_VIDEO_DOWNLOAD_REQUESTED:
            success = process_video_download_request(data)
        elif event_type == EVENT_FRAMES_EXTRACTION_REQUESTED:
            success = process_frames_extraction_request(data)
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
            ch.basic_ack(delivery_tag=method.delivery_tag)  # 실패해도 메시지 처리 완료로 간주
            
    except Exception as e:
        # 예외 발생 로깅
        log_event_failed(logger, event_type, data.get("task_id", "unknown"), str(e))
        logger.error(f"이벤트 처리 중 오류 발생: {str(e)}")
        ch.basic_ack(delivery_tag=method.delivery_tag)  # 예외 발생해도 메시지 처리 완료로 간주


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
        
        # 비디오 프로세서 큐 선언
        queue_name = 'video_processor'
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
