import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from atk_common.utils import *
from atk_common.enums import *

class TestLogUtils(unittest.TestCase):
    
    def test_add_log_item(self):
        add_log_item("Test message")

if __name__ == "__main__":
    unittest.main()
