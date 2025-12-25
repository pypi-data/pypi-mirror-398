import hashlib
from automation_error_detector.domain.value_objects.keywords import Keywords


class SignatureService:
    @staticmethod
    def generate(keywords: Keywords) -> str:
        raw = "|".join(keywords.words)
        return hashlib.sha256(raw.encode()).hexdigest()
