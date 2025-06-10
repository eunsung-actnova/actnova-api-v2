from fastapi import APIRouter, HTTPException
import uuid

from app.schemas.video import VideoDownload, VideoExtractFrames, VideoUpload
from app.schemas.task import TaskResponse

from actverse_common.messaging import publish_event
from actverse_common.events import (
    EVENT_VIDEO_DOWNLOAD_REQUESTED,
    EVENT_FRAMES_EXTRACTION_REQUESTED,
    EVENT_VIDEO_UPLOAD_REQUESTED
)
from actverse_common.logging import setup_logger

logger = setup_logger(service_name="api_gateway-video")

router = APIRouter(
    prefix="/video",
    tags=["video"],
    responses={
        400: {"description": "잘못된 요청 데이터"},
        404: {"description": "파일 찾을 수 없음"},
        500: {"description": "서버 오류"}
    }
)


@router.post("/download", response_model=TaskResponse)
async def download_video(data: VideoDownload):
    """비디오 다운로드 요청"""
    try:
        # 고유 태스크 ID 생성
        task_id = str(uuid.uuid4())
        
        # 비디오 다운로드 이벤트 발행
        event_data = {
            "task_id": task_id,
            "file_path": data.file_path,
            "download_path": data.download_path
        }
        # publish_event(logger, EVENT_VIDEO_DOWNLOAD_REQUESTED, event_data)
        
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 다운로드 요청 실패: {str(e)}")


@router.post("/extract-frames", response_model=TaskResponse)
async def extract_frames(data: VideoExtractFrames):
    """비디오 프레임 추출 요청"""
    try:
        # 고유 태스크 ID 생성
        task_id = str(uuid.uuid4())
        
        # 프레임 추출 이벤트 발행
        event_data = {
            "task_id": task_id,
            "file_path": data.file_path,
            "num_frames": data.num_frames
        }
        # publish_event(logger, EVENT_FRAMES_EXTRACTION_REQUESTED, event_data)
        
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 프레임 추출 실패: {str(e)}")


@router.post("/upload", response_model=TaskResponse)
async def upload_video(data: VideoUpload):
    """비디오 업로드 요청"""
    try:
        # 고유 태스크 ID 생성
        task_id = str(uuid.uuid4())
        
        # 비디오 업로드 이벤트 발행
        event_data = {
            "task_id": task_id,
            "file_path": data.file_path,
            "upload_path": data.upload_path
        }
        # publish_event(logger, EVENT_VIDEO_UPLOAD_REQUESTED, event_data)
        
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 업로드 실패: {str(e)}")
