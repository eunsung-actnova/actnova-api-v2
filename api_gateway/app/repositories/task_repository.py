from app.entities.task import Task
from .base_repository import BaseRepository

class TaskRepository(BaseRepository):
    def __init__(self, db_session):
        self.db = db_session

    def add(self, task: Task):
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, id):
        return self.db.query(Task).get(id)

    def list(self, **filters):
        query = self.db.query(Task)
        for attr, value in filters.items():
            query = query.filter(getattr(Task, attr) == value)
        return query.all()

    def delete(self, id):
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()