'''
Created on Oct 4, 2018

@author: rene
'''

import os

import pandas as pd
import seaborn as sns
from myplotlib import init_figure, Columnes, Journal, save_figure
import numpy as np

def plot_hist(df, column_name, output_path, ylim=(0, 55)):
    journal = Journal.POWERPOINT_A3

    f, ax = init_figure(nrows=1,
                        ncols=1,
                        columnes=Columnes.ONE,
                        journal=journal)

    sns.distplot(df[column_name],
                 bins=np.arange(0, 101, 5),
                 kde=False,
                 # rug=True,
                 # color="#4f6228",
                 hist_kws=dict(edgecolor="darkgrey", alpha=1.0),
                 ax=ax)

    ax.set_ylabel("Frequency", labelpad=20)
    ax.set_xlabel(r"Home charging energy demand coverd by PV [\%]", labelpad=20)
    ax.set_xlim(0, 100)
    ax.set_ylim(ylim)
    save_figure(output_path)


if __name__ == '__main__':


    df = pd.read_csv(os.path.join('data', 'output', 'coverage_by_scenario.csv'))
    df = df*100
    column_names = ['baseline', 'scenario1', 'scenario2', 'scenario3']
    for column_name in column_names:

        output_path = os.path.join(".", "plots", "histogram", f"hist_{column_name}.png")
        plot_hist(df, column_name, output_path, ylim=(0, 55))



