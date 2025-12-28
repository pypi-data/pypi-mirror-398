class ErrorResultDTO:
    def __init__(self, error_code, description, keywords, action, source):
        self.error_code = error_code
        self.description = description
        self.keywords = keywords
        self.action = action
        self.source = source

    def to_dict(self):
        return self.__dict__
