from fastapi import APIRouter, HTTPException
from app.schemas.task import TaskCreate, TaskResponse
import uuid
import time

from app.celery.tasks import video_pipeline

import logging
logger = logging.getLogger(__name__)


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
        # publish_event(logger, EVENT_TASK_CREATED, task_data)

        video_pipeline(task_data)

        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"태스크 생성 실패: {str(e)}"
        )
