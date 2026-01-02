import sys
from datetime import datetime
from atk_common.datetime_utils import get_utc_date_time_str
from atk_common.enums.log_level_enum import LogLevel

class BoLogger:
    def __init__(self, log_level: LogLevel, log_url):
        if log_level is None:
            self.log_level = LogLevel.INFO.value
        else:
            self.log_level = log_level
        self.log_url = log_url

    def set_level(self, log_level):
        self.log_level = log_level

    def _create_log_json(self, timestamp, level: LogLevel, message: str):
        log_entry = {
            "timestamp": timestamp,
            "level": LogLevel.name(level),
            "message": message
        }
        return log_entry

    def _log(self, level: LogLevel, message: str):
        if level >= self.log_level:
            timestamp = get_utc_date_time_str()
            log_json = self._create_log_json(timestamp, level, message)
            print('[' + timestamp + '] ' + LogLevel.name(level) + ': ' + message)
            # TODO:
            # Send log_json to self.log_url via HTTP POST request (Grafana Loki or similar)

    def debug(self, message: str):
        self._log(LogLevel.DEBUG.value, message)

    def info(self, message: str):
        self._log(LogLevel.INFO.value, message)

    def warning(self, message: str):
        self._log(LogLevel.WARNING.value, message)

    def error(self, message: str):
        self._log(LogLevel.ERROR.value, message)

    def critical(self, message: str):
        self._log(LogLevel.CRITICAL.value, message)
