from enum import Enum


class InstanceCpuType(str, Enum):
    INTEL: str = 'INTEL'
    AMD: str = 'AMD'
    ARM: str = 'ARM'
    UNKNOWN: str = 'UNKNOWN'
