from typing import Callable, Any, Optional
from http import HTTPStatus
from atk_common.enums import *
from atk_common.interfaces import *
from atk_common.classes import *
from atk_common.utils import *

_bo_logger: BoLogger | None = None
_image_name_key: str | None = None

def create_bo_logger(env_handler: IEnvHandler, log_level: LogLevel, image_name_key: str, image_version_key: str):
    global _bo_logger
    global _image_name_key
    _image_name_key = image_name_key
    _bo_logger = BoLogger(
        log_level, 
        env_handler.get_env_value(image_name_key), 
        env_handler.get_env_value(image_version_key))
    _bo_logger.info(f"Log level set to default {log_level.name}")

def get_bo_logger():
    global _bo_logger
    if _bo_logger is None:
        raise ValueError("BoLogger not initialized. Call create_bo_logger first.")
    return _bo_logger

def create_log_level_response(log_level: LogLevel):
    return {
        'logLevel': log_level.name
    }

def set_log_level(request, endpoint):
    global _bo_logger

    if _bo_logger is None:
        raise ValueError("Logger not initialized. Call create_bo_logger first.")
    
    log_level = request.json.get('logLevel')
    if log_level is not None:
        ll = LogLevel(log_level)
        _bo_logger.info('IN: ' + endpoint, item_id=ll.name)
        _bo_logger.set_level(ll)
        _bo_logger.info(f"Log level set to {ll.name}")
    else:
        ll = LogLevel.INFO
        _bo_logger.info('IN: ' + endpoint, item_id=ll.name)
        _bo_logger.set_level(ll)
        _bo_logger.info(f"Log level set to default {ll.name}")
    _bo_logger.info('OUT: ' + endpoint, item_id=ll.name)
    return create_response(ResponseStatusType.OK, HTTPStatus.OK, create_log_level_response(ll))
