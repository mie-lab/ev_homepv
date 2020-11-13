import copy
import numpy as np
import pint
import pandas as pd
import os

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


def get_id_matching_dict(filepath_matching):
    """Create a dict that has myway_ids as keys and
    vins as values"""
    matching = pd.read_csv(filepath_matching, sep=';')
    myway_id = matching['BMW_userid']
    vin = matching['BMW_vid']
    return dict(zip(myway_id, vin))


def filter_good_users(data_raw, attr, path_to_data_folder):
    """
    data: Dataframe
    attr: column_name of vin column
    """
    data = data_raw.copy()
    vins_with_zero_demand = ['0007f9c8534b7924352bed2b9842b1fc',
                             '003d3821dfaabc96fa1710c2128aeb62']
    vins_only_in_baseline = ['0072a451141128e2b75f66a1a34b7c67',
                             'a8efc1cea1e62b7b4ae65e19878edbcf']
    other_bad_vins = vins_with_zero_demand + vins_only_in_baseline
    filepath = os.path.join(path_to_data_folder,
                            "manual_validation.csv")
    validation = pd.read_csv(filepath, sep=';')

    matching_dict = get_id_matching_dict(os.path.join(path_to_data_folder,
                                                      "matching_bmw_to_address.csv"))

    good_userids_ix = (validation['Brauchbar'] == 1) & (validation['EFH'] == 1)
    good_userids = validation.loc[good_userids_ix, 'ID']

    # transform user_id to vin
    good_vins = good_userids.map(matching_dict)
    good_vins = good_vins.dropna()
    good_vins = good_vins[~good_vins.isin(other_bad_vins)]
    good_row_ix = data[attr].isin(good_vins)

    return data[good_row_ix]


def validate_data(data, attr, path_to_data_folder):
    """validate_data is replaced by filter_good_users (HM)"""
    print("validate is called!")
    filepath_matching = os.path.join(path_to_data_folder,
                                     "matching_bmw_to_address.csv")
    filepath = os.path.join(path_to_data_folder,
                            "manual_validation.csv")
    validation = pd.read_csv(filepath, sep=';')
    matching = pd.read_csv(filepath_matching, sep=';')

    current_vin_list = []

    df = copy.deepcopy(data)
    # print(len(df))

    vin_list = data[attr].tolist()
    vin_list = set(vin_list)
    # print(vin_list)
    count = 0
    for current_vin in vin_list:
        count += 1

        house = get_user_id(current_vin, path_to_data_folder)
        # print(house)
        # print(validation)
        if (current_vin not in current_vin_list):  # or house is None:
            useable = None
            single_home = None
            keep_row = False
            if house is not None:
                useable = validation['Brauchbar'].loc[validation['ID'] == int(house)]
                useable = int(useable.iloc[0])
                single_home = validation['EFH'].loc[validation['ID'] == int(house)]
                single_home = int(single_home.iloc[0])
                keep_row = ((useable == 1) and (single_home == 1))
            current_vin_list.append(current_vin)

            if not keep_row:
                df.reset_index()
                df = df.drop(df[df.vin == current_vin].index)
            # print(len(df))

        # a = 1/0
    print(len(data))
    print(len(df))
    return df
