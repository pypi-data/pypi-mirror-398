from http import HTTPStatus
from atk_common.datetime_utils import get_utc_date_time_str

def is_http_status_ok(status_code):
    return status_code >= HTTPStatus.OK.value and status_code < HTTPStatus.MULTIPLE_CHOICES.value

def is_http_status_internal(status_code):
    return status_code >= HTTPStatus.INTERNAL_SERVER_ERROR.value

def get_test_response(docker_container_data, component):
    data = {}
    data['utcDateTime'] = get_utc_date_time_str()
    if docker_container_data is None:
        data['containerData'] = None
        data['component'] = component
    else:
        data['containerData'] = docker_container_data
    return data
