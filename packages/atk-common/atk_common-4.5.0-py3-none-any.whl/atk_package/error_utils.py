from datetime import datetime
import json
from atk_common.datetime_utils import get_utc_date_time
from atk_common.log_utils import add_log_item
from atk_common.internal_response_utils import create_save_resp

def get_message(error):
    if hasattr(error, 'message'):
        return str(error.message)
    else:
        return str(error)

def get_error_entity(app, error, component, method, error_type, status_code):
    data = {}
    data['statusCode'] = status_code
    data['exceptionType'] = str(type(error))
    data['errorType'] = error_type
    data['message'] = get_message(error)
    data['component'] = component
    data['method'] = method
    data['timestamp'] = get_utc_date_time()
    return app.response_class(
        response=json.dumps(data),
        status=500,
        mimetype='application/json'
    )

def handle_error(resp, status):
    if resp.status_code == 500:
        add_log_item(resp.json().get('message'))
        return create_save_resp(status, resp.status_code, resp.json())
    else:
        add_log_item(resp.text)
        return create_save_resp(status, resp.status_code, resp.text)

def get_response_error(resp):
    if resp.status_code == 500:
        return resp.json()
    else:
        return resp.text

# Return values:
# 1 - Connection error
# 2 - Database error
def get_error_type(conn):
    if conn is None:
        return 1
    return 2
