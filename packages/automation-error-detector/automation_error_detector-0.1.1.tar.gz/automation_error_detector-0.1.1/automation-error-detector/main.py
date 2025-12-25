from infrastructure.cache.json_cache_repository import JsonCacheRepository
from infrastructure.ai.openai_client import OpenAIClient
from application.use_cases.detect_error_use_case import DetectErrorUseCase

if __name__ == "__main__":
    cache = JsonCacheRepository()
    ai = OpenAIClient(api_key="YOUR_API_KEY")

    use_case = DetectErrorUseCase(cache, ai)

    screen_text = """
    Your session has expired.
    Please log in again.
    """
    result = use_case.execute(screen_text)
    print(result.to_dict())
