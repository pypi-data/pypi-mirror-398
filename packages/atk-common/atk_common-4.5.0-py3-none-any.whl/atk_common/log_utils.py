from atk_common.datetime_utils import get_utc_date_time_str
from atk_common.http_utils import is_http_status_internal

def create_date_time():
    date_time = get_utc_date_time_str()
    return '[' + date_time + '] '

def add_log_item(text):
    print(create_date_time() + text)

def add_log_item_http(resp):
    if is_http_status_internal(resp.status_code):
        err_resp_json = resp.json().get('message')
        add_log_item(err_resp_json)
    else:
        add_log_item(resp.text)
