from enum import Enum
 
class ProcessStatus(Enum):
    NEW = 1
    STARTED = 2
    FINALIZED = 3
    LOCKED = 4
    NOTAPPROVED = 5
