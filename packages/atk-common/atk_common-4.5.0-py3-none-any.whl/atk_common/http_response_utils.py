import json
from flask import Response
from http import HTTPStatus
from atk_common.enums.api_error_type_enum import ApiErrorType
from atk_common.utils.error_utils import get_error_entity, resend_error_entity
from atk_common.http_utils import is_http_status_internal, is_http_status_ok
from atk_common.internal_response_utils import is_response_http

def convert_response_data(data):
    if isinstance(data, dict):
        return json.dumps(data)
    elif isinstance(data, list):
        return json.dumps(data)
    elif isinstance(data, str):
        json_data = json.loads(data)
        return json.dumps(json_data)
    else:
        return data

# If response['status'] == 0 (OK, http status = 200): create Response and return response['responseMsg']   
# If http status == 500: 
#   If response['status'] == 1 (HTTP): resend received error entity
#   If response['status'] == 2 (INTERNAL): create new error entity and return as response
# If http status other value: create new error entity and return as response
def http_response(method, response, container_info):
    if is_http_status_ok(response['statusCode']):
        return Response(
            response=convert_response_data(response['responseMsg']),
            status=HTTPStatus.OK,
            mimetype=response['contentType'],
            headers=response['httpHeaders']
        )
    elif is_http_status_internal(response['statusCode']):
        if is_response_http(response):
            return resend_error_entity(response['responseMsg'])
        return get_error_entity(response['responseMsg'], method, ApiErrorType.INTERNAL, response['statusCode'], container_info)
    return get_error_entity(response['responseMsg'], method, ApiErrorType.CONNECTION, response['statusCode'], container_info)
