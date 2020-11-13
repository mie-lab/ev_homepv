import numpy as np
import pint
import pandas as pd
import os
import datetime

ureg = pint.UnitRegistry()

def soc2remainingCharge(soc):
    charge = 0.293 * (100.0 - soc) + 0.232 * np.sqrt(100.0 - soc)  # formula to calc charge from soc
    assert charge >= 0.0
    # return charge * ureg.kilowatthour
    return charge


def remainingCharge2soc(charge):
    # wolfram alpha magic
    # https://www.wolframalpha.com/input/?i=invert+y+%3D+0.293+*+%28100-x%29+%2B+0.232+*+sqrt%28100-x%29
    # old: soc = -3.42674 * (-29.0785 + charge) + 1.6478263810833557*10**-44 * np.sqrt(4.654229268178746*10**86 + 8.972720402977183*10**87 * charge)
    soc = -3.41297 * (-29.2082 + charge) + 5.82418 * (10 ** -6) * np.sqrt(
        6.30817 * (10 ** 10) * charge + 2.89702 * (10 ** 9))

    assert 0 <= soc <= 100.0
    return soc


def get_user_id(vid, path_to_data_folder=os.path.join('.', 'data')):
    """Transforms vin to myway user id"""
    # print(f"vid ID:{vid}")
    filepath_to_table = os.path.join(path_to_data_folder, "matching_bmw_to_address.csv")
    # print(os.path.abspath(filepath_to_table))
    data = pd.read_csv(filepath_to_table, sep=';')
    relevant_columns = ['BMW_vid', 'BMW_userid']
    data = data[relevant_columns]
    # print(data_PV_Solar)
    user_id = data['BMW_userid'].loc[data['BMW_vid'] == vid]
    # print(house_ID)
    # print(type(user_id))
    """
    if (len(user_id) ==1):
        user_id = user_id[0]
    else:
        print(user_id.loc(0))
        user_id = user_id[0][0]
    """
    # print(user_id.iloc[0])
    # print(vid)
    if len(user_id) == 0:
        return None
    return str(int(user_id.iloc[0]))


