# interfaces/env_handler_interface.py
from typing import Protocol

class IHttpResponseHandler(Protocol):
    def http_response(self, method, response) -> None: ...
