import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import datetime
import pytest
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from src.methods.helpers import soc2remainingCharge
from src.methods.PV_interface import get_PV_generated


def parse_dates(data_raw):
    data = data_raw.copy()
    data['start'] = pd.to_datetime(data['start'])
    data['end'] = pd.to_datetime(data['end'])

    return data


output_folder = os.path.join('.', 'data', 'output')

baseline = pd.read_csv(os.path.join(output_folder, 'results_baseline.csv'))
baseline = parse_dates(baseline)

scenario1 = pd.read_csv(os.path.join(output_folder, 'results_scenario1.csv'))
scenario1 = parse_dates(scenario1)

scenario2 = pd.read_csv(os.path.join(output_folder, 'results_scenario2.csv'))
scenario2 = parse_dates(scenario2)

scenario3 = pd.read_csv(os.path.join(output_folder, 'results_scenario3.csv'))
scenario3 = parse_dates(scenario3)


def test_consumption_sc23():
    d2 = scenario2.copy()
    d3 = scenario3.copy()

    print(d2['needed_by_car'].sum(), d3['needed_by_car'].sum())

    assert True

def test_consumption_scb13():
    b = baseline.copy()
    d1 = scenario1.copy()

    print(b['needed_by_car'].sum() - d1['needed_by_car'].sum())

def test_if_same_users():
    baseline_data = baseline.copy()
    data = scenario1.copy()
    vins_baseline = baseline_data['vin'].unique()
    vins_data = data['vin'].unique()

    for ix, vin_b in enumerate(vins_baseline):
        assert vin_b == vins_data[ix]
