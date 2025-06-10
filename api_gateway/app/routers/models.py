from fastapi import APIRouter, HTTPException, Path
from app.schemas.task import InferenceCreate

import logging
logger = logging.getLogger(service_name="api_gateway-models")

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={
        400: {"description": "잘못된 데이터 경로"},
        404: {"description": "모델 찾을 수 없음"},
        422: {"description": "잘못된 추론 파라미터"},
        500: {"description": "추론 실패"}
    }
)


@router.get("/")
async def list_models():
    """배포 모델 리스트 조회"""
    try:
        # 실제 구현에서는 데이터베이스에서 모델 리스트 조회
        models = [
            {"model_id": "model1", "name": "YOLOv5", "version": "1.0"},
            {"model_id": "model2", "name": "YOLOv8", "version": "2.0"}
        ]
        return models
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"모델 리스트 조회 실패: {str(e)}"
        )


@router.post("/{task_id}/inference")
async def run_inference(
    task_id: str = Path(...),
    data: InferenceCreate = None
):
    """모델 추론 요청"""
    try:
        # 모델 추론 요청 이벤트 발행
        event_data = {
            "task_id": task_id,
            "data_path": data.data_path,
            "confidence": data.confidence,
            "iou": data.iou,
            "batch_size": data.batch_size,
            "frame_skip": data.frame_skip,
            "max_frames": data.max_frames
        }
        # publish_event(logger, EVENT_INFERENCE_REQUESTED, event_data)
        
        # 임시 결과 반환
        return {"results": [], "task_id": task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"모델 추론 요청 실패: {str(e)}"
        )
