import unittest

from jannik.methods.loading_and_preprocessing import load_car_data, preprocess_car_data
from jannik.methods.merge_PV_and_car import compute_additional_columns
from jannik.methods.scenarios_for_users import extract_user_data, scenario_1, create_scenario_table


class TestExtractUserData(unittest.TestCase):
    def setUp(self):
        self.filepath = 'toy_data\car_is_at_home_toy_data.csv'
        self.data = load_car_data(self.filepath)
        self.data = preprocess_car_data(self.data)

    def test_right_number_rows_selected(self):
        data_user_123 = extract_user_data(self.data, '123')
        print(data_user_123)
        self.assertTrue(len(data_user_123.index) == 2)

    def test_scenario_1_for_toy_data(self):
        filepath = 'toy_data\car_is_at_home_toy_data.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        supposed_coverage = (5.0 + 3.69635) / (22.486285 + 3.696350)
        computed_coverage = scenario_1(data_with_columns, "123")
        print(supposed_coverage)
        print(computed_coverage)

        self.assertAlmostEqual(supposed_coverage, computed_coverage)

    def test_create_table_does_not_crash(self):
        filepath = 'toy_data\car_is_at_home_toy_data.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        create_scenario_table(data_with_columns)