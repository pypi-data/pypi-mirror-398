from enum import Enum


class InstanceGpuType(str, Enum):
    NVIDIA: str = 'NVIDIA'
    AMD: str = 'AMD'
    NO_GPU: str = 'NO_GPU'
    UNKNOWN: str = 'UNKNOWN'
