import numpy as np
import pandas as pd
import os
from src.methods.PV_interface import get_PV_generated, get_max_pv_charged
from src.methods.helpers import soc2remainingCharge


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


def baseline(data_baseline_raw):
    # print(f"\tbaseline called for user {user}")
    data_baseline = data_baseline_raw.copy()

    all_users = data_baseline['vin'].unique()
    coverage_all = []
    user_df_list = []
    for user in all_users:

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
            coverage = 1
        assert 0 <= coverage <= 1
        coverage_all.append((user, coverage, total_demand))

        user_df_list.append(user_data)

    all_user_data = pd.concat(user_df_list)
    return coverage_all, all_user_data


def scenario_1(data_raw):
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

    data = data_raw.copy()
    coverage_all = []

    all_users = data['vin'].unique()
    for user in all_users:

        user_data = extract_user(data, user)

        total_charged = sum(user_data['charged_from_pv'])
        total_demand = sum(user_data['needed_by_car'])

        if (total_demand == 0):
            print(f'\t\tuser with zero demand: {user}')

        coverage = total_charged / total_demand

        assert 0 <= coverage <= 1
        coverage_all.append((user, coverage))

    return coverage_all, data


def scenario_2(data_raw):
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
    data = data_raw.copy()
    all_users = data['vin'].unique()
    coverage_all = []
    user_df_list = []
    for user in all_users:

        # filter
        user_data = extract_user(data, user)
        user_data = user_data.sort_values('start')
        # init new columns
        user_data['kWh_start'] = [0.] * len(user_data.index)
        user_data['kWh_end'] = [0.] * len(user_data.index)
        user_data['charged_from_outside'] = [0.] * len(user_data.index)
        user_data['max_kWh'] = [soc2remainingCharge(0)] * len(user_data.index)

        # calculcate total consumption per segment in kWh
        user_data['total_segment_consumption_kWh'] = \
            [soc2remainingCharge(0) -
             soc2remainingCharge(user_data['total_segment_consumption'][user_data.index[i]])
             for i in range(len(user_data.index))]

        # relevant_columns = ['kWh_start', 'start', 'end', 'is_home', 'kWh_end', 'total_segment_consumption_kWh',
        #                     'generated_by_pv', 'max_kWh', 'charged_from_outside']
        # user_data = user_data[relevant_columns]

        for i, ix in enumerate(user_data.index):
            if i != 0:
                # end has to be updated with the consumptions of the other segments
                user_data.loc[ix, 'kWh_start'] = user_data['kWh_end'].iloc[i - 1]

            # load from outside if necessary
            if user_data['kWh_start'].iloc[i] < 0:
                user_data.loc[ix, 'charged_from_outside'] = - user_data['kWh_start'].iloc[i]
                user_data.loc[ix, 'kWh_start'] = 0

            if user_data.loc[ix, 'is_home']:
                # load from PV, the column 'generated_by_pv' already considers max charging
                max_pv_charging = user_data.loc[ix, 'generated_by_pv']

                user_data.loc[ix, 'kWh_end'] = np.minimum(user_data.loc[ix, 'max_kWh'],
                                                          user_data.loc[ix, 'kWh_start']
                                                          + max_pv_charging
                                                          + user_data.loc[ix, 'total_segment_consumption_kWh'])
            else:
                # if not at home, just consume
                user_data.loc[ix, 'kWh_end'] = user_data.loc[ix, 'kWh_start'] \
                                               + user_data.loc[ix, 'total_segment_consumption_kWh']

        assert np.all(user_data['charged_from_outside'] >= 0)
        assert np.all(user_data['total_segment_consumption_kWh'] <= 0)
        total_charged_from_outside = sum(user_data['charged_from_outside'])
        total_demand = - sum(user_data['total_segment_consumption_kWh'])
        coverage = 1 - (total_charged_from_outside / total_demand)
        assert 0 <= coverage <= 1

        coverage_all.append((user, coverage))
        user_df_list.append(user_data)

    all_user_data = pd.concat(user_df_list)
    return coverage_all, all_user_data


