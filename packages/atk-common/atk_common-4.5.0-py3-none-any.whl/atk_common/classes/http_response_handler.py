import json
from flask import Response
from http import HTTPStatus
from atk_common.enums.api_error_type_enum import ApiErrorType
from atk_common.utils.http_utils import is_http_status_internal, is_http_status_ok
from atk_common.utils.internal_response_utils import is_response_http
from atk_common.interfaces import IErrorHandler, ILogger
from atk_common.interfaces import IHttpResponseHandler

class HttpResponseHandler(IHttpResponseHandler):
    def __init__(self, logger: ILogger, error_handler: IErrorHandler):
        self.error_handler = error_handler
        self.logger = logger

    def _convert_response_data(self, data):
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
    def http_response(self, method, response):
        self.logger.debug(f'http_response: method={method}, statusCode={response.get('statusCode')}')
        if is_http_status_ok(response.get('statusCode')):
            return Response(
                response=self._convert_response_data(response.get('responseMsg')),
                status=HTTPStatus.OK,
                mimetype=response.get('contentType'),
                headers=response.get('httpHeaders')
            )
        elif is_http_status_internal(response.get('statusCode')):
            if is_response_http(response):
                return self.error_handler.resend_error_entity(response.get('responseMsg'))
            return self.error_handler.get_error_entity(response.get('responseMsg'), method, ApiErrorType.INTERNAL, response.get('statusCode'))
        return self.error_handler.get_error_entity(response.get('responseMsg'), method, ApiErrorType.CONNECTION, response.get('statusCode'))
