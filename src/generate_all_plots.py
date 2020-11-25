import os
from os.path import join as osp


os.system(f'python ./src/plotting/plot_power_factor.py')
os.system(f'python ./src/plotting/plot_cumsum_charging_strategies.py')
os.system(f'python ./src/plotting/plot_co2_usage_over_year.py')
os.system(f'python ./src/plotting/plot_user_coverage_over_year.py')
os.system(f'python ./src/plotting/plot_soc_over_time_singleuser_rawdata.py')


print("done")