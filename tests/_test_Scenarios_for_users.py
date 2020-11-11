import unittest
import pandas as pd

from src.methods.PV_interface import get_PV_generated
from src.methods.helpers import soc2remainingCharge
from src.methods.loading_and_preprocessing import load_car_data, preprocess_car_data
from src.methods.compute_additional_columns import compute_additional_columns
from src.methods.scenarios_for_users import extract_user_data, scenario_1, create_scenario_table, scenario_2, \
    scenario_3


class TestExtractUserData(unittest.TestCase):
    def setUp(self):
        self.filepath = 'toy_data\car_is_at_home_toy_data.csv'
        self.data = load_car_data(self.filepath)
        self.data = preprocess_car_data(self.data)
        self.battery_capacity = 10

    def test_right_number_rows_selected(self):
        data_user_123 = extract_user_data(self.data, '123')
        print(data_user_123)
        self.assertTrue(len(data_user_123.index) == 2)

    def test_scenario_1_for_toy_data(self):
        filepath = 'toy_data\car_is_at_home_toy_data.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 500)
        print(data_with_columns)
        supposed_coverage = (5.0 + 5.) / (22.486285 + 10.102422)
        computed_coverage = scenario_1(data_with_columns, "123")
        print(supposed_coverage)
        print(computed_coverage)

        self.assertAlmostEqual(supposed_coverage, computed_coverage)

    def test_create_table_does_not_crash(self):
        filepath = 'toy_data\car_is_at_home_toy_data.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        table = create_scenario_table(data_with_columns, self.battery_capacity)
        print(table)

    def test_only_one_entry_yields_same_result_for_all_scenarios(self):
        filepath = 'toy_data\car_is_at_home_toy_data.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        table = create_scenario_table(data_with_columns, self.battery_capacity)

        print(table)
        self.assertAlmostEqual(table['Scenario 1'][456], table['Scenario 3'][456])

    def test_correct_result_for_scenario_1(self):
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 500)
        filepath = 'toy_data\car_is_at_home_toy_data_for_scenarios.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        result_scenario_1 = scenario_1(data_with_columns, '123')
        true_total_demand = soc2remainingCharge(30) + soc2remainingCharge(50)
        true_charge_from_PV = 10
        true_coverage = true_charge_from_PV / true_total_demand
        self.assertAlmostEqual(true_coverage, result_scenario_1)

    def test_correct_result_for_scenario_2(self):
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 500)
        filepath = 'toy_data\car_is_at_home_toy_data_for_scenarios.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)

        result_scenario_2 = scenario_2(data_with_columns, '123')
        true_total_demand = soc2remainingCharge(30) + soc2remainingCharge(50)
        total_charged_from_outside = 0
        true_coverage = 1- total_charged_from_outside / true_total_demand
        self.assertAlmostEqual(true_coverage, result_scenario_2)

    def test_correct_result_for_scenario_3(self):
        battery_capacity = 10
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 500)
        filepath = 'toy_data\car_is_at_home_toy_data_for_scenarios.csv'
        data = load_car_data(filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)

        result_scenario_3 = scenario_3(data_with_columns, '123', battery_capacity)
        true_total_demand = soc2remainingCharge(30) + soc2remainingCharge(50)
        charged_from_outside_1 = soc2remainingCharge(30) - get_PV_generated(data_with_columns["start"][0], data_with_columns["start"][0], 2)
        charged_from_outside_2 = 0
        charged_from_outside_3 = soc2remainingCharge(50) - battery_capacity - get_PV_generated(data_with_columns["start"][0], data_with_columns["start"][0], 2)

        total_charged_from_outside = charged_from_outside_1 + charged_from_outside_2 + charged_from_outside_3
        true_coverage = 1 - total_charged_from_outside / true_total_demand
        print(result_scenario_3)
        self.assertAlmostEqual(true_coverage, result_scenario_3)