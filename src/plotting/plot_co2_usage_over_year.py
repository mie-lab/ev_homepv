# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 20:38:18 2020

@author: henry
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import datetime
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from src.methods.helpers import soc2remainingCharge
from src.methods.PV_interface import get_PV_generated
import pandas as pd
import seaborn as sns
from src.plotting.myplotlib import init_figure, Columnes, Journal, save_figure
from src.methods.pv_swissbuildings_json import PVModel
import numpy as np
from src.methods.helpers import get_user_id
import statsmodels.api as sm
import scipy 
import logging

def parse_dates(data_raw):
    data = data_raw.copy()
    data['start'] = pd.to_datetime(data['start'])
    data['end'] = pd.to_datetime(data['end'])
    
    return data

def reshape_for_quantile_plot(df):
    df = df.pivot(index='vin', values='coverage', columns='start')
    return df.columns, df.values #(x, y)

import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot') # this was just used for the examples

# data
CO2_pv = 53.6/1000 # kg/kWh
# for switzerland: Verbraucher-Strommix: 
# https://www.bafu.admin.ch/bafu/de/home/themen/klima/klimawandel--fragen-und-antworten.html#-1202736887
# CO2_swissmix = 181.1/1000  # kg/kWh https://www.bafu.admin.ch/bafu/de/home/themen/klima/klimawandel--fragen-und-antworten.html#-1202736887
CO2_swissmix = 401/1000 
# 181.1 = schweiz
# 401 = Germany
# 5000 charge cycles / 1 cycle per day = 13.6986301369863 years of lifetime
# https://iea-pvps.org/key-topics/environmental-life-cycle-assessment-of-residential-pv-and-battery-storage-systems/
# Emissions are 76.1 gco2/kwh
# Prospective LCA of the production and EoL recycling of a novel type of Li-ion battery for electric vehicles
bat_co2_kwh = 76.1
bat_cap_kwh = 13.5
bat_lifetime_weeks = 5000/365 * 52
gCO2_storage_week = bat_cap_kwh * bat_co2_kwh / bat_lifetime_weeks

fig_out = os.path.join('plots', 'co2_plot', 'plot_average_co2_over_year.png')

def get_aggr_df(df):
    
    df = df.groupby(['vin', pd.Grouper(key='start',
                                freq='W-MON')])
    
    df = df[['needed_by_car', 'charged_from_pv', 'charged_from_outside']].sum()
    df = df.reset_index().sort_values('start')
    
    df.fillna(0, inplace=True)
    
    df['co2'] = df['charged_from_pv'] * CO2_pv + \
        df['charged_from_outside'] * CO2_swissmix
    
    too_old = datetime.datetime.strptime('2018-01-01 00:00:00', '%Y-%m-%d %M:%H:%S')
    df = df[df['start'] < too_old]
    
    return df



