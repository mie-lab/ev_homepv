import pandas as pd

import copy
import os

def load_car_data(filepath, filter=True):
    """
    loads the car data from CSV and filters only relevant data if necessary

    Parameters
    ----------
    filepath : string
        string to where the data lies
    filter: boolean
        if true, only data relevant for the paper is selected

    Returns:
    data: pandas-df
        loaded data
    """
    data = pd.read_csv(filepath, sep = ',')
    relevant_columns = ['vin', 'start', 'soc_start', 'is_home', 'end', 'soc_end']
    if filter:
        data = data[relevant_columns]
    data = data.drop(data[data['vin'] == '0007f9c8534b7924352bed2b9842b1fc'].index) # delete that column as user has zero demand
    data = data.drop(
        data[data['vin'] == '003d3821dfaabc96fa1710c2128aeb62'].index)  # delete that column as user has zero demand
    data = data.drop(
        data[data['vin'] == '00478e28c489e344b1db9f3bdf9aac99'].index)  # delete that column as house data does not exist
    data = data.drop(
        data[
            data['vin'] == '4f3417a1c272af8c8ae31eeb8ce060f4'].index)  # delete that column as house data does not exist
    data = data.drop(
        data[
            data['vin'] == '8335678314417d1094b8b956bac57761'].index)  # delete that column as house data does not exist
    data = data.drop(
        data[
            data['vin'] == 'a2c77c6bfd36c79bab9d598575cbf6ab'].index)  # delete that column as house data does not exist


    return data

def load_baseline_car_data(filepath, filter=True):
    data = pd.read_csv(filepath, sep=',')

    data = data.drop(
        data[data['vin'] == '0007f9c8534b7924352bed2b9842b1fc'].index)  # delete that column as user has zero demand
    data = data.drop(
        data[data['vin'] == '003d3821dfaabc96fa1710c2128aeb62'].index)  # delete that column as user has zero demand
    data = data.drop(
        data[
            data['vin'] == '00478e28c489e344b1db9f3bdf9aac99'].index)  # delete that column as house data does not exist
    data = data.drop(
        data[
            data['vin'] == '4f3417a1c272af8c8ae31eeb8ce060f4'].index)  # delete that column as house data does not exist
    data = data.drop(
        data[
            data['vin'] == '8335678314417d1094b8b956bac57761'].index)  # delete that column as house data does not exist
    data = data.drop(
        data[
            data['vin'] == 'a2c77c6bfd36c79bab9d598575cbf6ab'].index)  # delete that column as house data does not exist


    #print(data)

    return data

def preprocess_car_data(data):
    """
    preprocesses the data:
    1) remove all entries where user is not at home
    2) compute the loaded energy (in SOC)

    Parameters
    ----------
    data: pandas dataframe
        data to be preprocessed

    Returns
    -------
    preprocessed_data: pandas dataframe
        data after preprocessing
    """
    preprocessed_data = copy.deepcopy(data)
    preprocessed_data = preprocessed_data.drop(preprocessed_data[preprocessed_data['is_home'] == False].index)
    preprocessed_data['delta_soc'] = preprocessed_data['soc_end'] - preprocessed_data['soc_start']

    return preprocessed_data

""" Do not touch PV data in this paper
def load_PV_data(directory_path):
    """
"""
    Reads in all JSON-files and converts them to one pandas-dataframe

    Parameters
    ----------
    directory_path: string
        path to directory where JSON-files are stored

    Returns
    -------
    PV_data: pandas df
        df containing the PV data
        """
"""
    directory = os.fsencode(directory_path)

    PV_data = None

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith("json"):
            full_filename = directory_path + "\\" + filename
            df = pd.read_json(full_filename,  typ='series', convert_axes=False)
            if(PV_data is None):
                PV_data = df
            else:
                PV_data = pd.concat([PV_data, df])
        else:
            continue

    PV_data = PV_data.to_frame()
    PV_data = PV_data.reset_index()
    PV_data = PV_data.rename(columns = {"index" : "JSON-key",0:"Energy"})
    return PV_data

def preprocess_PV_data(PV_data):
    """
"""
    
    preprocesses PV data:
    1) extracts household ID from JSON-key
    2) extracts start time from JSON-key
    3) create end time from JSON-key
    4) deletes JSON-key from JSON-key

    Parameters
    ----------
    PV_data: pandas df
        dataframe to be preprocessed

    Returns
    -------
    preprocessed_PV_data: pandas df
        preprocessed PV_data
        """
"""

    PV_data["household_id"] =
"""
