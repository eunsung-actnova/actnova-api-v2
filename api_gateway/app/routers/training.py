from fastapi import APIRouter, HTTPException, Path
from app.schemas.task import TrainingCreate, TaskResponse
import uuid

from actverse_common.events import EVENT_TRAINING_REQUESTED
from actverse_common.messaging import publish_event
from actverse_common.logging import setup_logger

logger = setup_logger(service_name="api_gateway-training")

router = APIRouter(
    prefix="/training",
    tags=["training"],
    responses={
        400: {"description": "잘못된 데이터 경로"},
        422: {"description": "잘못된 학습 설정"},
        500: {"description": "학습 실패"}
    }
)


@router.post("/", response_model=TaskResponse)
async def train_model(data: TrainingCreate):
    """모델 학습 요청"""
    try:
        # 고유 태스크 ID 생성
        task_id = str(uuid.uuid4())
        
        # 모델 학습 요청 이벤트 발행
        event_data = {
            "task_id": task_id,
            "data_path": data.data_path,
            "mode_train_info": data.mode_train_info
        }
        # publish_event(logger, EVENT_TRAINING_REQUESTED, event_data)
        
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"모델 학습 요청 실패: {str(e)}"
        )


@router.get("/{task_id}")
async def get_training_status(task_id: str = Path(...)):
    """모델 학습 태스크 상태 요청"""
    try:
        # 실제 구현에서는 데이터베이스에서 상태 조회
        status = {
            "task_id": task_id,
            "status": "training",
            "current_epoch": 5,
            "total_epochs": 10,
            "progress": 0.5
        }
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"학습 상태 조회 실패: {str(e)}"
        )
