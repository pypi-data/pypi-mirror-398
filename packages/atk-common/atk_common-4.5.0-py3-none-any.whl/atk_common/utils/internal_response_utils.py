from atk_common.enums.response_status_type_enum import ResponseStatusType

def create_response(status, status_code, response_msg, http_headers=None, content_type='application/json'):
    data = {}
    data['status'] = status
    data['statusCode'] = status_code
    data['responseMsg'] = response_msg
    data['httpHeaders'] = http_headers
    data['contentType'] = content_type
    return data

def is_response_ok(response):
    return response['status'] == ResponseStatusType.OK

def is_response_http(response):
    return response['status'] == ResponseStatusType.HTTP

def is_response_internal(response):
    return response['status'] == ResponseStatusType.INTERNAL
    
