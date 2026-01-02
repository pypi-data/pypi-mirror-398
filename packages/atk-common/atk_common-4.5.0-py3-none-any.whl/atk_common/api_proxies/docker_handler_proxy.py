from atk_common.api_init.docker_handler_init import get_docker_handler
from atk_common.interfaces import *

class DockerHandlerProxy(IDockerHandler):
    def __getattribute__(self, name):
        if name in ('__class__', '__dict__', '__module__', '__annotations__'):
            return super().__getattribute__(name)

        # Optional: avoid recursion for special methods
        if name.startswith('__') and name.endswith('__'):
            return super().__getattribute__(name)

        env_handler = get_docker_handler()
        if env_handler is None:
            raise RuntimeError("Docker handler not initialized")
        return getattr(env_handler, name)
