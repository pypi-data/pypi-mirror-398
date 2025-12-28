from automation_error_detector.config.base import BaseConfig


class AppConfig:
    """
    Global configuration for automation-error-detector
    """

    __slots__ = ()
    # ===== OpenAI =====
    openai_api_key: str = BaseConfig.get_env("OPENAI_API_KEY", required=False)

    openai_model: str = BaseConfig.get_env("OPENAI_MODEL", default="gpt-4.1-mini")

    # ===== Cache =====
    cache_file: str = BaseConfig.get_env("ERROR_CACHE_FILE", default="error_cache.json")

    cache_backend: str = BaseConfig.get_env("CACHE_BACKEND", default="json")

    # ===== Behavior =====
    min_keywords: int = BaseConfig.get_env("MIN_KEYWORDS", default=2, cast_type=int)

    enable_ai_fallback: bool = BaseConfig.get_env(
        "ENABLE_AI_FALLBACK", default=True, cast_type=lambda x: x.lower() == "true"
    )
