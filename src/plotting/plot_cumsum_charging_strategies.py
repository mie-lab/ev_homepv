# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 14:23:16 2020

@author: henry
"""

# plt.legend()
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import datetime 

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from src.methods.helpers import soc2remainingCharge
from src.methods.PV_interface import get_PV_generated



def plot_cumsum_by_scenario(data_raw, ax, label=None):
    data = data_raw.copy()

    cumsum_saldo = (data['charged_from_pv'] - data['charged_from_outside']).cumsum()
    cumsum_total_consumption = data['needed_by_car'].cumsum()

    ax.plot(cumsum_total_consumption, cumsum_saldo, label=label)

def parse_dates(data_raw):
    data = data_raw.copy()
    data['start'] = pd.to_datetime(data['start'])
    data['end'] = pd.to_datetime(data['end'])
    
    return data


output_folder = os.path.join('.', 'data', 'output')

baseline = pd.read_csv(os.path.join(output_folder, 'results_baseline.csv'))
baseline = parse_dates(baseline)

scenario1 = pd.read_csv(os.path.join(output_folder, 'results_scenario1.csv'))
scenario1 = parse_dates(scenario1)

scenario2 = pd.read_csv(os.path.join(output_folder, 'results_scenario2.csv'))
scenario2 = parse_dates(scenario2)

scenario3 = pd.read_csv(os.path.join(output_folder, 'results_scenario3.csv'))
scenario3 = parse_dates(scenario3)




f, ax = plt.subplots()
plot_cumsum_by_scenario(baseline[baseline.is_home], ax, label='baseline')
plot_cumsum_by_scenario(scenario1[scenario1.is_home], ax, label='scenario1')
plot_cumsum_by_scenario(scenario2, ax, label='scenario2')
plot_cumsum_by_scenario(scenario3, ax, label='scenario3')

xlim = plt.xlim()
plt.plot(np.arange(0, xlim[1]), np.arange(0, xlim[1]), label='x=y (only using pv generation)', color='k', 
         linestyle=':')
plt.plot(np.arange(0, xlim[1]), - np.arange(0, xlim[1]), label='x=-y (only using grid generation)', color='k', 
         linestyle=':')

ylim = plt.ylim()
ylim = (ylim[0], xlim[1])
ax.set_ylim(ylim)
plt.xlabel('total energy used by car (cumulative)')
plt.ylabel('energy charged from pv - energy charged from grid')
plt.legend()

plt.savefig(os.path.join('plots', 'cumsum_all_scenarios.png'))