import os


class BaseConfig:
    @staticmethod
    def get_env(key: str, default=None, required: bool = False, cast_type=str):
        value = os.getenv(key, default)

        if required and not value:
            raise RuntimeError(f"Missing required environment variable: {key}")

        if value is None:
            return None

        try:
            return cast_type(value)
        except Exception:
            raise ValueError(f"Invalid value for env var {key}")
