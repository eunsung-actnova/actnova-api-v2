from app.entities import Video
from .base_repository import BaseRepository

class VideoRepository(BaseRepository):
    def __init__(self, db_session):
        self.db = db_session

    def add(self, video: Video):
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

    def get(self, id):
        return self.db.query(Video).get(id)

    def list(self, **filters):
        query = self.db.query(Video)
        for attr, value in filters.items():
            query = query.filter(getattr(Video, attr) == value)
        return query.all()

    def delete(self, id):
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()