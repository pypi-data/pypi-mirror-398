from thestage.exceptions.base_exception import BaseAbstractException


class HttpClientException(BaseAbstractException):
    _status_code: int = 0

    def __init__(self, message: str, status_code: int, ):
        super(HttpClientException, self).__init__(message=message)
        self._status_code = status_code

    def get_status_code(self) -> int:
        return self._status_code
