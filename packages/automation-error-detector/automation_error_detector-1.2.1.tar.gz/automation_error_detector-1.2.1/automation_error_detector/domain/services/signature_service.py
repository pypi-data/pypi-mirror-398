import hashlib
from automation_error_detector.domain.value_objects.keywords import Keywords


class SignatureService:
    @staticmethod
    def generate(
        keywords: Keywords,
        purpose: str,
        version: str = "v1",
    ) -> str:
        """
        purpose: SCREEN | ERROR | NAVIGATION | ...
        version: allow future evolution without cache break
        """

        raw_parts = [
            version,
            purpose.upper(),
            "|".join(sorted(keywords.words)),
        ]

        raw = "::".join(raw_parts)

        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
