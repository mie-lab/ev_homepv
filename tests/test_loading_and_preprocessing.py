import unittest
import numpy as np

from src.methods.loading_and_preprocessing import load_car_data, preprocess_car_data

class TestLoadingAndPreprocessingCarData(unittest.TestCase):
    def setUp(self):
        self.directory_path = 'toy_data\PV_data'
        self.filepath = 'toy_data\car_is_at_home_toy_data.csv'

    def test_load_data_and_preprocess_car_data(self):
        data = load_car_data(self.filepath)
        print(f"data_PV_Solar: {data}")
        preprocessed_data = preprocess_car_data(data)
        print(len(preprocessed_data.columns))
        self.assertTrue(len(preprocessed_data.columns) == 7)
        print(preprocessed_data['delta_soc'])
        self.assertTrue(np.all(preprocessed_data['delta_soc'] == [70, 30, 20]))

""" Do not touch PV data_PV_Solar in this paper

    def test_load_PV_data(self):
        PV_data = load_PV_data(self.directory_path)
        print(PV_data)
        print(PV_data.columns)
        self.assertTrue(len(PV_data.index) == 96*3)
        #self.assertTrue(len(PV_data.columns) == 5)#index, househod_id, starttime, endtime, energy

    def test_load_and_preprocess_data(self):
        PV_data = load_PV_data(self.directory_path)
        PV_data_preprocessed = preprocess_PV_data(PV_data)
        self.assertTrue(len(PV_data_preprocessed.index) == 96 * 3)
        self.assertTrue(len(PV_data_preprocessed.columns) == 5)#index, househod_id, starttime, endtime, energy
"""

