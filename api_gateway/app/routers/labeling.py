from typing_extensions import deprecated
from fastapi import APIRouter, HTTPException, Path
from app.models.schemas import LabelingCreate, TaskResponse
from actverse_common.events import EVENT_LABELING_REQUESTED
from actverse_common.messaging import publish_event
from actverse_common.logging import setup_logger

logger = setup_logger(service_name="api_gateway-labeling")

router = APIRouter(
    prefix="/labeling",
    tags=["labeling"],
    responses={
        400: {"description": "잘못된 폴더 경로"},
        404: {"description": "폴더 찾을 수 없음"},
        500: {"description": "라벨링 작업 실패"}
    }
)


@router.post("/", response_model=TaskResponse, deprecated=True)
async def create_labeling_task(data: LabelingCreate):
    """라벨링 요청"""
    try:
        # 라벨링 요청 이벤트 발행
        event_data = {
            "folder_path": data.folder_path,
            "task_id": data.task_id,
            "user_id": data.user_id
        }
        publish_event(logger, EVENT_LABELING_REQUESTED, event_data)
        
        return {"task_id": data.task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"라벨링 요청 실패: {str(e)}"
        )


@router.get("/{task_id}")
async def get_labeling_status(task_id: str = Path(...)):
    """라벨링 태스크 상태 요청"""
    try:
        # 실제 구현에서는 데이터베이스에서 상태 조회
        status = {
            "task_id": task_id,
            "status": "processing",
            "progress": 0.3,
        }
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"라벨링 상태 조회 실패: {str(e)}"
        )