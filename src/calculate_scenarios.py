from src.methods.PV_interface import get_PV_generated_from_pandas_row
import copy
import logging
import os
from functools import partial
from multiprocessing import Pool

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.methods.PV_interface import get_PV_generated_from_pandas_row
from src.methods.compute_additional_columns import compute_additional_columns
from src.methods.helpers import filter_good_users
from src.methods.loading_and_preprocessing import load_car_data, preprocess_car_data, load_baseline_car_data
from src.methods.scenarios_for_users import create_scenario_table

logging.basicConfig(
    filename='calculate_scenarios.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')


def readFile(filename):
    filehandle = open(filename)
    print(filehandle.read())
    filehandle.close()


def prepare_baseline_data(filepath_baseline):
    """do the following preprocessing steps for the baseline data
    - load it (the function does already some user filtering
    - filter users based on manual validation table
    - transform timestamps to datetime objects
    - rename columns"""
    data_baseline = load_baseline_car_data(filepath_baseline)
    data_baseline = filter_good_users(data_baseline, 'vin', path_to_data_folder)

    data_baseline['timestamp_start_utc'] = pd.to_datetime(data_baseline['timestamp_start_utc'])
    data_baseline['timestamp_end_utc'] = pd.to_datetime(data_baseline['timestamp_end_utc'])
    data_baseline = data_baseline.rename(columns={'timestamp_start_utc': 'start', 'timestamp_end_utc': 'end',
                                                  'soc_customer_start': 'soc_start',
                                                  'soc_customer_end': 'soc_end'})

    return data_baseline


def get_cached_csv(filepath, data_raw, max_power_kw=11):
    data = data_raw.copy()
    baseline_cache_path = os.path.join(os.path.dirname(filepath), 'cache',
                                       os.path.basename(filepath) + '_pvgen_maxkw=' + str(max_power_kw) + '_cached.csv')

    if os.path.isfile(baseline_cache_path):
        logging.debug("\tload from cache")
        data = pd.read_csv(baseline_cache_path)
        data['start'] = pd.to_datetime(data['start'])
        data['end'] = pd.to_datetime(data['end'])

    else:
        logging.debug("\tStart pv calculation")
        data['start'] = pd.to_datetime(data['start'])
        data['end'] = pd.to_datetime(data['end'])

        get_PV_generated_from_pandas_row_partial = partial(get_PV_generated_from_pandas_row, max_power_kw=max_power_kw)
        with Pool(8) as pool:
            data['generated_by_pv'] = pool.map(get_PV_generated_from_pandas_row_partial, data.iterrows())
            pool.close()
            pool.join()
        logging.debug("\tfinished pv calculation")
        logging.debug("cache baseline to {}".format(baseline_cache_path))
        data.to_csv(baseline_cache_path, index=False)

    assert 'generated_by_pv' in data.columns

    return data


if __name__ == '__main__':
    # battery_capacity = 20
    battery_capacity = 13.5  # tesla power box.
    battery_charging_power = 12  # Dauerbetrieb
    max_power_kw = 11

    path_to_data_folder = os.path.join('.', 'data')

    filepath = os.path.join(path_to_data_folder, 'car_is_at_home_table_UTC.csv')
    filepath_baseline = os.path.join(path_to_data_folder, 'data_baseline.csv')

    logging.debug("read files")
    data_baseline = prepare_baseline_data(filepath_baseline)

    data = load_car_data(filepath)
    data = filter_good_users(data, 'vin', path_to_data_folder)

    # check cache
    logging.debug("get pv generation for baseline data")
    data_baseline = get_cached_csv(filepath_baseline, data_baseline, max_power_kw=max_power_kw)
    logging.debug("get pv generation for scenario 2 data")
    data = get_cached_csv(filepath, data, max_power_kw=max_power_kw)
    data_unrestricted = get_cached_csv(filepath, data, max_power_kw=10000)

    data['charged_from_pv_unrestricted'] = data_unrestricted['generated_by_pv']

    data_scenario_2 = copy.deepcopy(data)
    preprocessed_data = copy.deepcopy(data)

    # - remove all entries where user is not at home
    # - compute the charged energy (delta SOC per segment)
    preprocessed_data = preprocess_car_data(preprocessed_data)
    data_with_columns = compute_additional_columns(preprocessed_data, path_to_data_folder, battery_charging_power)

    table = create_scenario_table(data_baseline, data_scenario_2, data_with_columns, battery_capacity,
                                  battery_charging_power, path_to_data_folder)
    print("done, start plotting")
    table.to_csv(os.path.join('data', 'table_validated.csv'))

    plt.xlim(0, 1)
    sns.distplot(table['Baseline'], hist=False, rug=True)
    plt.title("Scenario Baseline - mean {:.2f}".format(table['Baseline'].mean()))
    # print(f"mean: {np.mean(table['Scenario 1'])}")
    plt.savefig(os.path.join('plots', 'Baseline_PV_model'))
    plt.close()

    plt.xlim(0, 1)
    sns.distplot(table['Scenario 1'], hist=False, rug=True)
    plt.title("Scenario 1 - mean {:.2f}".format(table['Scenario 1'].mean()))
    print(f"mean: {np.mean(table['Scenario 1'])}")
    plt.savefig(os.path.join('plots', 'Scenario 1_PV_model'))
    plt.close()

    plt.xlim(0, 1)
    sns.distplot(table['Scenario 2'], hist=False, rug=True)
    plt.title("Scenario 2 - mean {:.2f}".format(table['Scenario 2'].mean()))
    plt.savefig(os.path.join('plots', 'Scenario 2_PV_model'))
    plt.close()

    plt.xlim(0, 1)
    sns.distplot(table['Scenario 3'], hist=False, rug=True)
    plt.title("Scenario 3 - mean {:.2f}".format(table['Scenario 3'].mean()))
    plt.savefig(os.path.join('plots', 'Scenario 3_PV_model_validated'))
    plt.close()
