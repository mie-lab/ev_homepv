import copy

import pandas as pd
import numpy as np

from src.methods.PV_interface import get_PV_generated, get_max_pv_charged
from src.methods.helpers import soc2remainingCharge


def extract_user_data(data, user):
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
    datacopy = copy.deepcopy(data)
    datacopy['vin'] = datacopy['vin'].astype(str)
    datacopy= datacopy.drop(datacopy[datacopy['vin'] != user].index)
    return datacopy

def baseline(data_baseline, user, max_kw_per_hour, path_to_data_folder):
    print(f"baseline called for user {user}")
    user_data = extract_user_data(data_baseline, user)
    user_data = user_data.sort_values(by=['timestamp'])

    user_data = user_data.rename(columns={"timestamp": "start"})
    user_data['end'] = [user_data['start'][user_data.index[i+1]] if i < len(user_data.index)-1 else 0 for i in range(len(user_data.index))]
    user_data['soc_start'] = [user_data['soc'][user_data.index[i]] for i in
                        range(len(user_data.index))]
    user_data['soc_end'] = [user_data['soc_start'][user_data.index[i + 1]] if i < len(user_data.index) - 1 else 0 for i in
                        range(len(user_data.index))]
    user_data.drop(user_data.tail(1).index,inplace=True) #drop last entry as end time is not known


    relevant_columns = ['vin', 'start', 'soc_start', 'is_home', 'end', 'soc_end', 'zustand']
    if filter:
        user_data = user_data[relevant_columns]



#    user_data['end'] += pd.Timedelta(pd.offsets.Second(1))


    user_data['zustand'] = user_data['zustand'].astype(str)
    user_data = user_data.drop(user_data[user_data['zustand'] != 'laden'].index)
    user_data['is_home'] = user_data['is_home'].astype(str)
    user_data = user_data.drop(user_data[user_data['is_home'] != 'True'].index)


    user_data["generated_by_PV"] = [get_PV_generated(user_data["start"][user_data.index[i]],
                                                         user_data["end"][user_data.index[i]],
                                                         user_data["vin"][user_data.index[i]], path_to_data_folder
                                                         ) for i in range(len(user_data.index))]

    needed_by_car = [soc2remainingCharge(user_data["soc_start"][user_data.index[i]]) -
                     soc2remainingCharge(user_data["soc_end"][user_data.index[i]])
                     for i in range(len(user_data.index))]
    needed_by_car = np.maximum(0, needed_by_car)
    #needed_by_car = np.maximum(0, needed_by_car)
    user_data['needed_by_car'] = needed_by_car
    relevant_columns = [ 'soc_start', 'soc_end', 'zustand', 'needed_by_car', 'generated_by_PV']

    charged_from_pv_raw = [np.minimum(user_data['generated_by_PV'][user_data.index[i]],
                                  user_data['needed_by_car'][user_data.index[i]])
                       for i in range(len(user_data.index))]

    #print(f"data 1:{type(user_data['generated_by_PV'][user_data.index[1]])}")
    #print(f"data 2:{type(get_max_pv_charged(user_data['start'][user_data.index[1]], user_data['end'][user_data.index[1]], max_kw_per_hour))}")
    #print(np.minimum(user_data['generated_by_PV'][user_data.index[1]],
    #                                  user_data['needed_by_car'][user_data.index[1]],
    #                                  get_max_pv_charged(user_data['start'][user_data.index[1]], user_data['end'][user_data.index[1]], max_kw_per_hour)))
    #charged_from_pv_new = [np.minimum(user_data['generated_by_PV'][user_data.index[i]],
    #                                  user_data['needed_by_car'][user_data.index[i]],
    #                                  get_max_pv_charged(user_data['start'][user_data.index[i]], user_data['end'][user_data.index[i]], max_kw_per_hour)) for i in range(len(user_data.index))]

    charged_from_pv_raw = np.maximum(0, charged_from_pv_raw)
    charged_from_pv = [np.minimum(charged_from_pv_raw[i],
                                  get_max_pv_charged(user_data['start'][user_data.index[i]], user_data['end'][user_data.index[i]], max_kw_per_hour))
                       for i in range(len(user_data.index))]

    #print(charged_from_pv_raw[0:10])
    #print(charged_from_pv[0:10])




    assert (np.all(np.array(charged_from_pv) >= 0))
    user_data['charged_from_PV'] = charged_from_pv

    total_charged = sum(user_data['charged_from_PV'])
    total_demand = sum(user_data['needed_by_car'])
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
    print(f"scenario 1 called for user {user}")
    user_data = extract_user_data(data, user)
    #print(user_data)


    total_charged = sum(user_data['charged_from_PV'])
    total_demand = sum(user_data['needed_by_car'])
    #print(user_data)
    #print(total_demand)
    if(total_demand == 0):
        print(f'user with zero demand: {user}')

    print(f"user: {user}")
    print(f"total charged: {total_charged}")
    print(f"total demand: {total_demand}")
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
    print(f"scenario 2 called for user {user}")
    user_data = extract_user_data(data, user)
    user_data['start'] = pd.to_datetime(user_data['start'])
    user_data['end'] = pd.to_datetime(user_data['end'])
    user_data = user_data.sort_values('start')
    user_data['kWh_start'] = [0.] * len(user_data.index)
    #user_data['kWh_start'][user_data.index[0]] = soc2remainingCharge(0) - soc2remainingCharge(
    #    user_data['soc_start'][user_data.index[0]])

    user_data['total_segment_consumption_kWh'] = [soc2remainingCharge(0) - soc2remainingCharge(user_data['total_segment_consumption'][user_data.index[i]] )for i in range(len(user_data.index))]


    user_data['kWh_end'] = [0.] * len(user_data.index)
    user_data['charged_from_outside'] = [0.] * len(user_data.index)
    user_data['max_kWh'] = [soc2remainingCharge(0)] * len(user_data.index)
    #user_data['MwH_needed_during_next_trip'] = [0.] * len(user_data.index)
    #relevant_columns = ['start', 'kWh_start', 'is_home', 'end', 'kWh_end', 'total_segment_consumption_kWh', 'generated_by_PV']
    relevant_columns = ['kWh_start', 'start', 'end', 'is_home', 'kWh_end', 'total_segment_consumption_kWh',
                        'generated_by_PV', 'max_kWh', 'charged_from_outside']
    user_data = user_data[relevant_columns]
    print(user_data)



    for i in range(len(user_data.index)):
        if i != 0:
            user_data['kWh_start'].iloc[i] = user_data['kWh_end'].iloc[i-1]
        #print(user_data['is_home'])
        #print(user_data['kWh_start'])
        #print(type(user_data['is_home'].iloc[i]))
        # load from outside if necessary
        if user_data['kWh_start'].iloc[i] < 0:
            user_data['charged_from_outside'].iloc[i] = -user_data['kWh_start'].iloc[i]
            user_data['kWh_start'].iloc[i] = 0

        if user_data['is_home'].iloc[i]:
            # load from PV
            charging = np.minimum(user_data['generated_by_PV'].iloc[i], get_max_pv_charged(user_data['start'].iloc[i], user_data['end'].iloc[i], max_charging_power))
            #print(f"difference: {chargeable - user_data['generated_by_PV'].iloc[i]}")
            user_data['kWh_end'].iloc[i] = np.minimum(user_data['max_kWh'].iloc[i],
                                                   user_data['kWh_start'].iloc[i] + charging + user_data['total_segment_consumption_kWh'].iloc[i])
        else:
            # if not at home, just consume
            user_data['kWh_end'].iloc[i] = user_data['kWh_start'].iloc[i] + user_data['total_segment_consumption_kWh'].iloc[i]

    #print(user_data.head(5))
    #print(user_data.tail(5))

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
    print(f"scenario 3 called for user {user}")
    user_data = extract_user_data(data, user)
    user_data['battery_end_of_timestamp'] = [0.] * len(user_data.index)
    user_data['charged_from_outside'] = [0.] * len(user_data.index)
    user_data['start'] = pd.to_datetime(user_data['start'])
    user_data['end'] = pd.to_datetime(user_data['end'])
    user_data = user_data.sort_values('start')
    for i in range(len(user_data.index)):
        battery_beginning = 0.
        if i > 0:
            battery_beginning = np.minimum(battery_capacity, user_data['battery_end_of_timestamp'][user_data.index[i-1]] + \
                                get_PV_generated(user_data['end'][user_data.index[i-1]], user_data['start'][user_data.index[i]], user, path_to_data_folder))

        #print(np.maximum(0., user_data['needed_by_car'][user_data.index[i]] -
         #                                                 user_data['generated_by_PV'][user_data.index[i]] -
         #                                                 battery_beginning))
        charging = np.minimum(user_data['generated_by_PV'][user_data.index[i]], get_max_pv_charged(user_data['start'].iloc[i], user_data['end'].iloc[i], max_charging_power))
        user_data['charged_from_outside'][user_data.index[i]] = np.maximum(0., user_data['needed_by_car'][user_data.index[i]] -
                                                          charging -
                                                          battery_beginning)
        user_data['battery_end_of_timestamp'][user_data.index[i]] = np. minimum(battery_capacity, battery_beginning + \
                                                   user_data['generated_by_PV'][user_data.index[i]] + \
                                                   user_data['charged_from_outside'][user_data.index[i]] - \
                                                   user_data['needed_by_car'][user_data.index[i]])

    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    #print(user_data)
    total_charged_from_outside = sum(user_data['charged_from_outside'])
    total_demand = sum(user_data['needed_by_car'])
    coverage = 1 - (total_charged_from_outside / total_demand)
    return coverage

