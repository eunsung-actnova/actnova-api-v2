from .base_repository import BaseRepository

class FakeRepository(BaseRepository):
    def __init__(self):
        self.storage = {}

    def add(self, obj):
        self.storage[obj.id] = obj
        return obj

    def get(self, id):
        return self.storage.get(id)

    def list(self, **filters):
        result = list(self.storage.values())
        for attr, value in filters.items():
            result = [obj for obj in result if getattr(obj, attr) == value]
        return result

    def delete(self, id):
        if id in self.storage:
            del self.storage[id]