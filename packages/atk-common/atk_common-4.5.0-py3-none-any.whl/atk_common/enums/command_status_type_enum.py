from enum import Enum
 
class CommandStatusType(Enum):
    CREATED = 1
    COMPLETED = 2
    EXPIRED = 3
    FAILED = 4
