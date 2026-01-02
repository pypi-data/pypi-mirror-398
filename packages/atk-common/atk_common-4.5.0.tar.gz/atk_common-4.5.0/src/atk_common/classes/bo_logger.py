import json
from typing import Optional
from opentelemetry.trace import get_current_span
from atk_common.interfaces import ILogger
from atk_common.enums import LogLevel
from atk_common.utils.datetime_utils import get_utc_iso_date_time
from atk_common.utils.str_utils import parse_component_name

class BoLogger(ILogger):
    def __init__(self, log_level: LogLevel, component, version):
        if log_level is None:
            self.log_level = LogLevel.INFO
        else:
            self.log_level = log_level
        self.component = parse_component_name(component)
        self.version = version

    def _get_trace_context(self):
        span = get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            return {
                "trace_id": f"{ctx.trace_id:032x}",
                "span_id": f"{ctx.span_id:016x}",
            }
        return {"trace_id": None, "span_id": None}

    def _create_log_json(self, timestamp, level: LogLevel, message: str):
        log_entry = {
            "timestamp": timestamp,
            "level": level.name,
            "message": message,
            "component": self.component,
            "version": self.version,
        }
        log_entry.update(self._get_trace_context())
        return log_entry

    def _log(self, level: LogLevel, message: str):
        if level.value >= self.log_level.value:
            timestamp = str(get_utc_iso_date_time())
            log_json = self._create_log_json(timestamp, level, message)
            print(json.dumps(log_json))

    def debug(self, message: str):
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str):
        self._log(LogLevel.INFO, message)

    def warning(self, message: str):
        self._log(LogLevel.WARNING, message)

    def error(self, message: str):
        self._log(LogLevel.ERROR, message)

    def set_level(self, log_level: LogLevel):
        self.log_level = log_level

    def get_level(self):
        return self.log_level
