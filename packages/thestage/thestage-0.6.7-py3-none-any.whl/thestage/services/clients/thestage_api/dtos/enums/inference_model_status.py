from enum import Enum


class InferenceModelStatus(str, Enum):
    SCHEDULED: str = 'SCHEDULED'
    PROCESSING: str = 'PROCESSING'
    PUSH_SUCCEED: str = 'PUSH_SUCCEED'
    PUSH_FAILED: str = 'PUSH_FAILED'
    UNKNOWN: str = 'UNKNOWN'
    ALL: str = 'ALL'