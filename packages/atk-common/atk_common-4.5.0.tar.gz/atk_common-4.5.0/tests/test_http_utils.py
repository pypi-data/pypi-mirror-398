import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from atk_common.utils import *
from atk_common.enums import *

class TestHttpUtils(unittest.TestCase):

    def test_get_test_response_none(self):
        resp_json = get_test_response(None, 'bo-config-db-api')
        self.assertIsNotNone(resp_json)

if __name__ == "__main__":
    unittest.main()
