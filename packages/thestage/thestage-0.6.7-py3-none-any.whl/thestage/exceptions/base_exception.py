
class BaseAbstractException(Exception):
    def __init__(self, message: str):
        self._message = message

    def __str__(self):
        return self._message

    def __repr__(self):
        return self._message

    def get_message(self) -> str:
        return self._message
