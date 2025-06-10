from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship


from datetime import datetime
from datetime import timezone

from app.entities.base import Base

class VideoType(str, Enum):
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WMV = "wmv"
    FLV = "flv"
    WEBM = "webm"


class VideoCodec(str, Enum):
    AVC1 = "avc1"
    MP4V = "mp4v"
    HEV1 = "hev1"
    HVC1 = "hvc1"
    XVID = "XVID"
    DIVX = "DIVX"
    MJPG = "MJPG"
    VP80 = "VP80"
    VP90 = "VP90"
    WMV1 = "WMV1"
    WMV2 = "WMV2"
    WMV3 = "WMV3"
    H263 = "H263"
    H264 = "H264"


class CameraAngle(str, Enum):
    TOP = "top"
    FRONT = "front"
    BOTTOM = "bottom"

class VideoQuality(str, Enum):
    QUALIFIED: "qualified"
    UNQUALIFIED: "unqualified"

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, unique=True)
    frame_count = Column(Integer, nullable=True)
    codec = Column(VideoCodec, nullable=True)
    video_type = Column(VideoType, nullable=True)
    duration_sec = Column(Float, nullable=True)
    camera_angle = Column(CameraAngle, nullable=True)
    video_quality = Column(VideoQuality, nullable=True)
    upload_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    task = relationship("Task", back_populates="video", uselist=False)
    
    
    

