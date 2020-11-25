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
        df.loc[vin, 'max_kW'] = pv.max_W/1000
        
        pvdict = pv.data['PVMODEL_SPV170']
        to_pop_list = ['year_Wh_dc', 'year_Wh_ac', 'year_inv_eff', 'max_W']
        for to_pop in to_pop_list:
            pvdict.pop(to_pop)
        df.loc[vin, 'max_gen_kw'] = max(list(pvdict.values()))*2/1000 * area_factor
        
        # print(pv.max_W/1000, max(list(pv.data['PVMODEL_SPV170'].values()))/2/1000)

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
    # plt.subplots()
    # plt.scatter(df['area'], df['baseline'])
    # plt.scatter(df['area'], df['scenario1'])
    # plt.scatter(df['area'], df['scenario2'])
    # plt.scatter(df['area'], df['scenario3'])
    # plt.xlabel("Roof area")
    # plt.ylabel("coverage")
    
    

### hist of kwp distribution
# https://de.enfsolar.com/pv/panel-datasheet/crystalline/36658
cell_area_m2 = 156/1000 * 156/1000
kwp_per_cell = (170/36)/1000
kwpm2_cell = kwp_per_cell / cell_area_m2

df['kwp_cell'] = df['area'] * kwpm2_cell
# plt.figure()


# plt.hist(df['max_W']/1000, bins=20)


     