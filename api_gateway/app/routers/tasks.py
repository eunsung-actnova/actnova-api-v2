from fastapi import APIRouter, HTTPException
from app.models.schemas import TaskCreate, TaskResponse
import uuid
import time

from actverse_common.logging import setup_logger

from actverse_common.messaging import publish_event
from actverse_common.events import (
    EVENT_TASK_CREATED,
    EVENT_VIDEO_DOWNLOAD_REQUESTED,
    EVENT_FRAMES_EXTRACTION_REQUESTED
)

logger = setup_logger(service_name="api_gateway-tasks")


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={
        400: {"description": "잘못된 요청 데이터"},
        401: {"description": "인증 실패"},
        500: {"description": "서버 오류"}
    }
)


@router.post("/", response_model=TaskResponse)
async def create_task(data: TaskCreate):
    """ActVerse 프로세스 요청"""
    try:
        # 고유 태스크 ID 생성
        task_id = str(uuid.uuid4())
        # TODO: 테스트 설정. task_id 고정에서 변환 필요
        # task_id = "f564be73-d028-431f-b433-c62dd8a5f18b"
        # 태스크 생성 이벤트 발행
        logger.info(f"Task created: {task_id}")
        
        # 태스크 데이터 생성
        task_data = {
            "task_id": task_id,
            "file_path": data.file_path,
            "user_id": data.user_id,
            "timestamp": int(time.time())
        }
        publish_event(logger, EVENT_TASK_CREATED, task_data)
        
        # 비디오 다운로드 요청 이벤트 발행
        download_data = {
            "task_id": task_id,
            "video_path": data.file_path,
            "user_id": data.user_id
        }
        publish_event(logger, EVENT_VIDEO_DOWNLOAD_REQUESTED, download_data)

        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"태스크 생성 실패: {str(e)}"
        )
