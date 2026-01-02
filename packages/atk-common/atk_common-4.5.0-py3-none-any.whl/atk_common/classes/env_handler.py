import os
from pathlib import Path
from typing import Optional
from atk_common.interfaces import IEnvHandler
from atk_common.interfaces import ILogger

class EnvHandler(IEnvHandler):
    def __init__(self, logger: Optional[ILogger]):
        self.logger = logger

    def set_logger(self, logger: ILogger):
        self.logger = logger

    def val_str(self, value: Optional[object]) -> str:
        if value is None:
            return '<Empty>'
        if isinstance(value, str):
            if value.strip() == '' or value.lower() == 'null':
                return '<Null>'
            return value
        return str(value)

    def is_value_null_or_empty(self, value: Optional[str]) -> bool:
        if value is None:
            return True
        s = value.strip()
        return s == '' or s.lower() == 'null'
    
    def get_env_value(self, key: str) -> Optional[str]:
        val = os.environ.get(key)
        if val is None:
            err_msg = f"Environment key '{key}' is missing."
            if self.logger:
                self.logger.error(err_msg)
            raise ValueError(err_msg)
        if self.logger:
            self.logger.info(key + ':' + self.val_str(val))
        if self.is_value_null_or_empty(val):
            return None
        return val

    @staticmethod    
    def read_secret(path):
        return Path(path).read_text().rstrip('\n')

    def get_env_value_secret(self, key: str, file_key: str) -> str:
        val = os.environ.get(key)
        if val is None:
            err_msg = f"Environment key '{key}' is missing."
            if self.logger:
                self.logger.error(err_msg)
            raise ValueError(err_msg)
        if self.is_value_null_or_empty(val):
            secret_path = os.getenv(file_key)
            if secret_path is None:
                err_msg = f"Secret file key '{file_key}' is missing."
                if self.logger:
                    self.logger.error(err_msg)
                raise ValueError(err_msg)
            if self.is_value_null_or_empty(secret_path):
                err_msg = f"Secret file variable '{file_key}' is not set."
                if self.logger:
                    self.logger.error(err_msg)
                raise ValueError(err_msg)
            if not Path(secret_path).is_file():
                err_msg = f"Secret file '{secret_path}' not found."
                if self.logger:
                    self.logger.error(err_msg)
                raise ValueError(err_msg)
            val = self.read_secret(secret_path)
            if self.is_value_null_or_empty(val):
                err_msg = f"Secret from key file '{secret_path}' is empty."
                if self.logger:
                    self.logger.error(err_msg)
                raise ValueError(err_msg)
        return val
