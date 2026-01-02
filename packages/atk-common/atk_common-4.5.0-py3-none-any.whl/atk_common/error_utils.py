from http import HTTPStatus
from flask import Response
from enum import Enum
import json
from atk_common.datetime_utils import get_utc_date_time_str
from atk_common.enums.api_error_type_enum import ApiErrorType
from atk_common.http_utils import is_http_status_internal
from atk_common.log_utils import add_log_item
from atk_common.internal_response_utils import create_response

def get_message(error):
    if hasattr(error, 'message'):
        return str(error.message)
    else:
        return str(error)
    
def create_error_log(data):
    err_str = data['message'] + ', statusCode: ' + str(data['statusCode']) + ', method: ' + data['method']
    if data['containerInfo'] is not None:
        err_str += ', imageName: ' + data['containerInfo']['imageName']
        err_str += ', imageVersion: ' + data['containerInfo']['imageVersion']
        err_str += ', containerName: ' + data['containerInfo']['containerName']
    else:
        err_str += ', imageName: <none>'
        err_str += ', imageVersion: <none>'
        err_str += ', containerName: <none>'
    add_log_item(err_str)

def get_error_entity(error, method, error_type, status_code, container_info):
    data = {}
    data['statusCode'] = status_code
    data['exceptionType'] = str(type(error))
    data['errorType'] = error_type.value if isinstance(error_type, Enum) else error_type
    data['message'] = get_message(error)
    data['method'] = method
    data['timestamp'] = get_utc_date_time_str()
    data['containerInfo'] = container_info
    create_error_log(data)
    return Response(
        response=json.dumps(data),
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        mimetype='application/json'
    )

def resend_error_entity(error_entity):
    create_error_log(error_entity)
    return Response(
        response=json.dumps(error_entity),
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        mimetype='application/json'
    )

def handle_error(resp, status):
    if is_http_status_internal(resp.status_code):
        add_log_item(resp.json().get('message'))
        return create_response(status, resp.status_code, resp.json())
    else:
        add_log_item(resp.text)
        return create_response(status, resp.status_code, resp.text)

def get_response_error(resp):
    if is_http_status_internal(resp.status_code):
        return resp.json()
    else:
        return resp.text

# Return values:
# 1 - Connection error
# 2 - Internal error
def get_error_type(conn):
    if conn is None:
        return ApiErrorType.CONNECTION
    return ApiErrorType.INTERNAL
