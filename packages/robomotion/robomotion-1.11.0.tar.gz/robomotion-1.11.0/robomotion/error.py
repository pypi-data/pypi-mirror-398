import json


class Error(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def serialize(self) -> str:
        err = {"code": self.code, "message": self.message}
        return json.dumps(err)


RuntimeNotInitializedError = Error("", "Runtime was not initialized")
