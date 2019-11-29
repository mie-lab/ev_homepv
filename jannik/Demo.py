from jannik.methods.loading_and_preprocessing import load_car_data, preprocess_car_data
from jannik.methods.merge_PV_and_car import compute_additional_columns
import pandas as pd

from pathlib import Path, PureWindowsPath

filename = PureWindowsPath("C:/Users/hamperj/private/ev_homepv/jannik/tests/toy_data/car_is_at_home_data.csv")
filepath = Path(filename)
filepath = 'data\car_is_at_home_toy_data.csv'

#filepath = 'C:\\Users\\hamperj\\private\\ev_homepv\\jannik\\tests\\toy_data\\car_is_at_home_data.csv'

data = load_car_data(filepath)
preprocessed_data = preprocess_car_data(data)
data_with_columns = compute_additional_columns(preprocessed_data)

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
print(data_with_columns)

