from enum import Enum


class ShellType(str, Enum):
    BASH = "/bin/bash"
    SH = "/bin/sh"
    UNKNOWN = "UNKNOWN"
