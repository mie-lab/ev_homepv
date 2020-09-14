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
    relevant_columns = ['vin', 'start', 'soc_start', 'is_home', 'end', 'soc_end', 'total_segment_consumption']
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
    data = data.drop(
        data[
            data['vin'] == 'e4aac45c1a674b721f2e3edf2b385fca'].index)  # delete that column as house data does not exist

    data = data.drop(
        data[
            data['vin'] == '00006bbc00f87b6d42ddf1589d2a45b6'].index)  # delete that column as vin to user ID mapping does not exist

    data = data.drop(
        data[
            data[
                'vin'] == '0001496d0daa2bb38fdecfb8ec639145'].index)  # delete that column as vin to user ID mapping does not exist

    data = data.drop(
        data[
            data[
                'vin'] == '0007c68aeb7ff4a95b3ba97fc0c142ed'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '003b39715b2736c263b14fbbff239b29'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '004e95457957c238d263e44db976ab64'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '006a79d82a40efeb156ed4db4675d9ce'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '00774485b3a0ec6f1d72181af7aa3bc6'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '00a0e0b03bf164ce962ff23c9e3c15e9'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0152fcd6049c74edb2e5e1119bfa65d7'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '02ffd5d15fe21d4a0537573b8f605415'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0573edfe65925de7d7def42143eb3f8f'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '05cf2acb2174f9962db4eb56eacf9ddd'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '06e3e1a3151e99e11c902721e25a5839'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '080857683e8e4e34316a79b07af8123d'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0876314af13ab88e8dafd41cf88f5139'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '08e26ea55f741801141c5b77216c843f'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '08ef62af248b9208348ad293eab4f1a7'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0a875dcb2b38748cb9537f37a9f48b10'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0afd5f3da115745cbab130e2cb607812'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0e6ec6ffb28979c4afb3ebe4af7274e4'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0fa9031ab3239b5949c57bf7a9abe2a7'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '0fb416cac595d207143ee26230d7f74a'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '2552357d4d60a6b211d0ce4d46a73249'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data['vin'] == '2bda8c8d3cde1c63e3c43bd8507de8b0'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data['vin'] == '47274133826e35cdc6b4139f5c6dd113'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data['vin'] == '4c5acf8392125d59685fccd583b8fa4b'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data['vin'] == '59444c69b5f8932561fd115485b3cffc'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data['vin'] == '6f13f5ee5129ad3c15ce573ee77152ff'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data['vin'] == '709475ceb9f0c73b6469a88068816c1c'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data['vin'] == '87845b273fbb71a38cd5379bce6a842f'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == '9c55223837a5be104d6b794ca64914a6'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == 'a411eecca8a77ad8e5ed4e3085c07fc7'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == 'e0d8c66f3d54112243c037b06c2bac26'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == 'eefae320ef4361f15816453887f44836'].index)  # delete that column as vin to user ID mapping does not exist
    data = data.drop(
        data[
            data[
                'vin'] == 'eefae320ef4361f15816453887f44836'].index)  # delete that column as vin to user ID mapping does not exist

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
