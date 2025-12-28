import json
from automation_error_detector.domain.services.ai_service import AIService
import httpx
from openai import OpenAI
from automation_error_detector.config import AppConfig


class OpenAIClient(AIService):
    """
    OpenAI client with optional per-instance proxy support.

    proxy example:
    {
        "http": "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8080",
        "socks": "socks5://127.0.0.1:1080"
    }
    """

    def __init__(self, key: str | None = None, proxy: str | None = None):
        self.client = OpenAI(
            api_key=key or AppConfig.openai_api_key,
            http_client=self._build_http_client(proxy),
        )

    def _build_http_client(self, proxy: dict | None) -> httpx.Client | None:
        if not proxy:
            return None

        return httpx.Client(
            proxy=proxy,
            timeout=httpx.Timeout(30.0),
        )

    def clean_json(self, text: str) -> str:
        """
        Remove markdown fences if AI accidentally returns ```json
        """
        text = text.strip()

        if text.startswith("```"):
            # handle ```json\n{...}\n```
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]

        return text.strip()

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

        raw_content = response.choices[0].message.content
        cleaned = self.clean_json(raw_content)

        return json.loads(cleaned)

    def detect_screen(self, screen_text: str) -> dict:
        """
        Detect current screen type from UI text / OCR text.

        Returns JSON:
        {
            screen_type: str,
            confidence: float (0-1),
            reason: str,
            keywords: list[str]
        }
        """

        prompt = f"""
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

        response = self.client.chat.completions.create(
            model=AppConfig.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        raw_content = response.choices[0].message.content
        cleaned = self.clean_json(raw_content)

        return json.loads(cleaned)
