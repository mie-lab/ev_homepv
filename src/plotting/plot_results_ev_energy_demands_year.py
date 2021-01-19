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
from src.methods.helpers import get_user_id, deltasoc2tocharge, soc2remainingCharge
from src.plotting.myplotlib import init_figure, Columnes, Journal, save_figure
import warnings
import numpy as np
from src.methods.loading_and_preprocessing import load_and_prepare_baseline_data, compute_additional_columns
from src.calculate_scenarios import get_cached_csv

def soc_to_kwh(soc_diff):

    return deltasoc2tocharge(-soc_diff)


if __name__ == "__main__":

    data_folder = os.path.join('.', 'data')
    car_is_at_home_file = os.path.join(data_folder, 'Car_is_at_home_table_UTC.csv')
    fig_out = os.path.join('plots', 'energy_demand_ev', 'energy_demand_ev.png')

    data = pd.read_csv(car_is_at_home_file, parse_dates=['start'])

    # load baseline data
    filepath_baseline = os.path.join(data_folder, 'data_baseline.csv')
    data_baseline = load_and_prepare_baseline_data(filepath_baseline)

    # calculate consumption
    delta_soc = data_baseline['soc_start'] - data_baseline['soc_end']
    delta_soc = np.maximum(np.zeros(delta_soc.shape), delta_soc.values)
    consumption_car = list(map(deltasoc2tocharge, delta_soc))
    data_baseline['energy_required_kwh'] = consumption_car


    data_baseline['day'] = data_baseline['start'].dt.floor('d')
    daily_user_consumption = data_baseline.groupby(by=['vin', 'day'])['energy_required_kwh'].sum()
    daily_user_consumption = daily_user_consumption.reset_index()
    daily_user_consumption['dow'] = daily_user_consumption['day'].dt.weekday
    data_to_plot = daily_user_consumption.copy()
    #raw_bmw_file = os.path.join(data_folder, 'bmw_soc_overtime_data.csv')

    #raw_bmw_data = pd.read_csv(raw_bmw_file, parse_dates=['timestamp_start_local', 
    #    'timestamp_end_local', 'timestamp_start_utc', 'timestamp_end_utc'])

    # all_vehicles = set(data['vin'].unique())
    #
    # data_to_plot = []
    # for vehicle in all_vehicles:
    #     veh_en_cons = []
    #     raw_bmw_data_vehicle = data[data['vin'] == vehicle].copy()
    #     raw_bmw_data_vehicle = raw_bmw_data_vehicle.sort_values(['start'])
    #
    #     # Go through everything in pairs, compute the difference between pairs.
    #     for (idx_1, row_1), (idx_2, row_2) in zip(raw_bmw_data_vehicle[:-1].iterrows(),
    #                                               raw_bmw_data_vehicle[1:].iterrows()):
    #         t_diff = row_2['start'] - row_1['start']
    #         soc_diff = row_2['total_segment_consumption']
    #         if soc_diff >= 0:
    #             energy_required_kwh = 0
    #         else:
    #             # In case the difference is negative, energy was consumed. Convert the change in SoC to kWh.
    #             energy_required_kwh = soc_to_kwh(soc_diff)
    #
    #         veh_en_cons.append({
    #             'start': row_1['start'] + (row_2['start'] - row_1['start']) / 2,
    #             'energy_required_kwh': energy_required_kwh
    #         })
    #
    #     veh_en_cons = pd.DataFrame(veh_en_cons, columns=['start', 'energy_required_kwh'])
    #
    #     # For each day, compute the average production per band, and multiply by 24 * 2.
    #     for day in range(365 - 31):  # Only from February to December.
    #         start_day = datetime.datetime(2017, 2, 1, 0, 0) + datetime.timedelta(days=day)
    #         end_day = datetime.datetime(2017, 2, 1, 0, 0) + datetime.timedelta(days=day + 1)
    #         tot_cons = veh_en_cons[(start_day <= veh_en_cons['start']) & (veh_en_cons['start'] < end_day)]
    #         tot_cons = tot_cons['energy_required_kwh'].sum()
    #         data_to_plot.append({
    #             'vid': vehicle,
    #             'day': start_day,
    #             'energy_required_kwh': tot_cons,
    #             'dow': start_day.weekday()
    #         })



    data_to_plot = pd.DataFrame(data_to_plot, columns=['day', 'energy_required_kwh', 'dow'])

    # mask missing data
    dates_to_exclude = [datetime.datetime(2017, 9, 30, 0, 0) + datetime.timedelta(days=i) for i in range(7)]
    data_exclude_ix = data_to_plot['day'].isin(dates_to_exclude)
    data_to_plot.loc[data_exclude_ix, 'energy_required_kwh'] = np.nan

    journal = Journal.POWERPOINT_A3
    fig, axes = init_figure(nrows=1, ncols=2,
                            columnes=Columnes.ONE, fig_height_mm=120,
                            journal=journal, sharex=False, sharey=False,
                            gridspec_kw={'width_ratios': [2, 1]})

    plt.sca(axes[0])
    sns.lineplot(data=data_to_plot, x="day", y="energy_required_kwh",
                 linewidth=2, ax=axes[0], ci=95, estimator=np.median, err_kws={'alpha':0.4})
    axes[0].set_xlabel('Days in 2017 [d]')
    axes[0].set_ylabel('Energy Demand of EV per day [kWh]')
    axes[0].set_ylim([-2, 30])
    x_dates = pd.date_range(start=datetime.datetime(2017, 1, 1, 0, 0),
                            end=datetime.datetime(2017, 12, 31, 0, 0),
                            freq='M',) + datetime.timedelta(days=1)
    axes[0].set_xticks(x_dates[::2])
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    plt.sca(axes[1])
    sns.boxplot(x="dow", y="energy_required_kwh", data=data_to_plot, ax=axes[1],
                flierprops={'alpha':.1, 'marker':'+'}, color='k')
    axes[1].set_xlabel('Weekdays')
    axes[1].set_ylabel('')
    # axes[1].set_ylabel('Energy Demand of EV [kWh]')
    axes[1].set_ylim([-2, 30])
    axes[1].set_xticks([0, 1, 2, 3, 4, 5, 6])
    axes[1].set_xticklabels(['M', 'T', 'W', 'T', 'F', 'S', 'S'])

    for patch in axes[1].artists:
        r, g, b, a = patch.get_facecolor()
        patch.set_facecolor((r, g, b, .4))

    plt.subplots_adjust(wspace=0.18)

    save_figure(fig_out, dpi=30)

    print(data_to_plot.groupby('dow').median())