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

def create_scenario_table(data):
    """
    Creates a dataframe that contains coverage in all different scenarios

    Parameters
    ----------
    data: pd-dataframe
        dataframe to extract information from

    Returns
    -------
    table: pandas-df
        table with the three scenarios
    """
    user_list = list(set(data["vin"]))
    print(user_list)
    scenario_1_list = [scenario_1(data, str(user_list[i])) for i in range(len(user_list))]
    table = pd.DataFrame(scenario_1_list, index = user_list, columns = ["Scenario 1"])

    return table


