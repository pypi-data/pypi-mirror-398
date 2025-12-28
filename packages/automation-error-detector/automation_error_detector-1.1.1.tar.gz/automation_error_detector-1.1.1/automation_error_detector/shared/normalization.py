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
    return [w for w in text.split() if w not in STOPWORDS and len(w) > 3]


def extract_keywords(text: str) -> list[str]:
    if is_vietnamese(text):
        return extract_keywords_vi(text)
    return extract_keywords_en(text)
