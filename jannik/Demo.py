import pickle

from jannik.methods.PV_interface import get_PV_generated
from jannik.methods.loading_and_preprocessing import load_car_data, preprocess_car_data, load_baseline_car_data
from jannik.methods.compute_additional_columns import compute_additional_columns
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path, PureWindowsPath
import copy
from jannik.methods.scenarios_for_users import create_scenario_table

import os
import numpy as np


def readFile(filename):
    filehandle = open(filename)
    print (filehandle.read())
    filehandle.close()

fileDir = os.path.dirname(os.path.realpath('__file__'))
print (fileDir)
filename = os.path.join(fileDir, '../same.txt')
print(filename)

# filepath = 'data\car_is_at_home_toy_data.csv' # toy data
filepath = "C:/Users/hamperj/private/Car_is_at_home_data.csv"

#filepath = 'C:\\Users\\hamperj\\private\\ev_homepv\\jannik\\tests\\toy_data\\car_is_at_home_data.csv'

current_dir = os.getcwd()
print(current_dir)



filepath = "../../Car_is_at_home_table_new.csv"
filepath_baseline  = "../../data_baseline_new.csv"


data_baseline = load_baseline_car_data(filepath_baseline)
data = load_car_data(filepath)


#filename = f"data_scenario_2"
#with open(filename, "rb") as f:
#    data_scenario_2 = pickle.load(f)

data_scenario_2 = copy.deepcopy(data)
data_scenario_2["generated_by_PV"] = [get_PV_generated(data_scenario_2["start"][data_scenario_2.index[i]],
                                                          data_scenario_2["end"][data_scenario_2.index[i]],
                                                          data_scenario_2["vin"][data_scenario_2.index[i]]
                                                          ) for i in range(len(data_scenario_2.index))]
with open(filename, 'wb') as f:
    pickle.dump(data_scenario_2, f)


preprocessed_data = preprocess_car_data(data)
data_with_columns = compute_additional_columns(preprocessed_data)

filename = f"preprocessed_data"
with open(filename, 'wb') as f:
    pickle.dump(data_scenario_2, f)

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
print(data_with_columns)


battery_capacity = 20

table = create_scenario_table(data_baseline, data_scenario_2, data_with_columns, battery_capacity)
print(table)


plt.xlim(0, 1)
sns.distplot(table['Baseline'], hist=False, rug=True)
#print(f"mean: {np.mean(table['Scenario 1'])}")
plt.savefig('Baseline_new_PV_model')
plt.show()

plt.xlim(0, 1)
sns.distplot(table['Scenario 1'], hist=False, rug=True)
print(f"mean: {np.mean(table['Scenario 1'])}")
plt.savefig('Scenario 1_new_PV_model')
plt.show()


plt.xlim(0, 1)
sns.distplot(table['Scenario 2'], hist=False, rug=True)
plt.savefig('Scenario 2_new_PV_model')
plt.show()


plt.xlim(0, 1)
sns.distplot(table['Scenario 3'], hist=False, rug=True)
plt.savefig('Scenario 3_new_PV_model')
plt.show()
