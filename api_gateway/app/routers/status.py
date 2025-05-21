from fastapi import APIRouter, HTTPException, Path
from app.services.task_tracker import TaskTracker

router = APIRouter(
    prefix="/status",
    tags=["status"],
    responses={
        404: {"description": "task_id 찾을 수 없음"},
        500: {"description": "서버 오류"}
    }
)

@router.get("/{task_id}")
async def get_task_status(task_id: str = Path(...)):
    """ActVerse 프로세스 진행율 요청"""
    try:
        task_tracker = TaskTracker.get_instance()
        status = task_tracker.get_task_status(task_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"태스크 ID {task_id}를 찾을 수 없습니다."
            )
            
        # 단계별 한글 이름 매핑
        step_names = {
            "video_download": "비디오 다운로드",
            "frame_extraction": "프레임 추출",
            "labeling": "라벨링",
            "model_training": "모델 학습",
            "model_deployment": "모델 배포",
            "inference": "모델 추론"
        }
        
        # 단계별 상태 한글 매핑
        status_names = {
            "pending": "대기중",
            "processing": "처리중",
            "completed": "완료",
            "failed": "실패"
        }
        
        # 응답 데이터 구성
        response = {
            "task_id": status["task_id"],
            "user_id": status["user_id"],
            "status": status["status"],
            "created_at": status["created_at"],
            "steps": {}
        }
        
        # 단계별 상태 정보 추가
        for step_name, step_info in status["steps"].items():
            response["steps"][step_names.get(step_name, step_name)] = {
                "status": status_names.get(step_info["status"], step_info["status"]),
                "started_at": step_info["started_at"],
                "finished_at": step_info["finished_at"]
            }
            
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"상태 조회 실패: {str(e)}"
        )