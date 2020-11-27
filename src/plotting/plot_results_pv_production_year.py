import datetime
import gzip
import json
import os
import sys
import warnings

sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.methods.helpers import get_user_id
from src.plotting.myplotlib import init_figure, Columnes, Journal, save_figure


if __name__ == "__main__":
    data_folder = os.path.join('.', 'data')

    car_is_at_home_file = os.path.join(data_folder, 'Car_is_at_home_table_UTC.csv')
    data = pd.read_csv(car_is_at_home_file, parse_dates=['start'])

    data_baseline = pd.read_csv(os.path.join(data_folder, 'data_baseline.csv'))
    vin_to_user_id = dict(set(list(data_baseline[~data_baseline['user_id'].isna()] \
        .apply(lambda r: (r['vin'], int(r['user_id'])), axis=1))))

    all_vehicles = set(data['vin'].unique())

    data_to_plot = []
    for vehicle in all_vehicles:
        wh_per_band = []
        user_id = vin_to_user_id[vehicle]
        try:
            filename = os.path.join(data_folder, f'data_PV_Solar', f'solar_rad_{user_id}.json.gz')
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
                # avg_prod = avg_prod['wh_produced'].mean()
                # prod = 24 * 2 * avg_prod
                prod = avg_prod['wh_produced'].sum()
                data_to_plot.append({
                    'uid': user_id,
                    'day': start_day,
                    'kwh_produced': prod / 1000
                })
        except Exception as e:
            warnings.warn(f'User {user_id} could not be processed: {e}.')

    data_to_plot = pd.DataFrame(data_to_plot, columns=['day', 'kwh_produced'])
    
    journal = Journal.POWERPOINT_A3
    fig, ax = init_figure(nrows=1, ncols=1,
                            columnes=Columnes.ONE, fig_height_mm=140,
                            journal=journal, sharex=True, sharey=True)

    plt.sca(ax)
    sns.lineplot(data=data_to_plot, x="day", y="kwh_produced",
                 linewidth=3, ax=ax)
    ax.set_xlabel('Days in 2017 [d]')
    ax.set_ylabel('Energy Produced by PV [kWh]')
    plt.savefig('plots/energy_generation.png', bbox_inches='tight', dpi=300)
