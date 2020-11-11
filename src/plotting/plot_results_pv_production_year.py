import datetime
import gzip
import json
import os
import sys

sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from src.methods.helpers import validate_data, get_user_id
from src.methods.loading_and_preprocessing import load_car_data

if __name__ == "__main__":
    path_to_data_folder = r'D:\Data\Polybox\Shared\ev_homepv\data'
    filepath = os.path.join(path_to_data_folder, 'car_is_at_home_table_UTC.csv')

    data = load_car_data(filepath)
    data = validate_data(data, 'vin', path_to_data_folder)

    all_vehicles = set(data['vin'].unique())

    data_to_plot = []
    for vehicle in all_vehicles:
        wh_per_band = []
        user_id = get_user_id(vehicle, path_to_data_folder)
        filename = os.path.join(path_to_data_folder, f'data_old\data_PV_Solar\solar_rad_{user_id}.json.gz')
        with gzip.GzipFile(filename, 'r') as f:
            json_bytes = f.read()
            json_string = json_bytes.decode('utf-8')
            pv_data = json.loads(json_string)

        for band in range(365 * 24 * 2):
            minutes = band * 30
            timestamp = datetime.datetime(2017, 1, 1, 0, 0) + datetime.timedelta(minutes=minutes)
            try:
                wh_produced = pv_data['PVMODEL_SPV170'][f'band_{band}_Wh']
            except:
                wh_produced = np.nan
            wh_per_band.append({
                'timestamp': timestamp,
                'wh_produced': wh_produced
            })

        wh_per_band = pd.DataFrame(wh_per_band, columns=['timestamp', 'wh_produced'])
        wh_per_band = wh_per_band.dropna()

        # For each day, compute the average production per band, and multiply by 24 * 2.
        for day in range(365):
            start_day = datetime.datetime(2017, 1, 1, 0, 0) + datetime.timedelta(days=day)
            end_day = datetime.datetime(2017, 1, 1, 0, 0) + datetime.timedelta(days=day + 1)
            avg_prod = wh_per_band[(start_day <= wh_per_band['timestamp']) & (wh_per_band['timestamp'] < end_day)]
            avg_prod = avg_prod['wh_produced'].mean()
            prod = 24 * 2 * avg_prod
            data_to_plot.append({
                'uid': user_id,
                'day': start_day,
                'kwh_produced': prod / 1000
            })

    data_to_plot = pd.DataFrame(data_to_plot, columns=['day', 'kwh_produced'])

    fig, ax = plt.subplots(1, 1, figsize=(8, 3.5))
    plt.scatter(data_to_plot['day'], data_to_plot['kwh_produced'], s=2, alpha=0.5)
    ax.set_xlabel('Days in 2017 [d]')
    ax.set_ylabel('Energy Produced by PV [kWh]')
    # data_to_plot.plot.kde(ax=ax)
    plt.savefig('plots/energy_generation.png', bbox_inches='tight', dpi=300)
