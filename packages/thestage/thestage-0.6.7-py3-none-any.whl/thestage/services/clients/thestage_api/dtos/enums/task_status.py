from enum import Enum
from typing import List


class TaskStatus(str, Enum):
    NEW: str = 'NEW'
    SCHEDULED: str = 'SCHEDULED'
    RUNNING: str = 'RUNNING'
    FINISHED: str = 'FINISHED'
    CANCELING: str = 'CANCELING'
    CANCELED: str = 'CANCELED'
    FAILED: str = 'FAILED'
