from thestage.exceptions.base_exception import BaseAbstractException


class ConfigException(BaseAbstractException):
    def __init__(self, message: str):
        super(ConfigException, self).__init__(message=message)
