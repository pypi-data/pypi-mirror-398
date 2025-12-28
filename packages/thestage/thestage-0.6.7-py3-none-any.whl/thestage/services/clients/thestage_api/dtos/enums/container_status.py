from enum import Enum


class DockerContainerStatus(str, Enum):
    FAILED: str = 'FAILED'
    BUSY: str = 'BUSY'
    DEAD: str = 'DEAD'
    CREATING: str = 'CREATING'
    CREATING_FAILED: str = 'CREATING_FAILED'
    STARTING: str = 'STARTING'
    RUNNING: str = 'RUNNING'
    STOPPING: str = 'STOPPING'
    STOPPED: str = 'STOPPED'
    RESTARTING: str = 'RESTARTING'
    DELETING: str = 'DELETING'
    DELETED: str = 'DELETED'
    UNKNOWN: str = 'UNKNOWN'
