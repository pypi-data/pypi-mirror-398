import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from atk_common.utils import *
from atk_common.enums import *

class TestDockerUtils(unittest.TestCase):

    def test_get_container_info(self):
        info = get_current_container_info()
        self.assertIsNone(info)

if __name__ == "__main__":
    unittest.main()
