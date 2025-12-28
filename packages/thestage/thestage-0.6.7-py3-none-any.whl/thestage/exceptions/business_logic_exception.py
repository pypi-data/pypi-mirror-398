from thestage.exceptions.base_exception import BaseAbstractException


class BusinessLogicException(BaseAbstractException):
    def __init__(self, message: str):
        super(BusinessLogicException, self).__init__(message=message)
