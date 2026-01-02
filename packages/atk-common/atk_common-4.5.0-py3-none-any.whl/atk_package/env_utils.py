import os
from atk_common.log_utils import add_log_item

def get_env_value(key, default_value):
    try:
        val = os.environ[key]
        add_log_item(key + ':' + val)
        return val
    except (Exception) as error:
        add_log_item(key + ':' + default_value)
        return default_value
