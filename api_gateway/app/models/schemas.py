from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# 기본 응답 모델
class TaskResponse(BaseModel):
    task_id: str


# 태스크 생성 요청 모델
class TaskCreate(BaseModel):
    file_path: str
    user_id: str


# 비디오 다운로드 요청 모델
class VideoDownload(BaseModel):
    file_path: str
    download_path: str


# 비디오 프레임 추출 요청 모델
class VideoExtractFrames(BaseModel):
    file_path: str
    num_frames: int


# 비디오 업로드 요청 모델
class VideoUpload(BaseModel):
    file_path: str
    upload_path: str


# 라벨링 요청 모델
class LabelingCreate(BaseModel):
    folder_path: str
    task_id: str
    user_id: str


# 모델 학습 요청 모델
class TrainingCreate(BaseModel):
    data_path: str
    mode_train_info: Dict[str, Any]


# 모델 배포 요청 모델
class DeploymentCreate(BaseModel):
    task_id: str
    model_path: str


# 모델 추론 요청 모델
class InferenceCreate(BaseModel):
    data_path: str
    confidence: float
    iou: float
    batch_size: int
    frame_skip: int
    max_frames: int
