import enum
from abc import ABC, abstractmethod
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

Base = declarative_base()


class LabellingStatus(enum.Enum):
    INPROGRESS = "INPROGRESS"
    COMPLETE = "COMPLETE"


class LabelTask(Base):
    __tablename__ = "label_tasks"

    task_id = sa.Column(sa.String, primary_key=True)
    status = sa.Column(
        Enum(LabellingStatus), nullable=False, default=LabellingStatus.INPROGRESS
    )
    label_url = sa.Column(sa.String, nullable=False)
    user_id = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())
    updated_at = sa.Column(sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())


class LabelTaskRepository(ABC):
    @abstractmethod
    def get_label_task(self, task_id: str) -> Optional[LabelTask]:
        raise NotImplementedError

    @abstractmethod
    def get_label_tasks_by_status(self, status: str) -> List[LabelTask]:
        raise NotImplementedError

    @abstractmethod
    def save_label_task(self, task: LabelTask) -> LabelTask:
        raise NotImplementedError


class PostgresLabelTaskRepository(LabelTaskRepository):
    def __init__(self, db_url: str):
        self.engine = sa.create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """데이터베이스 테이블을 생성합니다. 애플리케이션 시작 시 한 번만 호출해야 합니다."""
        Base.metadata.create_all(self.engine)

    def _get_session(self) -> Session:
        return self.Session()

    def get_label_task(self, task_id: str) -> Optional[LabelTask]:
        with self._get_session() as session:
            return session.query(LabelTask).filter(LabelTask.task_id == task_id).first()

    def get_label_tasks_by_status(self, status: str) -> List[LabelTask]:
        with self._get_session() as session:
            return session.query(LabelTask).filter(LabelTask.status == status).all()

    def save_label_task(self, task: LabelTask) -> LabelTask:
        with self._get_session() as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        
    def update_label_task_status(self, task_id: str, new_status: str):
        with self._get_session() as session:
            session.query(LabelTask).filter(LabelTask.task_id == task_id).update({LabelTask.status: new_status})
            session.commit()


class FakeLabelTaskRepository(LabelTaskRepository):
    def __init__(self):
        self.tasks: dict[str, LabelTask] = {}

    def get_label_task(self, task_id: str) -> Optional[LabelTask]:
        return self.tasks.get(task_id)

    def get_label_tasks_by_status(self, status: str) -> List[LabelTask]:
        return [
            task for task in self.tasks.values()
            if task.status.value == status
        ]

    def save_label_task(self, task: LabelTask) -> LabelTask:
        self.tasks[task.task_id] = task
        return task
