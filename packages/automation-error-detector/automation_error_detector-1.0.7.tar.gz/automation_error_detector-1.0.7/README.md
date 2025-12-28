# Automation Error Detector

🚀 **Automation Error Detector** là một Python package giúp bạn **phát hiện và phân loại lỗi màn hình trình duyệt trong automation**, sử dụng **OpenAI API chỉ một lần**, sau đó **cache kết quả để tái sử dụng mà không cần AI nữa**.

Package được thiết kế theo **DDD + Clean Architecture**, cho phép bạn **tự do lưu cache ở bất kỳ đâu** (Redis, PostgreSQL, file, cloud, v.v.) thông qua **callback**.

---

## ✨ Features

- ✅ Phát hiện lỗi từ **text trên màn hình trình duyệt**
- 🤖 **AI fallback (OpenAI)** chỉ dùng khi cache miss
- ⚡ Cache thông minh bằng **signature từ keywords**
- 🔌 **Pluggable cache callback** (Redis, Postgres, JSON, custom)
- 🧱 Kiến trúc **DDD + Clean Architecture**
- 📦 Sẵn sàng publish & reuse qua **PyPI**
- 🧪 Dễ test, dễ mở rộng, production-ready

---

## 📦 Installation

```bash
pip install automation-error-detector
```

---

## 🔐 Environment Variables

| Name | Required | Description |
|---|---|---|
| OPENAI_API_KEY | ✅ | OpenAI API key |
| OPENAI_MODEL | ❌ | Model name (default: gpt-4.1-mini) |
| ERROR_CACHE_FILE | ❌ | Cache file path (JSON adapter) |

```bash
export OPENAI_API_KEY="sk-xxxx"
```

---

## 🚀 Quick Start

```python
from application.use_cases.detect_error_use_case import DetectErrorUseCase
from infrastructure.ai.openai_client import OpenAIClient
from infrastructure.cache.json_cache_callback import JsonCacheCallback

cache = JsonCacheCallback()
ai = OpenAIClient()

use_case = DetectErrorUseCase(
    cache_callback=cache,
    ai_client=ai
)

screen_text = """
Your session has expired.
Please log in again.
"""

result = use_case.execute(screen_text)
print(result.to_dict())
```
🌐 OpenAI Proxy (Instance-based)

Package KHÔNG dùng HTTP_PROXY / HTTPS_PROXY của OS.
Proxy được inject theo từng OpenAIClient instance.

HTTP / HTTPS Proxy
```python 
proxy = {
    "https": "http://127.0.0.1:8080"
}

ai = OpenAIClient(proxy=proxy)
```


SOCKS5 Proxy
```python 
proxy = {
    "socks": "socks5://127.0.0.1:1080"
}

ai = OpenAIClient(proxy=proxy)
```
---

## 🔌 Custom Cache Callback

Bạn có thể lưu cache ở **bất kỳ đâu** bằng cách implement callback.

```python
from domain.services.cache_callback import CacheSaveCallback

class CacheSaveCallback:
    def load(self, signature: str) -> dict | None:
        pass

    def save(self, signature: str, data: dict) -> None:
        pass
```

---

## ⚙️ Configuration API

```python
from config import AppConfig

AppConfig.openai_api_key
AppConfig.openai_model
AppConfig.cache_file
```

---

## 🔒 Security Notes

- Không hard-code API key
- Không commit `.env`
- Luôn dùng ENV variables

---

## 📄 License

MIT License
