from automation_error_detector.config.base import BaseConfig


class AppConfig:
    # ===== OpenAI =====
    openai_api_key: str = BaseConfig.get_env("OPENAI_API_KEY", required=True)

    openai_model: str = BaseConfig.get_env("OPENAI_MODEL", default="gpt-4.1-mini")

    # ===== OpenAI Proxy (package scoped) =====
    openai_proxy_http: str | None = BaseConfig.get_env(
        "OPENAI_PROXY_HTTP", default=None
    )

    openai_proxy_https: str | None = BaseConfig.get_env(
        "OPENAI_PROXY_HTTPS", default=None
    )

    openai_proxy_socks: str | None = BaseConfig.get_env(
        "OPENAI_PROXY_SOCKS", default=None
    )
