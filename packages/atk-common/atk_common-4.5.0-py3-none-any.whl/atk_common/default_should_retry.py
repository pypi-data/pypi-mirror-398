from atk_common.enums.api_error_type_enum import ApiErrorType
from atk_common.enums.response_status_type_enum import ResponseStatusType
from atk_common.http_utils import is_http_status_internal, is_http_status_ok

def default_should_retry(message_status):
    if message_status['status'] == ResponseStatusType.HTTP:
        status_code = message_status['statusCode']
        if is_http_status_ok(status_code):
            return False
        elif is_http_status_internal(status_code):
            #errorType = 1: connection error
            #errorType = 2: api internal error (database, etc)
            if message_status['responseMsg']['errorType'] == ApiErrorType.CONNECTION.value:
                return True
            else:
                return False
        else:
            return True
    return True