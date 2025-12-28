import abc
import json
import httpx
from openai import OpenAI
from automation_error_detector.config import AppConfig


class AIService(abc.ABC):
    @abc.abstractmethod
    def analyze(self, screen_text: str) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def detect_screen(self, screen_text: str) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    async def aanalyze(self, screen_text: str) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    async def adetect_screen(self, screen_text: str) -> dict:
        raise NotImplementedError
