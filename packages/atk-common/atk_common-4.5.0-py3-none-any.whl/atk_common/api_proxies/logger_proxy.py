from atk_common.api_init.logger_init import get_bo_logger
from atk_common.interfaces import *

class LoggerProxy(ILogger):
    def __getattribute__(self, name):
        if name in ('__class__', '__dict__', '__module__', '__annotations__'):
            return super().__getattribute__(name)

        # Optional: avoid recursion for special methods
        if name.startswith('__') and name.endswith('__'):
            return super().__getattribute__(name)

        logger = get_bo_logger()
        if logger is None:
            raise RuntimeError("Logger not initialized")
        return getattr(logger, name)
