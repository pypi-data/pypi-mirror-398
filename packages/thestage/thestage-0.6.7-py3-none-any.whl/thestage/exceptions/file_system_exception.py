from thestage.exceptions.base_exception import BaseAbstractException


class FileSystemException(BaseAbstractException):
    def __init__(self, message: str):
        super(FileSystemException, self).__init__(message=message)
