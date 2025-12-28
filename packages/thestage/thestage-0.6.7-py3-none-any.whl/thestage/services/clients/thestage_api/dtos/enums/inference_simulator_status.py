from enum import Enum


class InferenceSimulatorStatus(str, Enum):
    SCHEDULED: str = 'SCHEDULED'
    CREATING: str = 'CREATING'
    CREATING_FAILED: str = 'CREATING_FAILED'
    RUNNING: str = 'RUNNING'
    STOPPING: str = 'STOPPING'
    STOPPED: str = 'STOPPED'
    DELETING: str = 'DELETING'
    DELETED: str = 'DELETED'
    FAILED: str = 'FAILED'
    RESTARTING: str = 'RESTARTING'
    UNKNOWN: str = 'UNKNOWN'
    ALL: str = 'ALL'