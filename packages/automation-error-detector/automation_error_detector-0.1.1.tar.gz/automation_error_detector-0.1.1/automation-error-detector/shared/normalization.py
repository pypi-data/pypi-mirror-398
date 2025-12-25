import re

STOPWORDS = {"the", "is", "and", "or", "to", "of", "a", "for", "on", "in"}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_keywords(text: str) -> list[str]:
    return [w for w in text.split() if w not in STOPWORDS and len(w) > 3]
