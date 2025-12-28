from typing import Optional

from thestage.exceptions.base_exception import BaseAbstractException


class RemoteServerException(BaseAbstractException):

    def __init__(
            self,
            message: str,
            ip_address: Optional[str] = None,
            username: Optional[str] = None,
    ):
        super(RemoteServerException, self).__init__(message=message)
        self._ip_address = ip_address
        self._username = username

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def username(self):
        return self._username
