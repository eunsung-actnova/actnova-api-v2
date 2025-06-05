from pydantic import BaseModel

# 라벨링 요청 모델
class LabelingCreate(BaseModel):
    folder_path: str
    task_id: str
    user_id: str

