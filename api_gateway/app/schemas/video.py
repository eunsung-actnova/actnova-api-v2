from pydantic import BaseModel


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

