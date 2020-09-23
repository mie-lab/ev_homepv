# -*- coding: utf-8 -*-
"""
Created on Tue Aug 28 2018

@author: martinhe
"""

import os
import numpy as np
import pandas as pd
from statsmodels.formula.api import ols
from sqlalchemy import create_engine

import matplotlib 
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.pyplot import tight_layout

from plotting.myplotlib import init_figure, Columnes, Journal, save_figure
from db_login import DSN


try:
    df = pd.read_csv(os.path.join('..','data_PV_Solar','power_factor_data.csv'))

except FileNotFoundError:
    engine = create_engine('postgresql://{user}:{password}@{host}' + 
    ':{port}/{dbname}'.format(**DSN))
    

    query = """SELECT soc_customer_start, soc_customer_end,
                consumed_electric_energy_total
                from bmw where zustand = 'fahrt'"""

    df = pd.read_sql_query(query, con=engine)
    df.to_csv(os.path.join('..','data_PV_Solar','power_factor_data.csv'))

#data_PV_Solar preparation
df['dsoc'] = df['soc_customer_start'] - df['soc_customer_end']
df['pow'] = df['consumed_electric_energy_total']

# filter all that is zero
df = df.drop(df[(df['dsoc'] <= 0) | (df['pow'] <= 0)].index)


# create plot
f, ax = init_figure(nrows=1,
                    ncols=1,
                    columnes=Columnes.ONE,
                    journal=Journal.POWERPOINT_A3)

hb = ax.hexbin(df['dsoc'],
               df['pow'],
               gridsize=100,
               bins='log',
               cmap=plt.get_cmap('bone_r'),
               mincnt=1,
               linewidths=0.2,
               edgecolors='slategray')

cb = f.colorbar(hb, ax=ax)
cb.set_label('log10(n), n = Number of data_PV_Solar points in cell', labelpad=20)

ax.set_ylabel(r"Consumed power [\si{\kilo\watthour}]", labelpad=20)
ax.set_xlabel(r'Change in state of charge ($\Delta_{{SoC}}$) [$\%$]', labelpad=20)

ax.set_xlim(0, 100)
ax.set_ylim(0, 32)




# Fit sqrt model
model = ols("pow ~ dsoc + np.sqrt(dsoc) - 1", df)
results = model.fit()
r2_sqrt = results.rsquared
params_sqrt= results.params

# Fit linear model
model_lin = ols("pow ~ dsoc -1", df)
results_lin = model_lin.fit()
r2_lin = results_lin.rsquared
params_lin = results_lin.params

# Plot regression
x = np.linspace(0,100, 30)
y = x * params_sqrt['dsoc'] + np.sqrt(x) * params_sqrt['np.sqrt(dsoc)']
y_lin = x * params_lin['dsoc']


ln_sqrt, = ax.plot(x, y,
              linestyle='--',
              color='r',
              linewidth=3,
              label="${} * \Delta_{{SoC}}  + {} * ".format(
                          round(params_sqrt['dsoc'], 3),
                          round(
                          params_sqrt['np.sqrt(dsoc)'], 3)) + \
                  "\sqrt{{ \Delta_{{SoC}} }}$, $R^2 = {}$".format(
                          round(r2_sqrt, 2))
                )
#
ln_lin, = ax.plot(x, y_lin,
              linestyle=':',
              color='orange',
              linewidth=3,
#              label="${} * \Delta_{{SoC}}$,  $R^2 = {}$".format(
#                      round(params_lin['dsoc'], 3), round(r2_lin, 2))
              label='linear fit',
              zorder=10 # draw this line on top
                )

leg = ax.legend(handles=[ln_sqrt, ln_lin], loc=2)
leg.set_zorder(20)
frame = leg.get_frame()
frame.set_facecolor('#ebefe8')
# frame.set_edgecolor('#ebefe8')

ax.text(0.99, 0.01, r"N = \num{{ {} }}".format(df.shape[0]),\
        horizontalalignment='right', verticalalignment='bottom',\
        transform=ax.transAxes)


save_figure(os.path.join("..", "plots", "power_factor.png"),
            dpi=600)


# #calculate power factor
# lr = LinearRegression(fit_intercept=True)
# 
# lr.fit(df['dsoc'].values.reshape(-1,1), df['pow'].values)
# lr.coef_
# lr.intercept_
# 
# y_pred = lr.predict(df['dsoc'].values.reshape(-1,1))
# 
# plt.plot(df['dsoc'].values.reshape(-1,1),y_pred, linestyle=':', color = 'lightcoral', label='Linear trend', linewidth=3)
# plt.legend()
# 
# fig.savefig(figure_path + '\\power_factor.pdf')
# plt.close(fig)

