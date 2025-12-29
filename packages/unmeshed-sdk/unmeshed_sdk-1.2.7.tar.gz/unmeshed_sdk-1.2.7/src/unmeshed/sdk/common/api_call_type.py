from enum import Enum

class ApiCallType(Enum):
    SYNC = "SYNC"
    ASYNC = "ASYNC"
    STREAM = "STREAM"