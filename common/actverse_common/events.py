"""이벤트 타입 정의 모듈"""

# API Gateway 이벤트
EVENT_TASK_CREATED = "task.created"
EVENT_VIDEO_DOWNLOAD_REQUESTED = "video.download.requested"
EVENT_FRAMES_EXTRACTION_REQUESTED = "video.frames.extraction.requested"
EVENT_VIDEO_UPLOAD_REQUESTED = "video.upload.requested"
EVENT_LABELING_REQUESTED = "labeling.requested"
EVENT_TRAINING_REQUESTED = "training.requested"
EVENT_DEPLOYMENT_REQUESTED = "deployment.requested"
EVENT_INFERENCE_REQUESTED = "inference.requested"

# Video Processor 이벤트
EVENT_VIDEO_DOWNLOADED = "video.downloaded"
EVENT_FRAMES_EXTRACTED = "video.frames.extracted"

# Labeling Manager 이벤트
EVENT_LABELING_REQUESTED = "labeling.created"

# Labeling Monitor 이벤트
EVENT_LABELING_COMPLETED = "labeling.completed"

# Model Trainer 이벤트
EVENT_MODEL_TRAINING_REQUESTED = "model.training.requested"
EVENT_MODEL_TRAINING_COMPLETED = "model.training.completed"

# Model Deployer 이벤트
EVENT_MODEL_DEPLOYMENT_REQUESTED = "model.deployment.requested"
EVENT_MODEL_DEPLOYMENT_COMPLETED = "model.deployment.completed"

# Model Inference 이벤트
EVENT_MODEL_INFERENCE_REQUESTED = "model.inference.requested"
EVENT_MODEL_INFERENCE_COMPLETED = "model.inference.completed"

# Task Completed 이벤트
EVENT_TASK_COMPLETED = "task.completed"

# Task Failed 이벤트
EVENT_TASK_FAILED = "task.failed"


# 모든 이벤트 매핑 (로깅 및 문서화 목적)
EVENT_DESCRIPTIONS = {
    EVENT_TASK_CREATED: "새로운 태스크 생성",
    EVENT_VIDEO_DOWNLOAD_REQUESTED: "비디오 다운로드 요청",
    EVENT_FRAMES_EXTRACTION_REQUESTED: "프레임 추출 요청",
    EVENT_VIDEO_UPLOAD_REQUESTED: "비디오 업로드 요청",
    EVENT_TRAINING_REQUESTED: "모델 학습 요청",
    EVENT_DEPLOYMENT_REQUESTED: "모델 배포 요청",
    EVENT_INFERENCE_REQUESTED: "모델 추론 요청",
    EVENT_VIDEO_DOWNLOADED: "비디오 다운로드 완료",
    EVENT_FRAMES_EXTRACTED: "프레임 추출 완료",
    EVENT_LABELING_REQUESTED: "라벨링 작업 요청",
    EVENT_LABELING_COMPLETED: "라벨링 작업 완료", 
    EVENT_MODEL_TRAINING_REQUESTED: "모델 학습 요청",
    EVENT_MODEL_TRAINING_COMPLETED: "모델 학습 완료",
    EVENT_MODEL_DEPLOYMENT_REQUESTED: "모델 배포 요청",
    EVENT_MODEL_DEPLOYMENT_COMPLETED: "모델 배포 완료",
    EVENT_MODEL_INFERENCE_COMPLETED: "모델 추론 완료"
}

def get_event_description(event_type):
    """이벤트 타입에 해당하는 설명 반환"""
    return EVENT_DESCRIPTIONS.get(event_type, f"알 수 없는 이벤트: {event_type}")
