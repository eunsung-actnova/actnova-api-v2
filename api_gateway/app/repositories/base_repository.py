from abc import ABC, abstractmethod


class BaseRepository(ABC):
    @abstractmethod
    def add(self, obj):
        pass

    @abstractmethod
    def get(self, id):
        pass

    @abstractmethod
    def list(self, **filters):
        pass

    @abstractmethod
    def delete(self, id):
        pass