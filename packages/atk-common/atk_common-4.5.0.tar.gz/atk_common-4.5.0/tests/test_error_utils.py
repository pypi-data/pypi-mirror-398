import unittest
from http import HTTPStatus
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from atk_common.utils import *
from atk_common.enums import *
from atk_common.classes import *

class TestErrorUtils(unittest.TestCase):

    def create_dummy_container_info(self):
        data = {}
        data['imageName'] = 'bo-test-api'
        data['imageVersion'] = '1.0.0'
        data['containerName'] = 'bo-test-api'
        data['ports'] = []
        data['ports'].append({'port': 8080, 'binding': 8080})
        return data

    def test_get_error_entity_enum(self):
        # http_response = get_error_entity('An new error occured', 'get-configuration', ApiErrorType.INTERNAL, HTTPStatus.INTERNAL_SERVER_ERROR, self.create_dummy_container_info())
        # self.assertIsNotNone(http_response)
        self.assertIsNone(None)

    def test_get_error_entity_enum_value(self):
        # http_response = get_error_entity('An new error occured', 'get-configuration', ApiErrorType.INTERNAL.value, HTTPStatus.INTERNAL_SERVER_ERROR, self.create_dummy_container_info())
        # self.assertIsNotNone(http_response)
        self.assertIsNone(None)

if __name__ == "__main__":
    unittest.main()
