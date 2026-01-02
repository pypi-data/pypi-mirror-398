from enum import Enum
 
class ProcessStatusType(Enum):
    NEW = 1
    STARTED = 2
    FINALIZED = 3
    LOCKED = 4
    NOT_APPROVED = 5
