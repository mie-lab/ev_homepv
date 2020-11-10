import datetime
import os
import numpy as np

import pint

from src.methods.helpers import get_user_id
from src.methods.pv_swissbuildings_json import PVModel

ureg = pint.UnitRegistry()

# TODO
pv_efficency = 0.18
#pv_efficency = 180


pv_cache = {}

def get_PV_generated_from_pandas_row(ix_row, max_power_kw=11):
    """wrapper function for get_PV_generated that can be used with the
    df.iterrows() generator"""
    ix, row = ix_row
    try:
        return get_PV_generated(row['start'],
                                row['end'],
                                row['vin'], max_power_kw=max_power_kw)
    except (ValueError, FileNotFoundError):
        return -1


def get_PV_generated(start, end, house_ID, path_to_data_folder=os.path.join('.','data'), max_power_kw=None):
    # todo: efficiency. If we still have to take into account the efficiency it has to be done in the method
    #  PVModel.get_solar_radiation() because otherwise the max_power_kw restriction would be too strong
    """
    start
    end
    house_ID: vin
    """

    assert start.year >= 2017, "solar model is defined starting from Jan 2017"
    assert end.year >= 2017
    if house_ID not in pv_cache:
        user_id = get_user_id(house_ID, path_to_data_folder)
        if user_id is None:
            # this means we don't have a  house for this user
            raise ValueError("No vin - myway user_id matching available for {}".format(user_id))

        pv = PVModel(str(user_id), path_to_data_folder)
        pv_cache[house_ID] = pv

    pv = pv_cache[house_ID]
    start_datetime = datetime.datetime.strptime(str(start), "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.datetime.strptime(str(end), "%Y-%m-%d %H:%M:%S")

    generated_energy = pv.get_solar_radiation("PVMODEL_SPV170",
                             start_datetime,
                             end_datetime,
                            max_power_kw=max_power_kw)
    generated_KWh = generated_energy / 1000
    return generated_KWh

def get_max_pv_charged(start, end, max_charging_power):
    start_datetime = datetime.datetime.strptime(str(start), "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.datetime.strptime(str(end), "%Y-%m-%d %H:%M:%S")
    max_charged = (end_datetime. timestamp() - start_datetime.timestamp()) * max_charging_power / (60*60)
   # print(start)
   # print(end)
   # print(max_charged)
    return np.float(max_charged)
