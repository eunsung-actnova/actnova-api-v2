from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    
    task_id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="created")  # created, processing, completed, failed
    current_step = Column(String, nullable=True)  # video_download, frame_extraction, labeling, training, deployment
    progress = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    estimated_time_remaining = Column(Integer, nullable=True)  # 남은 시간(초)
    step_history = Column(JSON, nullable=True)  # 단계별 시작/종료 시간 추적
