import json
from atk_common.utils.error_utils import get_message
from atk_common.log_utils import add_log_item

def decode_message(body, message):
    import gzip
    import msgpack
    try:
        content_encoding = message.headers.get('content_encoding')
        if content_encoding is not None and content_encoding == 'gzip':
            body = gzip.decompress(body)
        if message.content_type is None or message.content_type == '':
            return body
        elif message.content_type == 'application/json':
            return body
        elif message.content_type == 'application/octet-stream':
            return body
        elif message.content_type == 'application/x-msgpack' or message.content_type == 'application/msgpack':
            return msgpack.unpackb(body, raw=False)
        elif message.content_type.startswith('text/'):
            return body.decode('utf-8')
        else:
            add_log_item('Unknown message content type')
            return None
    except Exception as error:
        add_log_item('Error decoding message: ' + get_message(error))
        return None
