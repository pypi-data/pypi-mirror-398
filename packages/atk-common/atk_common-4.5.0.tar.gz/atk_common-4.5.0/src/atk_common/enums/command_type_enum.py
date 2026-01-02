from enum import Enum
 
class CommandType(Enum):
    POINT_ENFORCEMENT = 1
    SECTION_ENFORCEMENT = 2
    LOCATION_CONFIG = 3
    PING = 4
    CAPTURE_IMAGE = 5
    GETLAST_IMAGE = 6
    GETNEXT_IMAGE = 7
    WRITE_CAMERA_AUX = 8
    STOP_ENFORCEMENTS = 9
    RESTART_CAMERA = 10
