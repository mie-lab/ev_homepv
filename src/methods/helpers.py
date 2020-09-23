import copy

import numpy as np
import pint
ureg = pint.UnitRegistry()
import pandas as pd
import os

def soc2remainingCharge(soc):
    charge = 0.29182217878746003 * (100.0 - soc) + 0.24606563337628493 * np.sqrt(100.0 - soc) #formula to calc charge from soc
    assert charge >= 0.0
    #return charge * ureg.kilowatthour
    return charge


def remainingCharge2soc(charge):
    # wolfram alpha magic
    soc = -3.42674 * (-29.0785 + charge) + 1.6478263810833557*10**-44 * np.sqrt(4.654229268178746*10**86 + 8.972720402977183*10**87 * charge)
    assert soc >= 0 and soc <= 100.0
    return soc

def get_user_id(vid, path_to_data_folder):
    #print(f"vid ID:{vid}")
    filepath_to_table = os.path.join( path_to_data_folder, "matching_bmw_to_address.csv")
    #print(os.path.abspath(filepath_to_table))
    data = pd.read_csv(filepath_to_table, sep=';')
    relevant_columns = ['BMW_vid', 'BMW_userid']
    data = data[relevant_columns]
    #print(data_PV_Solar)
    user_id = data['BMW_userid'].loc[data['BMW_vid'] == vid]
    #print(house_ID)
    #print(type(user_id))
    """
    if (len(user_id) ==1):
        user_id = user_id[0]
    else:
        print(user_id.loc(0))
        user_id = user_id[0][0]
    """
    #print(user_id.iloc[0])
    #print(vid)
    if len (user_id) == 0:
        return None
    return str(int(user_id.iloc[0]))


def validate_data(data, attr, path_to_data_folder):
    print("validate is called!")
    filepath_matching = os.path.join(path_to_data_folder,
                            "matching_bmw_to_address.csv")
    filepath = os.path.join(path_to_data_folder,
                 "Validation.csv")
    validation = pd.read_csv(filepath, sep=';')
    matching = pd.read_csv(filepath_matching, sep=';')

    list = []

    df = copy.deepcopy(data)
    #print(len(df))

    vin_list = data[attr].tolist()
    vin_list = set(vin_list)
    #print(vin_list)
    count = 0
    for current_vin in vin_list:
        count +=1

        #print(index)
        #print(row)
        #print(count)
        #print(current_vin)
        #current_vin = "004c4ba86e77149b9bfe2dfebb4057a4"
        house = get_user_id(current_vin, path_to_data_folder)
        #print(house)
        #print(validation)
        if (not current_vin in list):# or house is None:
            useable = None
            single_home = None
            keep_row = False
            if house is not None:
                useable = validation['Brauchbar'].loc[validation['ID'] == int(house)]
                useable = int(useable.iloc[0])
                single_home = validation['EFH'].loc[validation['ID'] == int(house)]
                single_home = int(single_home.iloc[0])
                keep_row = ((useable==1) and (single_home==1))
            list.append(current_vin)

            #print(current_vin)
            #print(house)
            #print(useable)
            #print(single_home)
            #print(keep_row)

            if not keep_row:
                df.reset_index()
                df = df.drop(df[df.vin == current_vin].index)
            #print(len(df))

        #a = 1/0
    print(len(data))
    print(len(df))
    return df
