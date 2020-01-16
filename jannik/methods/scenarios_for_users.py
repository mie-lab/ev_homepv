import copy
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

    user_data = extract_user_data(data, user)
    user_data['start'] = pd.to_datetime(user_data['start'])
    user_data['end'] = pd.to_datetime(user_data['end'])
    user_data = user_data.sort_values('start')

    user_data['MwH_start'] = [0.] * len(user_data.index)
    user_data['MwH_end'] = [0.] * len(user_data.index)
    user_data['charged_from_outside'] = [0.] * len(user_data.index)
    user_data['MwH_needed_during_next_trip'] = [0.] * len(user_data.index)
    for i in range(len(user_data.index)-1):
        user_data['MwH_needed_during_next_trip'][user_data.index[i]] = soc2remainingCharge(user_data['soc_start'][user_data.index[i+1]]) \
                                                   - soc2remainingCharge(user_data['soc_end'][user_data.index[i]])
        if i == 0:
            user_data['MwH_start'][user_data.index[i]] = soc2remainingCharge(0) - soc2remainingCharge(user_data['soc_start'][user_data.index[i]])
        if i > 0:
            user_data['MwH_start'][user_data.index[i]] = \
                user_data['MwH_end'][user_data.index[i-1]] - user_data['MwH_needed_during_next_trip'][user_data.index[i-1]]

        #print(user_data['MwH_start'][user_data.index[i]])
        assert round(user_data['MwH_start'][user_data.index[i]], 10) >= 0.0
        user_data['charged_from_outside'][user_data.index[i]] = np.maximum(0, user_data['MwH_needed_during_next_trip'][user_data.index[i]] -
                                                                               user_data['MwH_start'][user_data.index[i]]-
                                                                               user_data['generated_by_PV'][user_data.index[i]])
        user_data['MwH_end'][user_data.index[i]] = user_data['MwH_start'][user_data.index[i]] + user_data['charged_from_outside'][user_data.index[i]] + user_data['generated_by_PV'][user_data.index[i]]
        # SOC must not exceed 100%
        user_data['MwH_end'][user_data.index[i]] = np.minimum(soc2remainingCharge(0), user_data['MwH_end'][user_data.index[i]])
        # assert that SOC <100
        #print(user_data['MwH_end'][user_data.index[i]])
        assert 100 > remainingCharge2soc(user_data['MwH_end'][user_data.index[i]])


    total_charged_from_outside = sum(user_data['charged_from_outside'])
    total_demand = sum(user_data['needed_by_car'])
    coverage = 1 - (total_charged_from_outside / total_demand)
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

def create_scenario_table(data, capacity):
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
    scenario_1_list = [scenario_1(data, str(user_list[i])) for i in range(len(user_list))]
    scenario_2_list = [scenario_2(data, str(user_list[i])) for i in range(len(user_list))]
    scenario_3_list = [scenario_3(data, str(user_list[i]), capacity) for i in range(len(user_list))]



    list_of_tuples = list(zip(scenario_1_list, scenario_2_list, scenario_3_list))
    table = pd.DataFrame(list_of_tuples , index = user_list, columns = ["Scenario 1", "Scenario 2", "Scenario 3"])

    print(f"table: {table}")
    print(np.array(scenario_3_list) >= np.array(scenario_1_list))
    assert np.all(np.array(scenario_3_list) >= np.array(scenario_1_list)-0.000001)

    return table


