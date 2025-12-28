from enum import Enum, unique


@unique
class Status(Enum):
    SUCCESS = 0
    RUN_TIME_ERROR = -90000
    PARAM_ERROR = -90001
    CORTEX_NOT_FOUND = -90002
    CORTEX_HAS_CYCLE = -90003
    CORTEX_CONFIG_ERROR = -90004
    CORTEX_NODE_MISSING = -90005
    NODE_EXECUTE_FAIL = -90006
    NODE_CANCELLED = -90007


@unique
class StateKey(Enum):
    TIME_DURATION = "time_duration"


@unique
class ErrorCode(Enum):
    SUCCESS = 0
    UNKNOWN_ERROR = -1


@unique
class ErrorMsg(Enum):
    SUCCESS = "success"
    UNKNOWN_ERROR = "unknown error"
