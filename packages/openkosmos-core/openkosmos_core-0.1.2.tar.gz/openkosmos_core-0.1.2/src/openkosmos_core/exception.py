class FatalException(Exception):
    status_code = 505

    def __init__(self, message, detail=None):
        Exception.__init__(self)
        self.message = message
        self.detail = detail

    def to_dict(self):
        value = {"message": self.message, "detail": dict(self.detail or ())}
        return value
