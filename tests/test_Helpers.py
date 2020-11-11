import unittest
import os

from src.methods.helpers import get_user_id, validate_data, filter_good_users
from src.methods.loading_and_preprocessing import load_baseline_car_data

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


def test_new_filter_method():
    data_baseline2 = load_baseline_car_data(os.path.join('data', 'data_baseline.csv'))
    baseline_filtered_old = validate_data(data_baseline2, 'vin', os.path.join('.', 'data'))
    baseline_filtered_new = filter_good_users(data_baseline2, 'vin', os.path.join('.', 'data'))

    assert baseline_filtered_old.shape == baseline_filtered_new.shape