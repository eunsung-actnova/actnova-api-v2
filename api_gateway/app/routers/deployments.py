from fastapi import APIRouter, HTTPException
from app.schemas.task import DeploymentCreate, TaskResponse

import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/deployments",
    tags=["deployments"],
    responses={
        400: {"description": "잘못된 모델 경로"},
        404: {"description": "모델 찾을 수 없음"},
        500: {"description": "배포 실패"}
    }
)


@router.post("/", response_model=TaskResponse)
async def deploy_model(data: DeploymentCreate):
    """모델 배포 요청"""
    try:
        # 모델 배포 요청 이벤트 발행
        event_data = {
            "task_id": data.task_id,
            "model_path": data.model_path
        }
        # publish_event(logger, EVENT_DEPLOYMENT_REQUESTED, event_data)
        
        return {"task_id": data.task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"모델 배포 요청 실패: {str(e)}"
        )
