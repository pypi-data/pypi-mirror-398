from enum import Enum
 
class HistoryStatusType(Enum):
    PRODUCED = 1
    CONNECTED = 2
    DISCONNECTED = 3
    REPAIR = 4
    DISCARDED = 5
