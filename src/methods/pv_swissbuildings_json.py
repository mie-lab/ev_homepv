'''
Created on Dec 12, 2019

@author: rene
'''
import os
import numpy as np
import datetime
import gzip
import json
import pint

ureg = pint.UnitRegistry()


class PVModel:

    def __init__(self, user_id, path_to_data_folder):
        
        #with gzip.GzipFile(os.path.join("data_PV_Solar", "solar_rad_{}.json.gz".format(user_id)), 'r') as f:
        #    self.data_PV_Solar = json.loads(f.read())
        filepath = os.path.join(path_to_data_folder,
                                "data_PV_Solar")
        filepath = os.path.join(filepath,
                                "solar_rad_{}.json.gz".format(user_id))

        with gzip.GzipFile(filepath, 'r') as f:
            self.data = json.loads(f.read())

    def _get_band(self, dt):
        """
            Returns band from timestamp
        """

        delta = dt - datetime.datetime(2017, 1, 1, 0, 0)

        half_hours = int(delta.total_seconds() / 60.0 / 30.0)

        return half_hours + 1

    def _get_datetime(self, b):
        """
            Returns timestamp from band
        """
        minutes = b * 30.0
        return datetime.datetime(2017, 1, 1, 0, 0) + datetime.timedelta(minutes=minutes)

    def get_solar_radiation(self, scenario, startts, endts):
        """
            Calculates total rooftop solar irradiation between startts and endts timestamp in Wh

            scenarios:
                PVMODEL_SPV170
                PVMODEL_JA
                PVMODEL_JINKO
                ONLY_SOLAR_PVSYSEFF_5
                ONLY_SOLAR_PVSYSEFF_6
                ONLY_SOLAR_PVSYSEFF_7
                ONLY_SOLAR_PVSYSEFF_8
                ONLY_SOLAR_PVSYSEFF_9
                ONLY_SOLAR_PVSYSEFF_10
                ONLY_SOLAR_PVSYSEFF_11
                ONLY_SOLAR_PVSYSEFF_12
                ONLY_SOLAR_PVSYSEFF_13
                ONLY_SOLAR_PVSYSEFF_14
                ONLY_SOLAR_PVSYSEFF_15
                ONLY_SOLAR_PVSYSEFF_16
                ONLY_SOLAR_PVSYSEFF_17
                ONLY_SOLAR_PVSYSEFF_18
                ONLY_SOLAR_PVSYSEFF_19
                ONLY_SOLAR_PVSYSEFF_20
                ONLY_SOLAR_PVSYSEFF_21
                ONLY_SOLAR_PVSYSEFF_22
                ONLY_SOLAR_PVSYSEFF_23
                ONLY_SOLAR_PVSYSEFF_24
                ONLY_SOLAR_PVSYSEFF_25
                ONLY_SOLAR_PVSYSEFF_26
                ONLY_SOLAR_PVSYSEFF_27
                ONLY_SOLAR_PVSYSEFF_28
                ONLY_SOLAR_PVSYSEFF_29
                ONLY_SOLAR_PVSYSEFF_100

        """

        assert endts >= startts

        start_band = self._get_band(startts)
        end_band = self._get_band(endts)

        seconds_in_half_hour = 60.0 * 30.0

        if start_band == end_band:
            percentage_in_start_band = (endts - startts).total_seconds() / seconds_in_half_hour
            percentage_in_end_band = 0.0
        else:
            percentage_in_start_band = (self._get_datetime(start_band) - startts).total_seconds() / seconds_in_half_hour
            percentage_in_end_band = 1.0 - (self._get_datetime(end_band) - endts).total_seconds() / seconds_in_half_hour

        assert 0 <= percentage_in_start_band <= 1.0
        assert 0 <= percentage_in_end_band <= 1.0

        tot_Wh = 0.0

        for b in range(start_band, end_band + 1):
            
            band_key = "band_{}_Wh".format(b)
            if band_key not in self.data[scenario]:
                _tot_Wh = 0.0
            else:
                _tot_Wh = float(self.data[scenario][band_key])


            tot_Wh += _tot_Wh

        return tot_Wh
        #return tot_Wh * ureg.watthour


#pv = PVModel("1761")

#print(pv.get_solar_radiation("PVMODEL_SPV170",
#                             datetime.datetime(2017, 1, 1, 0, 0),
#                             datetime.datetime(2017, 12, 31, 23, 59)))
