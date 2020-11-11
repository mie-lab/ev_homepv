import datetime
import math
import os
import sys

sys.path.append('.')

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import seaborn as sns

from src.methods.helpers import validate_data, get_user_id
from src.methods.loading_and_preprocessing import load_car_data


def soc_to_kwh(soc_diff):
    soc_diff = -soc_diff
    return 0.293 * soc_diff + 0.232 * math.sqrt(soc_diff)


if __name__ == "__main__":
    path_to_data_folder = r'D:\Data\Polybox\Shared\ev_homepv\data'
    filepath = os.path.join(path_to_data_folder, 'car_is_at_home_table_UTC.csv')
    raw_bmw_filepath = os.path.join(path_to_data_folder, 'raw_bmw_data.csv')

    data = load_car_data(filepath)
    data = validate_data(data, 'vin', path_to_data_folder)
    raw_bmw_data = pd.read_csv(raw_bmw_filepath, parse_dates=['timestamp'])

    all_vehicles = set(data['vin'].unique())

    data_to_plot = []
    for vehicle in all_vehicles:
        veh_en_cons = []
        user_id = get_user_id(vehicle, path_to_data_folder)
        raw_bmw_data_vehicle = raw_bmw_data[raw_bmw_data['vin'] == vehicle].copy()
        raw_bmw_data_vehicle = raw_bmw_data_vehicle.sort_values(['timestamp'])

        # Go through everything in pairs, compute the difference between pairs.
        for (idx_1, row_1), (idx_2, row_2) in zip(raw_bmw_data_vehicle[:-1].iterrows(),
                                                  raw_bmw_data_vehicle[1:].iterrows()):
            t_diff = row_2['timestamp'] - row_1['timestamp']
            soc_diff = row_2['soc'] - row_1['soc']
            if soc_diff >= 0:
                energy_required_kwh = 0
            else:
                # In case the difference is negative, energy was consumed. Convert the change in SoC to kWh.
                energy_required_kwh = soc_to_kwh(soc_diff)

            veh_en_cons.append({
                'timestamp': row_1['timestamp'] + (row_2['timestamp'] - row_1['timestamp']) / 2,
                'energy_required_kwh': energy_required_kwh
            })

        veh_en_cons = pd.DataFrame(veh_en_cons, columns=['timestamp', 'energy_required_kwh'])

        # For each day, compute the average production per band, and multiply by 24 * 2.
        for day in range(365):
            start_day = datetime.datetime(2017, 1, 1, 0, 0) + datetime.timedelta(days=day)
            end_day = datetime.datetime(2017, 1, 1, 0, 0) + datetime.timedelta(days=day + 1)
            tot_cons = veh_en_cons[(start_day <= veh_en_cons['timestamp']) & (veh_en_cons['timestamp'] < end_day)]
            tot_cons = tot_cons['energy_required_kwh'].sum()
            data_to_plot.append({
                'uid': user_id,
                'day': start_day,
                'energy_required_kwh': tot_cons,
                'dow': start_day.weekday()
            })

    data_to_plot = pd.DataFrame(data_to_plot, columns=['day', 'energy_required_kwh', 'dow'])

    gs = GridSpec(1, 3)
    fig = plt.figure(figsize=(8, 3.5))
    axes = []
    axes.append(fig.add_subplot(gs[0, :-1]))
    axes.append(fig.add_subplot(gs[0, -1]))

    plt.sca(axes[0])
    plt.scatter(data_to_plot['day'], data_to_plot['energy_required_kwh'], s=2, alpha=0.5)
    axes[0].set_xlabel('Days in 2017 [d]')
    axes[0].set_ylabel('Energy Demand of EV [kWh]')

    plt.sca(axes[1])
    sns.boxplot(x="dow", y="energy_required_kwh", data=data_to_plot, ax=axes[1])
    axes[1].set_xlabel('Weekdays')
    axes[1].set_ylabel('Energy Demand of EV [kWh]')

    plt.savefig('plots/energy_demand_ev.png', bbox_inches='tight', dpi=300)
