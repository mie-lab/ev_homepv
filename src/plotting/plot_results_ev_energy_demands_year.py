import datetime
import math
import os
import sys
sys.path.append('.')

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
import seaborn as sns

from src.methods.helpers import get_user_id
from src.plotting.myplotlib import init_figure, Columnes, Journal, save_figure
import warnings


def soc_to_kwh(soc_diff):
    soc_diff = -soc_diff
    warnings.warn("Check if this is formula currently used in the paper")
    return 0.293 * soc_diff + 0.232 * math.sqrt(soc_diff)


if __name__ == "__main__":
    data_folder = os.path.join('.', 'data')

    car_is_at_home_file = os.path.join(data_folder, 'Car_is_at_home_table_UTC.csv')
    data = pd.read_csv(car_is_at_home_file, parse_dates=['start'])
    #raw_bmw_file = os.path.join(data_folder, 'bmw_soc_overtime_data.csv')

    #raw_bmw_data = pd.read_csv(raw_bmw_file, parse_dates=['timestamp_start_local', 
    #    'timestamp_end_local', 'timestamp_start_utc', 'timestamp_end_utc'])

    all_vehicles = set(data['vin'].unique())

    data_to_plot = []
    for vehicle in all_vehicles:
        veh_en_cons = []
        raw_bmw_data_vehicle = data[data['vin'] == vehicle].copy()
        raw_bmw_data_vehicle = raw_bmw_data_vehicle.sort_values(['start'])

        # Go through everything in pairs, compute the difference between pairs.
        for (idx_1, row_1), (idx_2, row_2) in zip(raw_bmw_data_vehicle[:-1].iterrows(),
                                                  raw_bmw_data_vehicle[1:].iterrows()):
            t_diff = row_2['start'] - row_1['start']
            soc_diff = row_2['total_segment_consumption']
            if soc_diff >= 0:
                energy_required_kwh = 0
            else:
                # In case the difference is negative, energy was consumed. Convert the change in SoC to kWh.
                energy_required_kwh = soc_to_kwh(soc_diff)

            veh_en_cons.append({
                'start': row_1['start'] + (row_2['start'] - row_1['start']) / 2,
                'energy_required_kwh': energy_required_kwh
            })

        veh_en_cons = pd.DataFrame(veh_en_cons, columns=['start', 'energy_required_kwh'])

        # For each day, compute the average production per band, and multiply by 24 * 2.
        for day in range(365 - 31):  # Only from February to December.
            start_day = datetime.datetime(2017, 2, 1, 0, 0) + datetime.timedelta(days=day)
            end_day = datetime.datetime(2017, 2, 1, 0, 0) + datetime.timedelta(days=day + 1)
            tot_cons = veh_en_cons[(start_day <= veh_en_cons['start']) & (veh_en_cons['start'] < end_day)]
            tot_cons = tot_cons['energy_required_kwh'].sum()
            data_to_plot.append({
                'vid': vehicle,
                'day': start_day,
                'energy_required_kwh': tot_cons,
                'dow': start_day.weekday()
            })

    data_to_plot = pd.DataFrame(data_to_plot, columns=['day', 'energy_required_kwh', 'dow'])

    journal = Journal.POWERPOINT_A3
    fig, axes = init_figure(nrows=1, ncols=2,
                            columnes=Columnes.ONE, fig_height_mm=120,
                            journal=journal, sharex=False, sharey=False,
                            gridspec_kw={'width_ratios': [2, 1]})

    plt.sca(axes[0])
    sns.lineplot(data=data_to_plot, x="day", y="energy_required_kwh",
                 linewidth=3, ax=axes[0])
    axes[0].set_xlabel('Days in 2017 [d]')
    axes[0].set_ylabel('Energy Demand of EV [kWh]')
    axes[0].set_ylim([0, 30])
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    plt.sca(axes[1])
    sns.boxplot(x="dow", y="energy_required_kwh", data=data_to_plot, ax=axes[1])
    axes[1].set_xlabel('Weekdays')
    axes[1].set_ylabel('')
    # axes[1].set_ylabel('Energy Demand of EV [kWh]')
    axes[1].set_ylim([0, 30])
    axes[1].set_xticks([0, 1, 2, 3, 4, 5, 6])
    axes[1].set_xticklabels(['M', 'T', 'W', 'T', 'F', 'S', 'S'])

    plt.subplots_adjust(wspace=0.18)

    plt.savefig('plots/energy_demand_ev.png', bbox_inches='tight', dpi=300)
