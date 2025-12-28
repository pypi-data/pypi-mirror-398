import unittest
from unittest.mock import Mock, patch
from crossmark_jotform_api.utils import fix_query_key


class TestUtils(unittest.TestCase):

    def test_fix_query_key_adds_q_prefix(self):
        """Test that fix_query_key adds 'q' prefix when missing"""
        result = fix_query_key("3:matches")
        self.assertEqual(result, "q3:matches")

    def test_fix_query_key_keeps_existing_q_prefix(self):
        """Test that fix_query_key keeps existing 'q' prefix"""
        result = fix_query_key("q3:matches")
        self.assertEqual(result, "q3:matches")

    def test_fix_query_key_empty_string(self):
        """Test fix_query_key with empty string"""
        result = fix_query_key("")
        self.assertEqual(result, "q")


if __name__ == "__main__":
    unittest.main()
