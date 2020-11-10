import pickle


import pandas as pd
import matplotlib.pyplot as plt

import copy
from src.methods.scenarios_for_users import create_scenario_table
from src.methods.PV_interface import get_PV_generated, get_PV_generated_from_pandas_row
from src.methods.helpers import validate_data, filter_good_users, soc2remainingCharge, remainingCharge2soc
from src.methods.loading_and_preprocessing import load_car_data, preprocess_car_data, load_baseline_car_data
from src.methods.compute_additional_columns import compute_additional_columns
from src.ecar_data_preprocessing import export_baseline_data
from src.db_login import DSN
from src.table_information import home_table_info, ecar_table_info, ecarid_athome_table_info

import datetime
import os
import numpy as np
from multiprocessing import Pool
import time



def test_solar_model_UTC():

    # sun rises in siwtzerland ~ 08:30 UTC + 1
    # we check that it is dark from 06:30 - 07:00 UTC and
    # that there is already some light 07:00 - 07:30 UTC
    vin = '00000dcb1a3963f3ae1d91cd9755b2d0'
    t_start = datetime.datetime(year=2017, month=1, day=1, hour=6, minute=30)
    t_end = t_start + datetime.timedelta(minutes=30)
    pvgen = get_PV_generated(t_start, t_end, vin)
    assert pvgen == 0, str(pvgen)

    t_start = datetime.datetime(year=2017, month=1, day=1, hour=7, minute=00)
    t_end = t_start + datetime.timedelta(minutes=30)

    pvgen = get_PV_generated(t_start, t_end, vin)
    assert pvgen  > 0, str(pvgen)

def test_partialy_covered_pvbands():
    # sunrise data https://galupki.de/kalender/sunmoon.php?jahrestabelle=HTML600&mobil=true&jahr=2017&monat=1&ort=Bonn&lon=7.1&lat=50.733

    vin = '00d98da128fd56261384c5a43da99ecf'

    # 60 minutes of pv generation
    t_start = datetime.datetime(year=2017, month=6, day=1, hour=14, minute=0)
    t_end = t_start + datetime.timedelta(hours=1)
    gen60 = get_PV_generated(t_start, t_end, vin)

    # 62 minutes of pv generation
    t_start = datetime.datetime(year=2017, month=6, day=1, hour=13, minute=59)
    t_end = t_start + datetime.timedelta(hours=1, minutes=1)
    gen62 = get_PV_generated(t_start, t_end, vin)

    # gen62 should only be a little bit larger than gen60
    assert gen62 > gen60
    assert gen62 * 0.9 < gen60


def test_max_charging_limitation():
    data_baseline = pd.read_csv(os.path.join('data', 'data_baseline.csv'))
    all_vins = data_baseline['vin'].unique()
    t_start = datetime.datetime(year=2017, month=6, day=1, hour=14, minute=0)
    t_end = t_start + datetime.timedelta(minutes=30)
    sum_no_limit = 0
    sum_limit = 0
    for vin in all_vins:
        try:
            sum_no_limit = sum_no_limit + get_PV_generated(t_start, t_end, vin)
            sum_limit = sum_limit + get_PV_generated(t_start, t_end, vin, max_power_kw=11)
        except (ValueError, FileNotFoundError):
            pass

    assert sum_no_limit > sum_limit
        # print(a)


def get_PV_generated_from_row(ix_row, max_power_kw=11):
    ix, row = ix_row
    try:
        return get_PV_generated(row['timestamp_start_utc'],
                                row['timestamp_end_utc'],
                                row['vin'], max_power_kw=max_power_kw)
    except (ValueError, FileNotFoundError):
        return -1


def test_mp_for_pv_generation():

    data_baseline = pd.read_csv(os.path.join('data', 'data_baseline.csv'))

    data_baseline['timestamp_start_utc'] = pd.to_datetime(data_baseline['timestamp_start_utc'])
    data_baseline['timestamp_end_utc'] = pd.to_datetime(data_baseline['timestamp_end_utc'])

    data_baseline = data_baseline[data_baseline['timestamp_start_utc'] >= datetime.datetime(year=2017, month=1, day=1)]
    data_baseline_sample = data_baseline.sample(1000)

    pvgen_singlecore = []
    t_before = time.time()
    for ix_row in data_baseline_sample.iterrows():
        pvgen_singlecore.append(get_PV_generated_from_row(ix_row))
    t_sc = time.time() - t_before

    t_before = time.time()
    with Pool(8) as pool:
        pvgen_mp = pool.map(get_PV_generated_from_row, data_baseline_sample.iterrows())
        pool.close()
        pool.join()

    t_mp = time.time() - t_before

    assert len(pvgen_singlecore) == len(pvgen_mp)

    print(t_sc, t_mp)
    for i in range(len(pvgen_mp)):
        assert np.isclose(pvgen_singlecore[i], pvgen_mp[i])

def test_and_write_baseline_data():
    file_out_baseline = os.path.join(".", "data", "data_baseline.csv")

    baseline_data = export_baseline_data(ecar_table_info, ecarid_athome_table_info, DSN)
    ix = baseline_data['timestamp_start_utc'] > baseline_data['timestamp_end_utc']
    assert baseline_data[ix].size == 0
    baseline_data.to_csv(file_out_baseline)

def test_new_filter_method():

    data_baseline2 = load_baseline_car_data(os.path.join('data', 'data_baseline.csv'))
    baseline_filtered_old = validate_data(data_baseline2, 'vin', os.path.join('.', 'data'))
    baseline_filtered_new = filter_good_users(data_baseline2, 'vin', os.path.join('.', 'data'))

    assert baseline_filtered_old.shape == baseline_filtered_new.shape

def test_inverse_soc2charge():
    soc_array = np.arange(0, 2.5, 100)

    for soc in soc_array:
        charge = soc2remainingCharge(soc)
        soc_from_charge = remainingCharge2soc(charge)
        assert np.isclose(soc, soc_from_charge, atol=0.001)

