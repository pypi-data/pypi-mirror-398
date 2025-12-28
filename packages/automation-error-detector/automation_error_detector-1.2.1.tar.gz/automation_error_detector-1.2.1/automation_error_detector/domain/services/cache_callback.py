from abc import ABC, abstractmethod


class CacheSaveCallback(ABC):
    """
    User-defined cache persistence
    """

    @abstractmethod
    def save(self, signature: str, data: dict) -> None:
        """
        Persist cache data anywhere (DB, Redis, file, etc.)
        """
        pass

    @abstractmethod
    def load(self, signature: str) -> dict | None:
        """
        Load cached data by signature
        """
        pass

    @abstractmethod
    async def aload(self, signature: str) -> dict | None: ...
    @abstractmethod
    async def asave(self, signature: str, data: dict) -> None: ...
