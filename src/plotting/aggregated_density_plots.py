# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 13:04:40 2020

@author: henry
"""

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import os


if __name__ == '__main__':
    
    table = pd.read_csv(os.path.join('data', 'output', 'coverage_by_scenario.csv'))

    sns.displot(data=table, x='baseline', kind='kde', rug=True)
    plt.xlim([0,1])
    plt.title("Scenario Baseline - mean {:.2f}".format(table['baseline'].mean()))
    plt.savefig(os.path.join('plots', 'Baseline_PV_model'))
    # plt.close()

    sns.displot(data=table, x='scenario1', kind='kde', rug=True)
    plt.xlim([0,1])
    plt.title("Scenario 1 - mean {:.2f}".format(table['scenario1'].mean()))
    plt.savefig(os.path.join('plots', 'Scenario1_PV_model'))
    # plt.close()

    sns.displot(data=table, x='scenario2', kind='kde', rug=True)
    plt.xlim([0,1])
    plt.title("Scenario 2 - mean {:.2f}".format(table['scenario2'].mean()))
    plt.savefig(os.path.join('plots', 'Scenario2_PV_model'))
    # plt.close()

    sns.displot(data=table, x='scenario3', kind='kde', rug=True)
    plt.xlim([0,1])
    plt.title("Scenario 3 - mean {:.2f}".format(table['scenario3'].mean()))
    plt.savefig(os.path.join('plots', 'Scenario3_PV_model'))
    # plt.close()

    