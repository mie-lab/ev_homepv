# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 17:17:17 2020

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

output_folder = os.path.join('.', 'data', 'output')

# baseline = pd.read_csv(os.path.join(output_folder, 'results_baseline.csv'))
# baseline = parse_dates(baseline)

# scenario1 = pd.read_csv(os.path.join(output_folder, 'results_scenario1.csv'))
# scenario1 = parse_dates(scenario1)

# scenario2 = pd.read_csv(os.path.join(output_folder, 'results_scenario2.csv'))
# scenario2 = parse_dates(scenario2)

# scenario3 = pd.read_csv(os.path.join(output_folder, 'results_scenario3.csv'))
# scenario3 = parse_dates(scenario3)

                                    

def add_roof_area(df):
    
    all_vins = df.index.tolist()
    for vin in all_vins:
        user_id = get_user_id(vin)
        area_factor = get_area_factor_for_user(user_id)
        
        pv = PVModel(user_id, area_factor=area_factor)
        df.loc[vin, 'area'] = pv.area
        df.loc[vin, 'user'] = int(user_id)

def return_ols_values(x, y):
    xx = sm.add_constant(x, prepend=False)
    mod = sm.OLS(y, xx)
    res = mod.fit()
    pval = res.pvalues
    params = res.params
    rsquared = res.rsquared
    
    logging.debug('\t\t' + f'pval demand: {pval[0]:.2E}')
    logging.debug('\t\t' + f'pval area: {pval[1]:.2E}')
    
    logging.debug('\t\t' + f'coef demand: {params[0]:.2E} [%/kWh]')
    logging.debug('\t\t' + f'coef area: {params[1]:.2E}  [%/m2]')
    
    logging.debug('\t\t' + f'rsquared: {rsquared:.2f}')

    print(res.summary())
    

if __name__ == '__main__':
    
    df = pd.read_csv(os.path.join('data', 'output', 'coverage_by_scenario.csv'))
    df.set_index('vin', inplace=True)
    df['area'] = 0
    df['user'] = 0
    add_roof_area(df) 
    
    column_names = ['baseline', 'scenario1', 'scenario2', 'scenario3']
    df[column_names] = df[column_names] * 100 # in %
    # df['total_demand'] = df['total_demand'] / 1000 # in MWh
    
    for column_name in column_names:
        logging.debug("\t" + column_name)
        x = df.loc[:, ['total_demand', 'area']].values.reshape(-1,2)
        y = df[column_name].values.reshape(-1,1)
        return_ols_values(x, y)
        
        
    # logging.debug("area")
    # for column_name in column_names:
    #     logging.debug("\t" + column_name)
    #     x = df['area'].values.reshape(-1,1)
    #     y = df[column_name].values.reshape(-1,1)
    #     return_ols_values(x, y)
        
    # plt.scatter(df['total_demand'], df['baseline'], s=df['area'])
    # plt.scatter(df['total_demand'], df['scenario1'], s=df['area'])
    # plt.scatter(df['total_demand'], df['scenario2'], s=df['area'])
    # plt.scatter(df['total_demand'], df['scenario3'], s=df['area'])
    plt.subplots()
    plt.scatter(df['area'], df['baseline'])
    plt.scatter(df['area'], df['scenario1'])
    plt.scatter(df['area'], df['scenario2'])
    plt.scatter(df['area'], df['scenario3'])
    plt.xlabel("Roof area")
    plt.ylabel("coverage")
    
    

     