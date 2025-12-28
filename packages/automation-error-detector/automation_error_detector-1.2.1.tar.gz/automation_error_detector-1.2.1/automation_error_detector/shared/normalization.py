import re
import unicodedata
from .text_dispatcher import is_vietnamese
from .vi_text_processor import extract_keywords_vi

STOPWORDS = {"the", "is", "and", "or", "to", "of", "a", "for", "on", "in"}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_keywords_en(text: str) -> list[str]:
    text = normalize(text)

    keywords: set[str] = set()

    # =========================
    # AUTH SIGNALS (login)
    # =========================
    AUTH_PHRASES = [
        "log in",
        "login",
        "sign in",
        "sign up",
        "create account",
        "password",
        "email",
        "phone",
    ]

    # =========================
    # BLOCK SIGNALS (permission)
    # =========================
    BLOCK_PHRASES = [
        "not available",
        "cannot view",
        "content blocked",
        "restricted",
        "not allowed",
        "access denied",
        "unavailable",
    ]

    # 1️⃣ Match PHRASES (highest priority)
    for phrase in AUTH_PHRASES + BLOCK_PHRASES:
        if phrase in text:
            keywords.add(phrase)

    # 2️⃣ Limited single-word fallback
    words = text.split()
    for w in words:
        if w in {"login", "password", "signin"}:
            keywords.add("login")
        elif w in {"blocked", "restricted", "denied"}:
            keywords.add("restricted")

    # 3️⃣ Safety fallback (ensure >= 2 keywords)
    if len(keywords) < 2:
        keywords.add("generic")
        keywords.add("screen")

    return sorted(keywords)


def extract_keywords(text: str) -> list[str]:
    if is_vietnamese(text):
        return extract_keywords_vi(text)
    return extract_keywords_en(text)
