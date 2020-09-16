import copy
import datetime

import pandas as pd
import numpy as np

from jannik.methods.PV_interface import get_PV_generated
from jannik.methods.helpers import soc2remainingCharge, remainingCharge2soc


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
        data with rows selected

    """
    datacopy = copy.deepcopy(data)
    datacopy['vin'] = datacopy['vin'].astype(str)
    datacopy= datacopy.drop(datacopy[datacopy['vin'] != user].index)
    return datacopy

def baseline(data_baseline, user):
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
                                                         user_data["vin"][user_data.index[i]]
                                                         ) for i in range(len(user_data.index))]
    needed_by_car = [soc2remainingCharge(user_data["soc_start"][user_data.index[i]]) -
                     soc2remainingCharge(user_data["soc_end"][user_data.index[i]])
                     for i in range(len(user_data.index))]
    needed_by_car = np.maximum(0, needed_by_car)
    #needed_by_car = np.maximum(0, needed_by_car)
    user_data['needed_by_car'] = needed_by_car
    relevant_columns = [ 'soc_start', 'soc_end', 'zustand', 'needed_by_car', 'generated_by_PV']

    charged_from_pv = [np.minimum(user_data['generated_by_PV'][user_data.index[i]],
                                  user_data['needed_by_car'][user_data.index[i]])
                       for i in range(len(user_data.index))]
    charged_from_pv = np.maximum(0, charged_from_pv)
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

def scenario_2(data, user):
    """
    Computes fraction when Energy can be charged, but does not have to be equal to real user data.

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
    relevant_columns = ['kWh_start', 'is_home', 'kWh_end', 'total_segment_consumption_kWh',
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
            user_data['kWh_end'].iloc[i] = np.minimum(user_data['max_kWh'].iloc[i],
                                                   user_data['kWh_start'].iloc[i] + user_data['generated_by_PV'].iloc[i] + user_data['total_segment_consumption_kWh'].iloc[i])
        else:
            # if not at home, just consume
            user_data['kWh_end'].iloc[i] = user_data['kWh_start'].iloc[i] + user_data['total_segment_consumption_kWh'].iloc[i]

    print(user_data.head(5))
    print(user_data.tail(5))

    assert np.all(user_data['charged_from_outside'] >=0)
    assert np.all(user_data['total_segment_consumption_kWh'] <= 0)
    total_charged_from_outside = sum(user_data['charged_from_outside'])
    total_demand = - sum(user_data['total_segment_consumption_kWh'])
    coverage = 1 - (total_charged_from_outside / total_demand)
    assert 0 <= coverage <= 1
    return coverage



def scenario_3(data, user, battery_capacity):
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
                                get_PV_generated(user_data['end'][user_data.index[i-1]], user_data['start'][user_data.index[i]], user))

        #print(np.maximum(0., user_data['needed_by_car'][user_data.index[i]] -
         #                                                 user_data['generated_by_PV'][user_data.index[i]] -
         #                                                 battery_beginning))

        user_data['charged_from_outside'][user_data.index[i]] = np.maximum(0., user_data['needed_by_car'][user_data.index[i]] -
                                                          user_data['generated_by_PV'][user_data.index[i]] -
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

def create_scenario_table(data_baseline, data_scenario_2, data, capacity):
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
    scenario_baseline_list = [baseline(data_baseline, str(user_list[i])) for i in range(len(user_list))]
    scenario_1_list = [scenario_1(data, str(user_list[i])) for i in range(len(user_list))]
    scenario_2_list = [scenario_2(data_scenario_2, str(user_list[i])) for i in range(len(user_list))]
    scenario_3_list = [scenario_3(data, str(user_list[i]), capacity) for i in range(len(user_list))]
    #scenario_baseline_list = scenario_1_list



    list_of_tuples = list(zip(scenario_baseline_list, scenario_1_list, scenario_2_list, scenario_3_list))
    table = pd.DataFrame(list_of_tuples , index = user_list, columns = ["Baseline", "Scenario 1", "Scenario 2", "Scenario 3"])

    print(f"table: {table}")
    print(np.array(scenario_3_list) >= np.array(scenario_1_list))
    assert np.all(np.array(scenario_3_list) >= np.array(scenario_1_list)-0.000001)

    return table