def create_scenario_table(data_baseline, data_scenario_2, data, capacity, power, path_to_data_folder):
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
    #print(user_list)
    scenario_baseline_list = [baseline(data_baseline, str(user_list[i]), power, path_to_data_folder) for i in range(len(user_list))]
    scenario_1_list = [scenario_1(data, str(user_list[i])) for i in range(len(user_list))]
    scenario_2_outcome = [scenario_2(data_scenario_2, str(user_list[i]), power) for i in range(len(user_list))]
    print('scenario 2 list')
    print(scenario_2_outcome)
    scenario_2_outcome = np.array(scenario_2_outcome)
    scenario_2_list = scenario_2_outcome[:,0]
    total_demand_list = scenario_2_outcome[:,1]
    print(scenario_2_list)
    print(total_demand_list)



    scenario_3_list = [scenario_3(data, str(user_list[i]), capacity, path_to_data_folder, power) for i in range(len(user_list))]
    #scenario_baseline_list = scenario_1_list



    list_of_tuples = list(zip(scenario_baseline_list, scenario_1_list, scenario_2_list, scenario_3_list, total_demand_list))
    table = pd.DataFrame(list_of_tuples , index = user_list, columns = ["Baseline", "Scenario 1", "Scenario 2", "Scenario 3", "Total Demand"])

    print(f"table: {table}")
    print(np.array(scenario_3_list) >= np.array(scenario_1_list))
    assert np.all(np.array(scenario_3_list) >= np.array(scenario_1_list)-0.000001)

    return table


