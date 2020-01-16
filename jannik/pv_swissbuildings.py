'''
Created on Dec 12, 2019

@author: rene
'''
import os
import rasterio
import numpy as np
import datetime


class PVModel:

    def __init__(self, user_directory):

        self.user_directory = user_directory

        # read mask
        with rasterio.open(os.path.join(user_directory, "mask.tif")) as src:
            self.mask = src.read(1)

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

    def get_solar_radiation(self, startts, endts):
        """
            Calculates total rooftop solar irradiation between startts and endts timestamp in Wh
        """

        # Each cell has size 0.5 * 0.5 m2
        cell_area = 0.5 * 0.5

        # Each band stands for 30 minutes interval
        hours_per_ts = 0.5

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

            with rasterio.open(os.path.join(self.user_directory, "solar_rad.tif")) as src:
                rad_W = src.read(b, masked=True) * self.mask

                # Convert radiation level per cell to Watt hours
                rad_Wh = rad_W * hours_per_ts * cell_area

                # For the first and last band we need to consider that
                # we need not necessary the whole period
                # Nodata values are set to 0
                _tot_Wh = np.sum(rad_Wh.filled(fill_value=0))
                if b == start_band:
                    _tot_Wh *= percentage_in_start_band
                elif b == end_band:
                    _tot_Wh *= percentage_in_end_band

                tot_Wh += float(_tot_Wh)

        return tot_Wh


pv = PVModel(r"/home/rene/workspace/PVMobility/data/pv/1761")

print(pv.get_solar_radiation(datetime.datetime(2017, 1, 1, 2, 0),
                             datetime.datetime(2017, 1, 1, 10, 0)))

