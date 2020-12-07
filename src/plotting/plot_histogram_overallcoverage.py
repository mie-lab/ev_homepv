'''
Created on Oct 4, 2018

@author: rene
'''

import os

import pandas as pd
import seaborn as sns
from src.plotting.myplotlib import init_figure, Columnes, Journal, save_figure
import numpy as np
import matplotlib.pyplot as plt

def plot_hist(df, column_name, ax):


    sns.histplot(data=df[column_name],
                 bins=np.arange(0, 101, 5), ax=ax,
                )

    # sns.distplot(df[column_name],
    #              bins=np.arange(0, 101, 5),
    #              kde=False,
    #              # rug=True,
    #              # color="#4f6228",
    #              hist_kws=dict(edgecolor="darkgrey", alpha=1.0),
    #              ax=ax)





if __name__ == '__main__':

    journal = Journal.POWERPOINT_A3

    df = pd.read_csv(os.path.join('data', 'output', 'coverage_by_scenario.csv'))
    df = df*100
    column_names = ['baseline', 'scenario1', 'scenario2', 'scenario3']
    titles = ['Baseline', 'Scenario 1', 'Scenario 2', 'Scenario 3']
    output_path = os.path.join(os.getcwd(), "plots", "histogram", f"hist_coverage.png")


    fig, axs = init_figure(nrows=2,
                        ncols=2,
                        columnes=Columnes.ONE,
                        journal=journal,
                        sharex=True, sharey=True)

    for ix, column_name in enumerate(column_names):

        ax = axs[ix // 2, ix % 2]
        plot_hist(df, column_name, ax=ax)
        ax.set_title(titles[ix] + f" - mean: {df[column_name].mean():.0f} \%")
        # ax.grid(which='both')
        ax.set_xlabel(None)
        ax.set_ylabel(None)
        ax.grid(b=True, which='both')

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.set_yticks([10, 20, 30, 40, 50, 60], minor=True)

    # labels
    # https://stackoverflow.com/questions/16150819/common-xlabel-ylabel-for-matplotlib-subplots
    fig.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    # ax = plt.gca()
    # ax.set_xticks([2, 4, 6, 8, 10])
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    plt.xlabel("Home charging energy demand covered by PV [\%]", labelpad=15)
    plt.ylabel("User count", labelpad=15)
    plt.grid(b=False, which='both')


    # plt.xlim(0, 100)
    # plt.ylim(0, 700)
    # ax.set_ylabel("User count", labelpad=20)
    # ax.set_xlabel(r"Home charging energy demand covered by PV [\%]", labelpad=20)
    save_figure(output_path)

