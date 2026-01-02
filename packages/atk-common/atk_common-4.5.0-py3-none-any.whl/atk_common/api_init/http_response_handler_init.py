from atk_common.interfaces import *
from atk_common.classes import *

_http_response_handler: HttpResponseHandler | None = None

def create_http_response_handler(logger: ILogger, error_handler: IErrorHandler):
    global _http_response_handler
    _http_response_handler = HttpResponseHandler(logger, error_handler)

def get_http_response_handler():
    global _http_response_handler
    if _http_response_handler is None:
        raise ValueError("HttpResponseHandler not initialized. Call create_http_response_handler first.")
    return _http_response_handler
