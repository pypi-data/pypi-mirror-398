from enum import Enum


class LogType(str, Enum):
    STDOUT = "STDOUT",
    STDERR = "STDERR"
