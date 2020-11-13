import unittest

from src.methods.helpers import get_user_id

class TestHelpers(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_user_id_in_first_line_of_table(self):
        user_id = str(get_user_id("004c4ba86e77149b9bfe2dfebb4057a4"))
        print(user_id)
        self.assertTrue(user_id == "1665")

    def test_user_with_duplicate_entries(self):
        user_id = str(get_user_id("00000dcb1a3963f3ae1d91cd9755b2d0"))
        print(user_id)
        self.assertTrue(user_id == "1598")