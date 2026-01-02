from atk_common.interfaces import *
from atk_common.classes import *

_docker_handler: DockerHandler | None = None

def create_docker_handler(logger: ILogger, env_handler: IEnvHandler, image_name_key: str, image_version_key: str):
    global _docker_handler
    _docker_handler = DockerHandler(
        logger, 
        env_handler.get_env_value(image_name_key), 
        env_handler.get_env_value(image_version_key))

def get_docker_handler():
    global _docker_handler
    if _docker_handler is None:
        raise ValueError("DockerHandler not initialized. Call create_docker_handler first.")
    return _docker_handler
