import os
from os.path import join as osp
import glob
import shutil
import ntpath

# # #
os.system(f'python ./src/plotting/plot_pv_generation_year.py')
os.system(f'python ./src/plotting/plot_results_ev_energy_demands_year.py')
os.system(f'python ./src/plotting/plot_bev_at_home_over_the_year.py')
os.system(f'python ./src/plotting/plot_scatter_roof_consumption_coverate.py')
os.system(f'python ./src/plotting/plot_cumsum_charging_strategies.py')
os.system(f'python ./src/plotting/plot_co2_usage_over_year.py')
os.system(f'python ./src/plotting/plot_histogram_overallcoverage.py')
os.system(f'python ./src/plotting/plot_user_coverage_over_year.py')
os.system(f'python ./src/plotting/plot_panel_sensitivity.py')
os.system(f'python ./src/plotting/plot_soc_over_time_singleuser_rawdata.py')
os.system(f'python ./src/plotting/plot_power_factor.py')
# not used nor finalized os.system(f'python ./src/plotting/plot_charging_schedule_for_all_scenarios.py')


all_folders = glob.glob(os.path.join("plots", "*", ""))
target_folder_name = "zzz_all_pdfs"
target_folder = os.path.join("plots", target_folder_name)
for folder in all_folders:
    if target_folder in folder:
        continue
    filepath_ = glob.glob(os.path.join(folder, "*crop.pdf"))
    for filepath in filepath_:
        filename = ntpath.basename(filepath)
        shutil.copyfile(filepath, os.path.join(target_folder, filename))

print("done")