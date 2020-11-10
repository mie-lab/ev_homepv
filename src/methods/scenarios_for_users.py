import copy

import pandas as pd
import numpy as np
import sys

from src.methods.PV_interface import get_PV_generated, get_max_pv_charged
from src.methods.helpers import soc2remainingCharge
import warnings

def extract_user(data, vin):
    """
    Extracts part of the preprocessed dataframe that belongs to the selected user.

    Parameters
    ----------
    data: pandas df
        dataframe to be selected from
    user: string
        userID/vin to be selected from

    Returns
    -------
    datacopy: pandas df
        data_PV_Solar with rows selected

    """
    assert isinstance(vin, str)
    return data[data['vin'] == vin].copy()

def baseline(data_baseline, user, max_kw_per_hour, path_to_data_folder):
    # print(f"\tbaseline called for user {user}")
    user_data = extract_user(data_baseline, user)
    user_data = user_data.sort_values(by=['start'])


    # user_data = user_data.drop(user_data[user_data['is_home'] != 'True'].index)

    needed_by_car = [soc2remainingCharge(user_data["soc_start"][user_data.index[i]]) -
                                        soc2remainingCharge(user_data["soc_end"][user_data.index[i]])
                                        for i in range(len(user_data.index))]
    needed_by_car = np.maximum(0, needed_by_car)
    user_data['needed_by_car'] = needed_by_car

    charged_from_pv = [np.minimum(user_data['generated_by_pv'][user_data.index[i]],
                                user_data['needed_by_car'][user_data.index[i]])
                                for i in range(len(user_data.index))]
    
    
    assert np.all(np.array(charged_from_pv) >= 0)
    user_data['charged_from_pv'] = charged_from_pv
    
    # user_data.to_csv("debug_user_data_baseline.csv")
    
    user_data_ishome = user_data[user_data['is_home']]

    total_charged = sum(user_data_ishome['charged_from_pv'])
    total_demand = sum(user_data_ishome['needed_by_car'])
    
    if total_demand != 0:
        coverage = total_charged / total_demand
    else:
        return None

    assert 0 <= coverage <= 1
    return coverage


def scenario_1(data, user):
    """
    Computes weighted average fraction of self-produced energy that is being charged.

    Parameters
    ----------
    data: pandas df
        dataframe to be selected from
    user: string
        userID/vin to be selected from

    Returns
    -------
    coverage: float
        computed average charge covered by own PV production
    """
    # print(f"\tscenario 1 called for user {user}")
    user_data = extract_user(data, user)

    total_charged = sum(user_data['charged_from_pv'])
    total_demand = sum(user_data['needed_by_car'])

    if(total_demand == 0):
        print(f'\t\tuser with zero demand: {user}')

    coverage = total_charged / total_demand

    assert 0<= coverage <= 1
    return coverage

def scenario_2(data, user, max_charging_power):
    """
    Computes fraction when Energy can be charged, but does not have to be equal to real user data_PV_Solar.

    Parameters
    ----------
    data: pandas df
        dataframe to be selected from
    user: string
        userID/vin to be selected from

    Returns
    -------
    coverage: float
        computed average charge covered by own PV production
    """
    # print(f"\tscenario 2 called for user {user}")
    user_data = extract_user(data, user)
    user_data['start'] = pd.to_datetime(user_data['start'])
    user_data['end'] = pd.to_datetime(user_data['end'])
    user_data = user_data.sort_values('start')
    user_data['kWh_start'] = [0.] * len(user_data.index)

    user_data['total_segment_consumption_kWh'] = \
        [soc2remainingCharge(0) -
         soc2remainingCharge(user_data['total_segment_consumption'][user_data.index[i]])
         for i in range(len(user_data.index))]


    user_data['kWh_end'] = [0.] * len(user_data.index)
    user_data['charged_from_outside'] = [0.] * len(user_data.index)
    user_data['max_kWh'] = [soc2remainingCharge(0)] * len(user_data.index)
    relevant_columns = ['kWh_start', 'start', 'end', 'is_home', 'kWh_end', 'total_segment_consumption_kWh',
                        'generated_by_pv', 'max_kWh', 'charged_from_outside']
    user_data = user_data[relevant_columns]

    for i in range(len(user_data.index)):
        ix = user_data.iloc[i].name
        if i != 0:
            user_data.loc[ix, 'kWh_start'] = user_data['kWh_end'].iloc[i-1] # end has to be updated wiht the consumptions of the other segments

        # load from outside if necessary
        if user_data['kWh_start'].iloc[i] < 0:
            user_data.loc[ix, 'charged_from_outside'] = - user_data['kWh_start'].iloc[i]
            user_data.loc[ix, 'kWh_start'] = 0

        if user_data['is_home'].iloc[i]:
            # load from PV
            charging = np.minimum(user_data['generated_by_pv'].iloc[i],
                                  get_max_pv_charged(user_data['start'].iloc[i],
                                                     user_data['end'].iloc[i],
                                                     max_charging_power))

            user_data.loc[ix, 'kWh_end'] = np.minimum(user_data['max_kWh'].iloc[i],
                                                   user_data['kWh_start'].iloc[i]
                                                      + charging
                                                      + user_data['total_segment_consumption_kWh'].iloc[i])
        else:
            # if not at home, just consume
            user_data.loc[ix, 'kWh_end'] = user_data['kWh_start'].iloc[i] \
                                           + user_data['total_segment_consumption_kWh'].iloc[i]

    assert np.all(user_data['charged_from_outside'] >=0)
    assert np.all(user_data['total_segment_consumption_kWh'] <= 0)
    total_charged_from_outside = sum(user_data['charged_from_outside'])
    total_demand = - sum(user_data['total_segment_consumption_kWh'])
    coverage = 1 - (total_charged_from_outside / total_demand)
    assert 0 <= coverage <= 1

    return coverage, total_demand


