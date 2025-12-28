from thestage.exceptions.base_exception import BaseAbstractException


class AuthException(BaseAbstractException):
    def __init__(self, message: str):
        super(AuthException, self).__init__(message=message)
