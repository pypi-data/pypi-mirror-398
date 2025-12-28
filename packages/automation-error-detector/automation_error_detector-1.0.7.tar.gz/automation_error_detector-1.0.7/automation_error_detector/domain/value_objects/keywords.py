class Keywords:
    def __init__(self, words: list[str]):
        if len(words) < 2:
            raise ValueError("Not enough keywords")
        self.words = sorted(set(words))
