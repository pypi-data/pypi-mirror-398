import json
import httpx
from openai import OpenAI
from automation_error_detector.config import AppConfig


class OpenAIClient:
    """
    OpenAI client with optional per-instance proxy support.

    proxy example:
    {
        "http": "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8080",
        "socks": "socks5://127.0.0.1:1080"
    }
    """

    def __init__(self, proxy: dict | None = None):
        self.client = OpenAI(
            api_key=AppConfig.openai_api_key,
            http_client=self._build_http_client(proxy),
        )

    def _build_http_client(self, proxy: dict | None) -> httpx.Client | None:
        if not proxy:
            return None

        proxies: dict[str, str] = {}

        if proxy.get("http"):
            proxies["http://"] = proxy["http"]

        if proxy.get("https"):
            proxies["https://"] = proxy["https"]

        if proxy.get("socks"):
            proxies["all://"] = proxy["socks"]

        if not proxies:
            return None

        return httpx.Client(
            proxies=proxies,
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
