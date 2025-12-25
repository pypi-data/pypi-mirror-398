from openai import OpenAI
from config import AppConfig


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=AppConfig.openai_api_key)

    def analyze(self, screen_text: str) -> dict:
        prompt = f"""
You are an automation error classifier.

Analyze the following browser error screen text and return JSON ONLY:

Fields:
- error_code (UPPER_SNAKE_CASE)
- short_description
- keywords (3-6 words)
- suggested_action

TEXT:
{screen_text}
"""

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return eval(response.choices[0].message.content)
