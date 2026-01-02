from enum import Enum
 
class SpeedControlStatusType(Enum):
    CREATED = 1
    CONFIRMED = 2
    STARTED = 3
    FAILED = 4
    PAUSED = 5
    STOPPED = 6
    DELETED = 7
