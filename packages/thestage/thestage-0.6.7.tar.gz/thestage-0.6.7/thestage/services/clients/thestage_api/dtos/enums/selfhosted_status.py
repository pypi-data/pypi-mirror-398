from enum import Enum


class SelfhostedBusinessStatus(str, Enum):
    AWAITING_CONFIGURATION: str = 'AWAITING_CONFIGURATION'
    RUNNING: str = 'RUNNING'
    UNREACHABLE_DAEMON: str = 'UNREACHABLE_DAEMON'
    DELETED: str = 'DELETED'
    UNKNOWN: str = 'UNKNOWN'
    ALL: str = 'ALL'
