from atk_common.api_init.http_response_handler_init import get_http_response_handler
from atk_common.interfaces import *

class HttpResponseHandlerProxy(IHttpResponseHandler):
    def __getattribute__(self, name):
        if name in ('__class__', '__dict__', '__module__', '__annotations__'):
            return super().__getattribute__(name)

        # Optional: avoid recursion for special methods
        if name.startswith('__') and name.endswith('__'):
            return super().__getattribute__(name)

        http_response_handler = get_http_response_handler()
        if http_response_handler is None:
            raise RuntimeError("Http response handler not initialized")
        return getattr(http_response_handler, name)
