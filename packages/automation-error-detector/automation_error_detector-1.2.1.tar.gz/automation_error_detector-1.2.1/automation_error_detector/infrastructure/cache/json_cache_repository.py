import asyncio
import json
import os
from automation_error_detector.domain.services.cache_callback import CacheSaveCallback
from automation_error_detector.config import AppConfig


class JsonCacheCallback(CacheSaveCallback):
    def __init__(self, file_path: str | None = None):
        self.file_path = file_path or AppConfig.cache_file
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)

    def _load_all(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _save_all(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, signature: str):
        return self._load_all().get(signature)

    def save(self, signature: str, data: dict) -> None:
        all_data = self._load_all()
        all_data[signature] = data
        self._save_all(all_data)

    # --------------------
    # ASYNC API
    # --------------------
    async def aload(self, signature: str) -> dict | None:
        return await asyncio.to_thread(self.load, signature)

    async def asave(self, signature: str, data: dict) -> None:
        await asyncio.to_thread(self.save, signature, data)
