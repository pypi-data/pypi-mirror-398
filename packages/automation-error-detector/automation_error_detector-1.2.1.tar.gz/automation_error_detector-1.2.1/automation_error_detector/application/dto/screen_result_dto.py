class ScreenResultDTO:
    def __init__(
        self,
        screen_type: str,
        confidence: float,
        keywords: list[str],
        reason: str,
        source: str = "AI",
    ):
        self.screen_type = screen_type
        self.confidence = confidence
        self.keywords = keywords
        self.reason = reason
        self.source = source

    def to_dict(self):
        return self.__dict__
