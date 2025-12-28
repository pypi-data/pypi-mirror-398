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
    text = normalize_vi(text)

    keywords: set[str] = set()

    # =========================
    # AUTH SIGNALS (login)
    # =========================
    AUTH_PHRASES = [
        "dang nhap",
        "phai dang nhap",
        "can dang nhap",
        "tao tai khoan",
        "mat khau",
        "email",
        "dien thoai",
    ]

    # =========================
    # BLOCK SIGNALS (permission)
    # =========================
    BLOCK_PHRASES = [
        "khong xem duoc",
        "khong hien thi",
        "bi han che",
        "theo yeu cau",
        "noi dung nay",
        "khong the xem",
    ]

    # 1️⃣ Match PHRASES (highest priority)
    for phrase in AUTH_PHRASES + BLOCK_PHRASES:
        if phrase in text:
            keywords.add(phrase)

    # 2️⃣ Fallback single-word signals (VERY limited)
    words = text.split()
    for w in words:
        if w in {"dang", "nhap", "mat", "khau"}:
            keywords.add("dang nhap")
        elif w in {"han", "che"}:
            keywords.add("bi han che")

    # 3️⃣ Safety fallback (ensure >= 2 keywords)
    if len(keywords) < 2:
        keywords.add("generic")
        keywords.add("screen")

    return sorted(keywords)
