import re
import unicodedata


def remove_vietnamese_tone(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


def normalize_vi(text: str) -> str:
    text = text.lower()
    text = remove_vietnamese_tone(text)
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


STOPWORDS_VI = {
    "da",
    "dang",
    "se",
    "can",
    "vui",
    "long",
    "hay",
    "va",
    "la",
    "bi",
    "khi",
    "neu",
    "lai",
}


def extract_keywords_vi(text: str) -> list[str]:
    normalized = normalize_vi(text)
    words = normalized.split()

    keywords = set()

    # unigram
    for w in words:
        if len(w) >= 4 and w not in STOPWORDS_VI:
            keywords.add(w)

    # bigram (VERY IMPORTANT)
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if (
            len(w1) >= 3
            and len(w2) >= 3
            and w1 not in STOPWORDS_VI
            and w2 not in STOPWORDS_VI
        ):
            keywords.add(f"{w1} {w2}")
    return sorted(keywords)
