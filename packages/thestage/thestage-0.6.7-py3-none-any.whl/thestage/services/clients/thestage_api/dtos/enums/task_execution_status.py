from enum import Enum


class TaskExecutionStatusEnumDto(str, Enum):
    NEW: str = 'NEW'
    RUNNING: str = 'RUNNING'
    FINISHED: str = 'FINISHED'
    CANCELED: str = 'CANCELED'
    CANCELING: str = 'CANCELING'
    SCHEDULED: str = 'SCHEDULED'
    FAILED: str = 'FAILED'
    UNKNOWN: str = 'UNKNOWN'
