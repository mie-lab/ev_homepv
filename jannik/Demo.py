from jannik.methods.loading_and_preprocessing import load_car_data, preprocess_car_data
from jannik.methods.compute_additional_columns import compute_additional_columns
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path, PureWindowsPath

from jannik.methods.scenarios_for_users import create_scenario_table, scenario_1

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



filepath = "../../Car_is_at_home_table.csv"




data = load_car_data(filepath)
preprocessed_data = preprocess_car_data(data)
data_with_columns = compute_additional_columns(preprocessed_data)

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
print(data_with_columns)


battery_capacity = 20

table = create_scenario_table(data_with_columns, battery_capacity)
print(table)

plt.xlim(0, 1)
sns.distplot(table['Scenario 1'], hist=False, rug=True)
print(f"mean: {np.mean(table['Scenario 1'])}")
plt.savefig('Scenario 1')
plt.show()


plt.xlim(0, 1)
sns.distplot(table['Scenario 2'], hist=False, rug=True)
plt.savefig('Scenario 2')
plt.show()


plt.xlim(0, 1)
sns.distplot(table['Scenario 3'], hist=False, rug=True)
plt.savefig('Scenario 3')
plt.show()
