from atk_common.interfaces import *
from atk_common.classes import *

_env_handler: EnvHandler | None = None

def create_env_handler(logger: ILogger):
    global _env_handler
    _env_handler = EnvHandler(logger)

def get_env_handler():
    global _env_handler
    if _env_handler is None:
        raise ValueError("EnvHandler not initialized. Call create_env_handler first.")
    return _env_handler