if __name__ == '__main__':
    output_folder = os.path.join('.', 'data', 'output', 'PVMODEL_SPV170')
    
    baseline = pd.read_csv(os.path.join(output_folder, 'results_baseline.csv'))
    baseline = parse_dates(baseline)
    df_b = get_aggr_df(baseline)
    
    scenario1 = pd.read_csv(os.path.join(output_folder, 'results_scenario1.csv'))
    scenario1 = parse_dates(scenario1)
    df_s1 = get_aggr_df(scenario1)
    
    scenario2 = pd.read_csv(os.path.join(output_folder, 'results_scenario2.csv'))
    scenario2 = parse_dates(scenario2)
    df_s2 = get_aggr_df(scenario2)
    
    scenario3 = pd.read_csv(os.path.join(output_folder, 'results_scenario3.csv'))
    scenario3 = parse_dates(scenario3) 
    df_s3 = get_aggr_df(scenario3)

    df_s3['co2'] = df_s3['co2'] + gCO2_storage_week
    
    df_b['scenario'] = 'Baseline'
    df_s1['scenario'] = 'Scenario 1'
    df_s2['scenario'] = 'Scenario 2'
    df_s3['scenario'] = 'Scenario 3'
    
    df_all = pd.concat((df_b, df_s1, df_s2, df_s3))
    
    journal = Journal.POWERPOINT_A3
    
    fig, ax = init_figure(nrows=1,
                            ncols=1,
                            columnes=Columnes.ONE,
                            journal=journal, sharex=True, sharey=True)
    
    sns.lineplot(data=df_all, x="start", y="co2", hue="scenario",
                 linewidth=3, ax=ax)
    
    # ax.set_xticks(ax.get_xticks()[::2]) # skip every second tick
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    # ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    
    
   
 
    handles, labels = ax.get_legend_handles_labels()
     
    for handle in handles:
        handle.set_linewidth(3)
        # handle._linewidth = 50
        
    leg = ax.legend(handles=handles, labels=labels,
                    loc='upper left', frameon=False, bbox_to_anchor=(-0.15, -0.15), 
                    ncol=4)
        
        
    plt.xlabel("Time of tracking aggregated by week", labelpad=15)
    plt.ylabel(r"Emissions per Person in $\frac{\text{kg CO2 equivalent}}{\text{week}}$", labelpad=20)
        
    bbox_extra_artists = [fig,  leg]
    save_figure(fig_out, bbox_extra_artists=bbox_extra_artists)
    plt.close(fig)         
    
    
    # calculate average Co2 savings per user
    df_avco2 = df_all.groupby('scenario')['co2'].mean()
    df_avco2  = df_avco2.Baseline - df_avco2 
    

    # data_list = [df_b, df_s1, df_s2, df_s3]
    # journal = Journal.POWERPOINT_A3
    
    # fig, axs = init_figure(nrows=2,
    #                         ncols=2,
    #                         columnes=Columnes.ONE,
    #                         journal=journal, sharex=True, sharey=True)
    # # fig, axs = plt.subplots(2,2)

    # title_list = ['Baseline', 'Scenario 1', 'Scenario 2', 'Scenario 3']
    # for ix, data in enumerate(data_list):
    #     ax = axs[ix//2, ix%2]
    #     t, y = reshape_for_quantile_plot(data)
    #     ax = tsplot(t, y, n=1, percentile_min=5, percentile_max=95, plot_median=True, ax=ax, plot_scatter=True, color='g', line_color='navy', alpha=0.3)
    #     ax = tsplot(t, y, n=1, percentile_min=25, percentile_max=75, ax=ax,  plot_median=False,  color='g', line_color='navy', alpha=0.5)
        
    #     ax.set_xticks(ax.get_xticks()[::2]) # skip every second tick
    #     ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    #     # ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    #     ax.set_title(title_list[ix])
    
    # # labels 
    # # https://stackoverflow.com/questions/16150819/common-xlabel-ylabel-for-matplotlib-subplots
    # fig.add_subplot(111, frameon=False)
    # # hide tick and tick label of the big axis
    # plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    # plt.xlabel("Time of tracking aggregated by week", labelpad=15)
    # plt.ylabel("Percentage of energy demand covered by PV", labelpad=20)

    # # plt.ylabel('Energy demand covered by PV')
    # # legend    
    # handles, labels = ax.get_legend_handles_labels()

    
    # leg = plt.figlegend(handles=handles, labels=labels, loc='upper left',
    #                     ncol=2, frameon=False,
    #                     bbox_to_anchor=(0.15, 0), labelspacing=0.1,
    #                     columnspacing=0.1)
    # leg.legendHandles[1].set_alpha(1) # no alpha for scatter circle
    # # leg.legendHandles[1]._sizes = [500]
    # leg.legendHandles[1].set_sizes([200])
        
    # bbox_extra_artists = [fig,  leg]
    
    # # save
    # save_figure(os.path.join('plots', 'quantile_plots', 'plot_quantile_coverage_year.png'), bbox_extra_artists=bbox_extra_artists,  dpi=100)
    # plt.close(fig)    




