import unittest
import numpy as np

from jannik.methods.helpers import soc2remainingCharge
from jannik.methods.loading_and_preprocessing import load_car_data, preprocess_car_data
from jannik.methods.merge_PV_and_car import compute_additional_columns


class TestMergePVAndCar(unittest.TestCase):
    def setUp(self):
        self.filepath = 'toy_data\car_is_at_home_toy_data.csv'

    def test_adding_columns_does_not_crash(self):
        data = load_car_data(self.filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        print(data_with_columns)

    def test_adding_columns_produces_correct_car_energy_demand(self):
        data = load_car_data(self.filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        supposed = [soc2remainingCharge(30), soc2remainingCharge(90), soc2remainingCharge(80)]
        demand = data_with_columns['needed_by_car']
        print(demand)
        print(supposed)
        self.assertTrue(np.all(supposed == demand))

    def test_adding_columns_no_more_energy_is_charged_from_PV_than_needed_or_generated_from_PV(self):
        data = load_car_data(self.filepath)
        preprocessed_data = preprocess_car_data(data)
        data_with_columns = compute_additional_columns(preprocessed_data)
        demand = data_with_columns['needed_by_car']
        generated = data_with_columns['generacted_by_PV']
        charged = data_with_columns['charged_from_PV']
        self.assertTrue(np.all(charged <= generated))
        self.assertTrue(np.all(charged <= demand))