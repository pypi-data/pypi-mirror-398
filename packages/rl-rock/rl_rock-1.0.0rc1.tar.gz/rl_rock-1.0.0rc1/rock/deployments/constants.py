from enum import Enum, IntEnum


class Status(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Port(IntEnum):
    SSH = 22
    PROXY = 8000
    SERVER = 8080