def scenario_3(data, user, battery_capacity, path_to_data_folder, max_charging_power):
    """
    Computes fraction of self-produced energy when there is a battery at home for use with a given maximal capacity.

    Parameters
    ----------
    data: pandas df
        dataframe to be selected from
    user: string
        userID/vin to be selected from
    battery_capacity: float
        maximum battery capacity

    Returns
    -------
    coverage: float
        computed average charge covered by own PV production
    """
    # print(f"\tscenario 3 called for user {user}")
    user_data = extract_user(data, user)
    user_data['battery_end_of_timestamp'] = [0.] * len(user_data.index)
    user_data['charged_from_outside'] = [0.] * len(user_data.index)
    user_data['start'] = pd.to_datetime(user_data['start'])
    user_data['end'] = pd.to_datetime(user_data['end'])
    user_data = user_data.sort_values('start')
    for i in range(len(user_data.index)):
        ix = user_data.iloc[i].name
        battery_beginning = 0.
        if i > 0:
            battery_beginning = np.minimum(battery_capacity, user_data['battery_end_of_timestamp'][user_data.index[i-1]] + \
                                get_PV_generated(user_data['end'][user_data.index[i-1]], user_data['start'][user_data.index[i]], user, path_to_data_folder))

        charging = np.minimum(user_data['generated_by_pv'][user_data.index[i]],
                              get_max_pv_charged(user_data['start'].iloc[i],
                                                 user_data['end'].iloc[i], max_charging_power))
        user_data.loc[user_data.index[i], 'charged_from_outside'] =  \
            np.maximum(0., user_data['needed_by_car'][user_data.index[i]]
                        - charging - battery_beginning)

        user_data.loc[user_data.index[i], 'battery_end_of_timestamp'] = \
                            np.minimum(battery_capacity, battery_beginning
                                       + user_data['generated_by_pv'][user_data.index[i]]
                                       + user_data['charged_from_outside'][user_data.index[i]]
                                       - user_data['needed_by_car'][user_data.index[i]])

    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)

    total_charged_from_outside = sum(user_data['charged_from_outside'])
    total_demand = sum(user_data['needed_by_car'])
    coverage = 1 - (total_charged_from_outside / total_demand)

    # user_data.to_csv("debug_scenario_3.csv")

    return coverage

def create_scenario_table(data_baseline, data_scenario_2, data, capacity, max_power_kw, path_to_data_folder):
    """
    Creates a dataframe that contains coverage in all different scenarios

    Parameters
    ----------
    data: pd-dataframe
        dataframe to extract information from
    capacity: float
        maximum batteriy capacity

    Returns
    -------

    table: pandas-df
        table with the three scenarios
    """
    user_list = list(set(data["vin"]))
    # user_list = ['00d98da128fd56261384c5a43da99ecf',]
    # warnings.warn("using single user filter")
    #print(user_list)
    print("baseline")
    scenario_baseline_list = [baseline(data_baseline, str(user_list[i]), max_power_kw, path_to_data_folder) for i in range(len(user_list))]
    print("scenario 1")
    scenario_1_list = [scenario_1(data, str(user_list[i])) for i in range(len(user_list))]
    print("scenario 2")
    scenario_2_outcome = [scenario_2(data_scenario_2, str(user_list[i]), max_power_kw) for i in range(len(user_list))]
    scenario_2_outcome = np.array(scenario_2_outcome)
    scenario_2_list = scenario_2_outcome[:,0]
    total_demand_list = scenario_2_outcome[:,1]

    print("scenario 3")
    scenario_3_list = [scenario_3(data, str(user_list[i]), capacity, path_to_data_folder, max_power_kw) for i in range(len(user_list))]



    list_of_tuples = list(zip(scenario_baseline_list, scenario_1_list, scenario_2_list, scenario_3_list, total_demand_list))
    table = pd.DataFrame(list_of_tuples, index=user_list,
                         columns=["Baseline", "Scenario 1", "Scenario 2", "Scenario 3", "Total Demand"])

    # print(f"table: {table}")
    # print(np.array(scenario_3_list) >= np.array(scenario_1_list))
    assert np.all(np.array(scenario_3_list) >= np.array(scenario_1_list)-0.000001)

    return table


