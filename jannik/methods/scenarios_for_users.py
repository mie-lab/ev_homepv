import copy
import pandas as pd

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
    print(datacopy['vin'])
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
    coverage = total_charged / total_demand
    return coverage
