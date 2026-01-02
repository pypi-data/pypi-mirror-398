def create_save_resp(status, status_code, response_msg):
    data = {}
    data['status'] = status
    data['statusCode'] = status_code
    data['responseMsg'] = response_msg
    return data
