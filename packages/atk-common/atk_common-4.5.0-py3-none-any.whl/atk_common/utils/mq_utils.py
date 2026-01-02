import json
from http import HTTPStatus
from atk_common.interfaces import ILogger
from atk_common.enums.response_status_type_enum import ResponseStatusType
from atk_common.utils.error_utils import get_message
from atk_common.utils.internal_response_utils import create_response

def decode_message(body, message, logger: ILogger):
    import gzip
    import msgpack
    try:
        content_encoding = message.headers.get('content_encoding')
        if content_encoding is not None and content_encoding == 'gzip':
            body = gzip.decompress(body)
        if message.content_type is None or message.content_type == '':
            return create_response(ResponseStatusType.OK, HTTPStatus.OK, body)
        elif message.content_type == 'application/json':
            return create_response(ResponseStatusType.OK, HTTPStatus.OK, body)
        elif message.content_type == 'application/octet-stream':
            return create_response(ResponseStatusType.OK, HTTPStatus.OK, body)
        elif message.content_type == 'application/x-msgpack' or message.content_type == 'application/msgpack':
            return create_response(ResponseStatusType.OK, HTTPStatus.OK, msgpack.unpackb(body, raw=False))
        elif message.content_type.startswith('text/'):
            return create_response(ResponseStatusType.OK, HTTPStatus.OK, body.decode('utf-8'))
        else:
            err_msg = f"Unknown message content type {message.content_type}. Cannot decode message."
            logger.error(err_msg)
            return create_response(ResponseStatusType.INTERNAL, HTTPStatus.INTERNAL_SERVER_ERROR, err_msg)
    except Exception as error:
        logger.error('Error decoding message: ' + get_message(error))
        return create_response(ResponseStatusType.INTERNAL, HTTPStatus.INTERNAL_SERVER_ERROR, get_message(error))
