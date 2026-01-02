from enum import Enum
 
class MqRetryActionType(Enum):
    SEND_TO_DLQ = 1
    SEND_TO_RETRY = 2
    DISCARD = 3
