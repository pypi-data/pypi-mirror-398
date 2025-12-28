from thestage.exceptions.base_exception import BaseAbstractException


class LogPollingException(BaseAbstractException):
    def __init__(self, message: str):
        super(LogPollingException, self).__init__(message=message)
