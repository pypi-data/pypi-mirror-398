from enum import Enum
 
class HttpStatus(Enum):
    INFO = 100
    OK = 200
    REDIRECT = 300
    CLIENT = 400
    INTERNAL = 500
