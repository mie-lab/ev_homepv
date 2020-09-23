'''
Created on Oct 4, 2018

@author: rene
'''

import os
import pprint

import matplotlib
import matplotlib.pyplot as plt
from myplotlib import init_figure, Columnes, Journal, save_figure
import pandas as pd
import seaborn as sns

if __name__ == '__main__':

    journal = Journal.POWERPOINT_A3

    f, ax = init_figure(nrows=1,
                        ncols=1,
                        columnes=Columnes.ONE,
                        journal=journal)

    df = pd.read_csv(os.path.join("..", "data_PV_Solar", "results_v1_nodouble.csv"))
    df = df.drop(df[(df['pv_cover_home_ratio'] <= 0)].index)

    sns.distplot(df['pv_cover_home_ratio'],
                 bins=20,
                 kde=False,
                 rug=True,
                 color="#4f6228",
                 hist_kws=dict(edgecolor="darkgrey", alpha=1.0),
                 ax=ax)
#     ax.hist(x=df['pv_cover_home_ratio'],
#             bins=20)

    ax.set_ylabel("Frequency", labelpad=20)
    ax.set_xlabel(r"Home charging energy demand coverd by PV [\%]", labelpad=20)
    ax.set_xlim(0, 100)

    save_figure(os.path.join("..", "plots", "hist_pv_cover_home.png"))


# ln, = ax.plot(x, y,
#               linestyle='--',
#               color='r',
#               linewidth=0.51,
#               label=r"${} * \Delta_{{soc}}  + {} * \sqrt{{ \Delta_{{soc}} }}$, $R^2 = {}$".format(round(paras['dsoc'], 3),
#                                                                                                   round(paras['np.sqrt(dsoc)'], 3),
#                                                                                                   round(r2, 2)))
