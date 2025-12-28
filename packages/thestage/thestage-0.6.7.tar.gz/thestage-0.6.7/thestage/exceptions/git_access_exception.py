from thestage.exceptions.base_exception import BaseAbstractException


class GitAccessException(BaseAbstractException):

    __url: str

    def __init__(self, message: str, url: str, dop_message: str):
        super(GitAccessException, self).__init__(message=message)
        self.__url = url
        self.__dop_message = dop_message

    def get_url(self) -> str:
        return self.__url

    def get_dop_message(self) -> str:
        return self.__dop_message
