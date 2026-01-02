from atk_common.api_init.error_handler_init import get_error_handler
from atk_common.interfaces import *

class ErrorHandlerProxy(IErrorHandler):
    def __getattribute__(self, name):
        if name in ('__class__', '__dict__', '__module__', '__annotations__'):
            return super().__getattribute__(name)

        # Optional: avoid recursion for special methods
        if name.startswith('__') and name.endswith('__'):
            return super().__getattribute__(name)

        err_handler = get_error_handler()
        if err_handler is None:
            raise RuntimeError("Error handler not initialized")
        return getattr(err_handler, name)