def scenario_3(data_raw, battery_capacity, battery_power, path_to_data_folder=os.path.join('.', 'data')):
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
    data = data_raw.copy()
    all_users = data['vin'].unique()
    coverage_all = []
    user_df_list = []
    for user in all_users:

        # print(f"\tscenario 3 called for user {user}")
        user_data = extract_user(data, user)
        user_data = user_data.sort_values('start')

        user_data['battery_end_of_timestamp'] = [0.] * len(user_data.index)
        user_data['charged_from_outside'] = [0.] * len(user_data.index)

        for i, ix in enumerate(user_data.index):

            battery_beginning = 0.
            if i > 0:
                # calculate battery SOC at the beginning of the timestamp as:
                # Battery last SOC + PV generated when the car was away
                battery_beginning = np.minimum(battery_capacity,
                                               user_data['battery_end_of_timestamp'].iloc[i - 1]
                                               + get_PV_generated(start=user_data['end'].iloc[i - 1],
                                                                  end=user_data['start'].iloc[i],
                                                                  house_ID=user,
                                                                  path_to_data_folder=path_to_data_folder,
                                                                  max_power_kw=battery_power)
                                               )

            max_pv_charging = user_data.loc[ix, 'generated_by_pv']
            # Everything that can not be covered by pv or by the battery is charged from outside (=the grid)
            user_data.loc[ix, 'charged_from_outside'] = \
                np.maximum(0., user_data.loc[ix, 'needed_by_car']
                           - max_pv_charging - battery_beginning)

            # calculate new SOC of battery at the end of the timestamp
            user_data.loc[user_data.index[i], 'battery_end_of_timestamp'] = \
                np.minimum(battery_capacity, battery_beginning
                           + user_data['generated_by_pv'][user_data.index[i]]
                           + user_data['charged_from_outside'][user_data.index[i]]
                           - user_data['needed_by_car'][user_data.index[i]])

        total_charged_from_outside = sum(user_data['charged_from_outside'])
        total_demand = sum(user_data['needed_by_car'])
        coverage = 1 - (total_charged_from_outside / total_demand)

        coverage_all.append((user, coverage))
        user_df_list.append(user_data)

    all_user_data = pd.concat(user_df_list)
    return coverage_all, all_user_data


def create_scenario_table(data_baseline, data_scenario_2, data, battery_capacity, battery_power,
                          path_to_data_folder=os.path.join('.', 'data')):
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

    print("baseline")
    baseline_coverage, baseline_results = baseline(data_baseline)

    print("scenario 1")
    scenario1_coverage, scenario1_results = scenario_1(data)

    print("scenario 2")
    scenario2_coverage, scenario2_results = scenario_2(data_scenario_2)

    print("scenario 3")
    scenario3_coverage, scenario3_results = scenario_3(data, battery_capacity=battery_capacity,
                                                       battery_power=battery_power)
    # transform to coverage information to single dataframe
    baseline_coverage = pd.DataFrame(baseline_coverage, columns=['vin', 'baseline', 'total_demand']).set_index('vin')
    scenario1_coverage = pd.DataFrame(scenario1_coverage, columns=['vin', 'scenario1']).set_index('vin')
    scenario2_coverage = pd.DataFrame(scenario2_coverage, columns=['vin', 'scenario2']).set_index('vin')
    scenario3_coverage = pd.DataFrame(scenario3_coverage, columns=['vin', 'scenario3']).set_index('vin')

    table = pd.concat((baseline_coverage, scenario1_coverage, scenario2_coverage, scenario3_coverage), axis=1)

    # write results
    print("write scenario results")
    baseline_results.to_csv(os.path.join(path_to_data_folder, 'output', 'results_baseline.csv'))
    scenario1_results.to_csv(os.path.join(path_to_data_folder, 'output', 'results_scenario1.csv'))
    scenario2_results.to_csv(os.path.join(path_to_data_folder, 'output', 'results_scenario2.csv'))
    scenario3_results.to_csv(os.path.join(path_to_data_folder, 'output', 'results_scenario3.csv'))

    # print(f"table: {table}")
    # print(np.array(scenario_3_list) >= np.array(scenario_1_list))
    # assert np.all(np.array(scenario_3_list) >= np.array(scenario_1_list) - 0.000001)

    return table
