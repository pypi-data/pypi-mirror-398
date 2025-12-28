from abc import ABC, abstractmethod


class CacheRepository(ABC):

    @abstractmethod
    def get(self, signature: str):
        pass

    @abstractmethod
    def save(self, signature: str, data: dict):
        pass
        