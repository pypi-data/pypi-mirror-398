from atk_common.interfaces import *
from atk_common.classes import *

_error_handler: ErrorHandler | None = None

def create_error_handler(logger: ILogger, docker_handler: IDockerHandler):
    global _error_handler
    _error_handler = ErrorHandler(logger, docker_handler)

def get_error_handler():
    global _error_handler
    if _error_handler is None:
        raise ValueError("ErrorHandler not initialized. Call create_error_handler first.")
    return _error_handler
