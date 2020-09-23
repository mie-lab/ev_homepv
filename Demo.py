import pickle

from src.methods.PV_interface import get_PV_generated
from src.methods.helpers import validate_data
from src.methods.loading_and_preprocessing import load_car_data, preprocess_car_data, load_baseline_car_data
from src.methods.compute_additional_columns import compute_additional_columns
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import copy
from src.methods.scenarios_for_users import create_scenario_table

import os
import numpy as np


def readFile(filename):
    filehandle = open(filename)
    print (filehandle.read())
    filehandle.close()

#fileDir = os.path.dirname(os.path.realpath('__file__'))
#print (fileDir)
#filename = os.path.join(fileDir, '../same.txt')
#print(filename)

# filepath = 'data_PV_Solar\car_is_at_home_toy_data.csv' # toy data_PV_Solar
#filepath = "C:/Users/hamperj/private/Car_is_at_home_data.csv"

#filepath = 'C:\\Users\\hamperj\\private\\ev_homepv\\jannik\\tests\\toy_data\\car_is_at_home_data.csv'

#current_dir = os.getcwd()
#print(current_dir)



path_to_data_folder = os.getcwd()
path_to_data_folder = os.path.abspath(os.path.join(path_to_data_folder, os.pardir))
path_to_data_folder= os.path.join(path_to_data_folder, 'data_homepv')
print(path_to_data_folder)


filepath = os.path.join(path_to_data_folder, 'car_is_at_home_table.csv')
filepath_baseline  = os.path.join(path_to_data_folder, 'data_baseline.csv')



data_baseline = load_baseline_car_data(filepath_baseline)
data = load_car_data(filepath)

#data = data.head(1000)
#data_baseline = data_baseline.head(100000)


data_baseline = validate_data(data_baseline, 'vin', path_to_data_folder)
data = validate_data(data, 'vin', path_to_data_folder)



data_scenario_2 = copy.deepcopy(data)
data_scenario_2["generated_by_PV"] = [get_PV_generated(data_scenario_2["start"][data_scenario_2.index[i]],
                                                          data_scenario_2["end"][data_scenario_2.index[i]],
                                                          data_scenario_2["vin"][data_scenario_2.index[i]], path_to_data_folder
                                                          ) for i in range(len(data_scenario_2.index))]


#battery_capacity = 20
battery_capacity = 13.5 #tesla power box.
battery_charging_power = 12 # Dauerbetrieb

preprocessed_data = preprocess_car_data(data)
data_with_columns = compute_additional_columns(preprocessed_data, path_to_data_folder, battery_charging_power)


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
print(data_with_columns)





table = create_scenario_table(data_baseline, data_scenario_2, data_with_columns, battery_capacity, battery_charging_power, path_to_data_folder)
print(table)
print("str table:")
print(str(table))
table.to_csv('table_validated.csv')

plt.xlim(0, 1)
sns.distplot(table['Baseline'], hist=False, rug=True)
#print(f"mean: {np.mean(table['Scenario 1'])}")
plt.savefig('Baseline_PV_model_validated')
plt.show()

plt.xlim(0, 1)
sns.distplot(table['Scenario 1'], hist=False, rug=True)
print(f"mean: {np.mean(table['Scenario 1'])}")
plt.savefig('Scenario 1_PV_model_validated')
plt.show()


plt.xlim(0, 1)
sns.distplot(table['Scenario 2'], hist=False, rug=True)
plt.savefig('Scenario 2_PV_model_validated')
plt.show()


plt.xlim(0, 1)
sns.distplot(table['Scenario 3'], hist=False, rug=True)
plt.savefig('Scenario 3_PV_model_validated')
plt.show()
