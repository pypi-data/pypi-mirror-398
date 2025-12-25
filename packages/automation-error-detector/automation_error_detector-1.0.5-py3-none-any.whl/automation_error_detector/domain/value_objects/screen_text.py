class ScreenText:
    def __init__(self, raw_text: str):
        if not raw_text:
            raise ValueError("Screen text cannot be empty")
        self.raw_text = raw_text
