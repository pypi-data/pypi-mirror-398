from atk_common.api_init.env_handler_init import get_env_handler
from atk_common.interfaces import *

class EnvHandlerProxy(IEnvHandler):
    def __getattribute__(self, name):
        if name in ('__class__', '__dict__', '__module__', '__annotations__'):
            return super().__getattribute__(name)

        # Optional: avoid recursion for special methods
        if name.startswith('__') and name.endswith('__'):
            return super().__getattribute__(name)

        env_handler = get_env_handler()
        if env_handler is None:
            raise RuntimeError("Env handler not initialized")
        return getattr(env_handler, name)
