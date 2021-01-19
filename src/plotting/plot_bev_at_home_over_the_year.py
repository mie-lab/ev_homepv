# plt.legend()
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import datetime
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from src.methods.helpers import soc2remainingCharge
from src.methods.PV_interface import get_PV_generated, get_area_factor_for_user
import pandas as pd
import seaborn as sns
from src.plotting.myplotlib import init_figure, Columnes, Journal, save_figure
from src.methods.pv_swissbuildings_json import PVModel
import numpy as np
from src.methods.helpers import get_user_id
import statsmodels.api as sm
import scipy
import logging
import warnings
from mpl_toolkits.axes_grid1 import make_axes_locatable
"""
Calendar heatmaps from Pandas time series data.
Plot Pandas time series data sampled by day in a heatmap per calendar year,
similar to GitHub's contributions calendar.
Based on Martijn Vermaat's calmap:  https://github.com/martijnvermaat/calmap
"""

import calendar
import datetime

from matplotlib.colors import ColorConverter, ListedColormap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_dates(data_raw):
    data = data_raw.copy()
    data['start'] = pd.to_datetime(data['start'])
    data['end'] = pd.to_datetime(data['end'])

    return data


logging.basicConfig(
    filename='roof_consumption_coverage.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

def prepare_df(s1):

    s1['end'] = s1['end'] - pd.Timedelta(seconds=1)
    assert np.all(s1['start'] < s1['end'])

    s1['value'] = 0
    s1.loc[s1.is_home, 'value'] = 1

    s1_start = s1[['start', 'value', 'vin']].copy()
    s1_start['tstamp'] = s1_start['start']

    s1_end = s1[['end', 'value', 'vin']].copy()
    s1_end['tstamp'] = s1_end['end']

    s11 = pd.concat((s1_start[['tstamp', 'value', 'vin']], s1_end[['tstamp', 'value', 'vin']]))
    s11 = s11.set_index('tstamp')

    return s11

output_folder = os.path.join('.', 'data', 'output', 'PVMODEL_SPV170')
fig_out = os.path.join('plots', 'bev_at_home_over_year', 'bev_at_home_over_year.png')

# baseline = pd.read_csv(os.path.join(output_folder, 'results_baseline.csv'))
# baseline = parse_dates(baseline)

s1 = pd.read_csv(os.path.join(output_folder, 'results_scenario1.csv'))
s1 = parse_dates(s1)


s11 = prepare_df(s1)
all_users = s11.vin.unique()
user_df_resampled_list = []
nb_users = all_users.shape[0]
# user_this = all_users[0]
at_home_time_list = []
for user_this in all_users:
    df = s11[s11['vin'] == user_this]
    df = pd.DataFrame(df['value'])

    # resample dataframe of 1 user
    # https://stackoverflow.com/questions/49191998/pandas-dataframe-resample-from-irregular-timeseries-index/55654486
    resample_index = pd.date_range(start=df.index[0], end=df.index[-1], freq='1min')
    dummy_frame = pd.DataFrame(np.NaN, index=resample_index, columns=['value'])
    user_df_resampled = df.combine_first(dummy_frame).interpolate('time')

    # aggregate to 1 hour. Every hour has now the fraction of the time that 1 user was at home
    user_df_resampled = user_df_resampled.resample('1H').sum()/60
    user_df_resampled_list.append(user_df_resampled)

    # at_home_time_list.append(user_df_resampled.max())

all_users_df = pd.concat(user_df_resampled_list, axis=1).mean(axis=1)
all_users_df = pd.DataFrame(all_users_df, columns=['value'])
all_users_df['hour'] = all_users_df.index.hour
all_users_df['day'] = all_users_df.index.floor('D')

matrix = all_users_df.pivot(index=['day'], columns=['hour'], values='value')
matrix = matrix.transpose()

# plot
journal = Journal.POWERPOINT_A3
fig, ax = init_figure(nrows=1,
                       ncols=1,
                       fig_height_mm=150,
                        # height_scale=5.0,
                       columnes=Columnes.ONE,
                       journal=journal,
                      disabled_spines=[],
                      # gridspec_kw={"height_ratios":[1, 0.05]})
                             )

plt.sca(ax)
# sns.heatmap(matrix, ax=ax)
im = ax.imshow(matrix, aspect='auto', cmap='viridis')
# PCM=ax.get_children()[-2] #get the mappable, the 1st and the 2nd are the x and y axes
# plt.colorbar(PCM, ax=ax)

# plt.colorbar()
plt.grid(b=None)
plt.xlabel("Days in study")
plt.ylabel("Hours of the day")

plt.yticks([0, 6, 12, 18, 24])

# fig.colorbar(im, cax=cax, orientation="horizontal")
im.set_clim([0, 1])
# cb = fig.colorbar(im, orientation="horizontal", pad=0.5, shrink=0.5)
divider = make_axes_locatable(ax)
cax = divider.new_vertical(size="5%", pad=1.5, pack_start=True)
fig.add_axes(cax)
cb = fig.colorbar(im, cax=cax, orientation="horizontal", fraction=0.5)
cb.outline.set_visible(False)
cb.set_label("Percentage of cars at home")
# cb.set_ticks(np.arange(0, 1.2, 0.2))
# cb.ax.set_xticklabels(np.arange(0, 1.2, 0.2))
# plt.savefig(fig_out[:-3] + "pdf")
# plt.close()
save_figure(fig_out, dpi=10)