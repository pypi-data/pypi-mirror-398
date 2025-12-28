import unittest
from unittest.mock import patch, mock_open
from test_configs import bad_conf_1, bad_conf_2, good_conf
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kolzchut_ragbot import Document


class MyTestCase(unittest.TestCase):


    @patch("builtins.open", mock_open(read_data=bad_conf_1))
    def test_wrong_identifier(self):
        should_raise = True
        did_raise = False
        try:
            Document.initialize_definitions()
        except ValueError as e:
            did_raise = True
            print(e)
        self.assertEqual(should_raise, did_raise)  # add assertion here

    @patch("builtins.open", mock_open(read_data=bad_conf_2))
    def test_wrong_vector(self):
        should_raise = True
        did_raise = False
        try:
            Document.initialize_definitions()
        except ValueError as e:
            did_raise = True
            print(e)
        self.assertEqual(should_raise, did_raise)  # add assertion here

    @patch("builtins.open", mock_open(read_data=good_conf))
    def test_something(self):
        should_raise = False
        did_raise = False
        try:
            Document.initialize_definitions()
        except Exception as e:
            did_raise = True
            print(e)
        self.assertEqual(should_raise, did_raise)  # add assertion here


if __name__ == '__main__':
    unittest.main()
