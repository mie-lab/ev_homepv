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

def get_user_id(house_ID):
    #print(f"house ID:{house_ID}")
    filepath_to_table = os.path.join( "..", "..",  "..", "..", "..",  "..", "..", "..","users", "hamperj", "private", "matching_bmw_to_address.csv")
    #print(os.path.abspath(filepath_to_table))
    data = pd.read_csv(filepath_to_table, sep=';')
    relevant_columns = ['BMW_vid', 'BMW_userid']
    data = data[relevant_columns]
    #print(data)
    user_id = data['BMW_userid'].loc[data['BMW_vid'] == house_ID]
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
    return str(int(user_id.iloc[0]))
