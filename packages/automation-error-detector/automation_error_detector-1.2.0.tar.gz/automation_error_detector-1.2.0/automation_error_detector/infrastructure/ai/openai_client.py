import json
import httpx
from typing import Optional

from openai import OpenAI, AsyncOpenAI

from automation_error_detector.domain.services.ai_service import AIService
from automation_error_detector.config import AppConfig


class OpenAIClient(AIService):
    """
    OpenAI client with full sync + async support.

    - Sync  : OpenAI + httpx.Client
    - Async : AsyncOpenAI + httpx.AsyncClient
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or AppConfig.openai_api_key

        # --------------------
        # HTTP clients
        # --------------------
        self._http_client = self._build_http_client(proxy, timeout)
        self._async_http_client = self._build_async_http_client(proxy, timeout)

        # --------------------
        # OpenAI clients
        # --------------------
        self.client = OpenAI(
            api_key=self.api_key,
            http_client=self._http_client,
        )

        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            http_client=self._async_http_client,
        )

    # ======================================================
    # HTTP CLIENT BUILDERS
    # ======================================================
    def _build_http_client(
        self,
        proxy: Optional[str],
        timeout: float,
    ) -> Optional[httpx.Client]:
        if not proxy:
            return None

        return httpx.Client(
            proxy=proxy,
            timeout=httpx.Timeout(timeout),
        )

    def _build_async_http_client(
        self,
        proxy: Optional[str],
        timeout: float,
    ) -> Optional[httpx.AsyncClient]:
        if not proxy:
            return None

        return httpx.AsyncClient(
            proxy=proxy,
            timeout=httpx.Timeout(timeout),
        )

    # ======================================================
    # UTILS
    # ======================================================
    def clean_json(self, text: str) -> str:
        """
        Remove markdown fences if AI accidentally returns ```json
        """
        text = text.strip()

        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]

        return text.strip()

    # ======================================================
    # ERROR ANALYSIS (SYNC)
    # ======================================================
    def analyze(self, screen_text: str) -> dict:
        prompt = f"""
You are an automation error classifier.

Return ONLY valid JSON.
Do NOT wrap markdown.
Do NOT include ```.

Fields:
- error_code
- short_description
- keywords
- suggested_action

TEXT:
{screen_text}
"""

        response = self.client.chat.completions.create(
            model=AppConfig.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        cleaned = self.clean_json(response.choices[0].message.content)
        return json.loads(cleaned)

    # ======================================================
    # ERROR ANALYSIS (ASYNC)
    # ======================================================
    async def aanalyze(self, screen_text: str) -> dict:
        prompt = f"""
You are an automation error classifier.

Return ONLY valid JSON.
Do NOT wrap markdown.
Do NOT include ```.

Fields:
- error_code
- short_description
- keywords
- suggested_action

TEXT:
{screen_text}
"""

        response = await self.async_client.chat.completions.create(
            model=AppConfig.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        cleaned = self.clean_json(response.choices[0].message.content)
        return json.loads(cleaned)

    # ======================================================
    # SCREEN DETECTION (SYNC)
    # ======================================================
    def detect_screen(self, screen_text: str) -> dict:
        prompt = self._build_screen_prompt(screen_text)

        response = self.client.chat.completions.create(
            model=AppConfig.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        cleaned = self.clean_json(response.choices[0].message.content)
        return json.loads(cleaned)

    # ======================================================
    # SCREEN DETECTION (ASYNC)
    # ======================================================
    async def adetect_screen(self, screen_text: str) -> dict:
        prompt = self._build_screen_prompt(screen_text)

        response = await self.async_client.chat.completions.create(
            model=AppConfig.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        cleaned = self.clean_json(response.choices[0].message.content)
        return json.loads(cleaned)

    # ======================================================
    # PROMPT BUILDER
    # ======================================================
    def _build_screen_prompt(self, screen_text: str) -> str:
        return f"""
You are a UI screen classifier for automation systems.

Your task is to identify the PRIMARY purpose of the screen.

IMPORTANT DECISION RULES:
1. Determine what the screen is MAINLY communicating to the user.
2. If the screen prominently displays a policy notice, restriction,
   or content availability message (e.g. government request, blocked content),
   classify it as permission_screen EVEN IF login or signup options exist.
3. Login or signup elements on global platforms (Facebook, Google, YouTube)
   are often secondary and should NOT override policy or restriction messages.
4. Use error_screen ONLY if the screen is a generic system error page
   without policy or permission context.

Return ONLY valid JSON.
Do NOT wrap markdown.
Do NOT include ```.

Screen types (choose ONE):
- login_screen
- home_screen
- error_screen
- loading_screen
- permission_screen
- confirmation_dialog
- form_screen
- unknown

Fields:
- screen_type
- confidence (0.0 - 1.0)
- reason
- keywords (array)

SCREEN TEXT:
{screen_text}
"""
