import json
from openai import OpenAI
from automation_error_detector.config import AppConfig


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=AppConfig.openai_api_key)

    def clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
        return text.strip()

    def analyze(self, screen_text: str) -> dict:
        prompt = f"""
You are an automation error classifier.

Analyze the following browser error screen text.

Return ONLY valid JSON.
Do NOT wrap with markdown.
Do NOT include ```json.

Fields:
- error_code (UPPER_SNAKE_CASE)
- short_description
- keywords (array of strings)
- suggested_action

TEXT:
{screen_text}
"""

        response = self.client.chat.completions.create(
            model=AppConfig.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        content = self.clean_json(response.choices[0].message.content.strip())

        return json.loads(content)
