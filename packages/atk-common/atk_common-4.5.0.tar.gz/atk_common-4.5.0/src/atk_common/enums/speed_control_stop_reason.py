from enum import Enum
 
class SpeedControlStopReason(Enum):
    UNKNOWN = 0
    STOPPED_BY_COMMAND = 1
    VIOLATIONS_COMPLETED_REACHED = 2
    STOP_TIME_REACHED = 3
    SERVICE_RESTARTED = 4
