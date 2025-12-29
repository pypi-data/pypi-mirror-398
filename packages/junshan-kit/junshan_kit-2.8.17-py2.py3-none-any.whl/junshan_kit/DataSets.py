"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin  
>>> Last Updated : 2025-10-16
----------------------------------------------------------------------
"""

import os
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.io import savemat
import junshan_kit.DataProcessor
import junshan_kit.kit
from sklearn.preprocessing import StandardScaler

#----------------------------------------------------------
def _download_data(data_name, data_type):
    """
    Download and extract a dataset from Jianguoyun using either Firefox or Chrome automation.

    This helper function allows the user to manually provide a Jianguoyun download link,
    choose a browser (Firefox or Chrome) for automated downloading, and automatically unzip the downloaded dataset into a structured local directory.

    Args:
        data_name (str):
            The name of the dataset (used as a folder name for storage).

        data_type (str):
            The dataset category, e.g., "binary" or "multi".
            Determines the subdirectory under './exp_data/'.

    Raises:
        ValueError:
            If `data_type` is not one of the allowed options: ["binary", "multi"].

    Behavior:
        - Prompts the user to input a Jianguoyun download URL.
        - Lets the user select a download method (Firefox or Chrome).
        - Downloads the `.zip` file into `./exp_data/{data_name}/`.
        - Automatically extracts the zip file in the same directory.
        - Prints progress and completion messages.

    Example:
        >>> _download_data("mnist", "binary")
        Enter the Jianguoyun download URL: https://www.jianguoyun.com/p/abcd1234
        Select download method:
        1. Firefox
        2. Chrome
        Enter the number of your choice (1 or 2): 

    Note:
        Requires `junshan_kit` with `JianguoyunDownloaderFirefox`, 
        `JianguoyunDownloaderChrome`, and `unzip_file` utilities available.
    """
    allowed_types = ["binary", "multi"]
    if data_type not in allowed_types:
        raise ValueError(f"Invalid data_type: {data_type!r}. Must be one of {allowed_types}.")
    from junshan_kit.kit import JianguoyunDownloaderFirefox, JianguoyunDownloaderChrome

    # User selects download method
    while True:
        # User inputs download URL
        url = input("Enter the Jianguoyun download URL: ").strip()

        print("Select download method:")
        print("1. Firefox")
        print("2. Chrome")
        choice = input("Enter the number of your choice (1 or 2): ").strip()

        if choice == "1":
            JianguoyunDownloaderFirefox(url, f"./exp_data/{data_name}").run()
            print("*** Download completed using Firefox ***")
            break
        elif choice == "2":
            JianguoyunDownloaderChrome(url, f"./exp_data/{data_name}").run()
            print("*** Download completed using Chrome ***")
            break
        else:
            print("*** Invalid choice. Please enter 1 or 2 ***\n")

    # unzip file
    junshan_kit.kit.unzip_file(f'./exp_data/{data_name}/{data_name}.zip', f'./exp_data/{data_name}') 

def _export_csv(df, data_name, data_type):
    path = f'./exp_data/{data_name}/'
    os.makedirs(path, exist_ok=True)
    df.to_csv(path + f'{data_name}_num.csv', index=False)
    print(path + f'{data_name}.csv')


def _export_mat(df, data_name, label_col):
    # Extract label and feature matrices
    y = df[label_col].values                  # Target column
    X = df.drop(columns=[label_col]).values  # Feature matrix

    # Convert to sparse matrices
    X_sparse = csr_matrix(X)
    Y_sparse = csr_matrix(y.reshape(-1, 1))  # Convert target to column sparse matrix

    # Get number of samples and features
    m, n = X.shape

    # Save as a MAT file (supports large datasets)
    save_path = f'exp_data/{data_name}/{data_name}.mat'
    savemat(save_path, {'X': X_sparse, 'Y': Y_sparse, 'm': m, 'n': n}, do_compression=True)

    # Print confirmation
    print("Sparse MAT file saved to:", save_path)
    print("Number of samples (m):", m)
    print("Number of features (n):", n)


def _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, user_one_hot_cols = [], export_csv = False, time_info = None, df = None, missing_strategy = 'drop', Paras = None):
    
    if csv_path is not None and not os.path.exists(csv_path):
        print('\n' + '*'*60)
        print(f"Please download the data.")
        print(csv_path)
        _download_data(data_name, data_type=data_type) 

    if not os.path.exists(f"./exp_data/{data_name}"):
        print('\n' + '*'*60)
        print(f"Please download the data.")
        print(f"./exp_data/{data_name}")
        _download_data(data_name, data_type=data_type) 

    if df is None:
        df = pd.read_csv(csv_path)

    cleaner = junshan_kit.DataProcessor.CSV_TO_Pandas()
    df = cleaner.preprocess_dataset(df, drop_cols, label_col, label_map, title_name=data_name, user_one_hot_cols=user_one_hot_cols, print_info=print_info, time_info = time_info, missing_strategy = missing_strategy)

    if export_csv:
        _export_csv(df, data_name, data_type)
    
    if Paras is not None and Paras["export_mat"]:
        _export_mat(df, data_name, label_col)

    return df



# ********************************************************************
"""
----------------------------------------------------------------------
                            Datasets
----------------------------------------------------------------------
"""

def credit_card_fraud_detection(data_name = "Credit_Card_Fraud_Detection", print_info = False, export_csv=False, drop_cols = []):

    data_type = "binary"
    csv_path = f'exp_data/{data_name}/creditcard.csv'
    label_col = 'Class' 
    label_map = {0: 0, 1: 1}
    

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)
    

    return df


def diabetes_health_indicators(data_name = "Diabetes_Health_Indicators", print_info = False, export_csv = False, drop_cols = [], Standard = False):
    data_type = "binary"
    csv_path = f'exp_data/{data_name}/diabetes_dataset.csv'
    label_col = 'diagnosed_diabetes'
    label_map = {0: 0, 1: 1}
    
    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)

    return df


def electric_vehicle_population(data_name = "Electric_Vehicle_Population", print_info = False, export_csv = False, drop_cols = ['VIN (1-10)', 'DOL Vehicle ID', 'Vehicle Location'], Standard = False):

    data_type = "binary"
    csv_path = f'exp_data/{data_name}/Electric_Vehicle_Population_Data.csv'
    # drop_cols = ['VIN (1-10)', 'DOL Vehicle ID', 'Vehicle Location']
    label_col = 'Electric Vehicle Type'
    label_map = {
    'Battery Electric Vehicle (BEV)': 1,
    'Plug-in Hybrid Electric Vehicle (PHEV)': 0
    }
    

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)

    return df

def global_house_purchase(data_name = "Global_House_Purchase", print_info = False, export_csv = False, drop_cols = ['property_id'], Standard =False):

    data_type = "binary"
    csv_path = f'exp_data/{data_name}/global_house_purchase_dataset.csv'
    label_col = 'decision'
    label_map = {0: 0, 1: 1}
    

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)

    return df


def health_lifestyle(data_name = "Health_Lifestyle", print_info = False, export_csv = False, drop_cols = ['id'], Standard =False):

    data_type = "binary"
    csv_path = f'exp_data/{data_name}/health_lifestyle_dataset.csv'
    
    label_col = 'disease_risk'
    label_map = {0: 0, 1: 1}
    

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)

    return df


def medical_insurance_cost_prediction(data_name = "Medical_Insurance_Cost Prediction", print_info = False, export_csv = False, drop_cols = ['alcohol_freq'], Standard = False):
    """
    1. The missing values in this dataset are handled by directly removing the corresponding column. Since the `alcohol_freq` column contains a large number of missing values, deleting the rows would result in significant data loss, so the entire column is dropped instead.

    2. There are several columns that could serve as binary classification labels, such as `is_high_risk`, `cardiovascular_disease`, and `liver_disease`. In this case, `is_high_risk` is chosen as the label column.
    """

    data_type = "binary"
    csv_path = f'exp_data/{data_name}/medical_insurance.csv'
    
    label_col = 'is_high_risk'
    label_map = {0: -1, 1: 1}
    

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)

    return df


def particle_physics_event_classification(data_name = "Particle_Physics_Event_Classification", print_info = False, export_csv = False, drop_cols = [], Standard =False):

    data_type = "binary"
    csv_path = f'exp_data/{data_name}/Particle Physics Event Classification.csv'
    
    label_col = 'Label'
    label_map = {'s': -1, 'b': 1}
    

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)

    return df



def adult_income_prediction(data_name = "Adult_Income_Prediction", print_info = False, export_csv=False, drop_cols = [], Standard = False):

    data_type = "binary"
    csv_path = f'./exp_data/{data_name}/adult.csv'
    
    label_col = 'income'
    label_map = {'<=50K': 0, '>50K': 1}
    

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv)

    return df


def TamilNadu_weather_2020_2025(data_name = "TN_Weather_2020_2025", print_info = False, export_csv = False, drop_cols = ['Unnamed: 0'], Standard = False):

    data_type = "binary"
    csv_path = f'./exp_data/{data_name}/TNweather_1.8M.csv'
    
    label_col = 'rain_tomorrow'
    label_map = {0: 0, 1: 1}

    time_info = {
        'time_col_name': 'time',
        'trans_type': 0
    }

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv, time_info=time_info)


    return df

def YouTube_Recommendation(data_name = "YouTube_Recommendation", print_info = False, export_csv = False, drop_cols = ['user_id']):

    data_type = "binary"
    csv_path = f'./exp_data/{data_name}/youtube recommendation dataset.csv'
    
    label_col = 'subscribed_after'
    label_map = {0: -1, 1: 1}

    # Extraction mode.
    # - 0 : Extract ['year', 'month', 'day', 'hour']
    # - 1 : Extract ['hour', 'dayofweek', 'is_weekend']
    # - 2 : Extract ['year', 'month', 'day']
    time_info = {
        'time_col_name': 'timestamp',
        'trans_type': 1
    }
    
    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv, time_info=time_info)

    return df


def Santander_Customer_Satisfaction(data_name = "Santander_Customer_Satisfaction", print_info = False, export_csv = False):
    data_type = "binary"
    csv_path = None

    drop_cols = ['ID_code']
    label_col = 'target'
    label_map = {False: 0, True: 1}

    df, y, categorical_indicator, attribute_names = junshan_kit.kit.download_openml_data(data_name)

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv, df=df)

    return df


def newsgroups_drift(data_name = "20_newsgroups.drift", print_info = False, export_csv = False):
    data_type = "binary"
    csv_path = None

    drop_cols = ['ID_code']
    label_col = 'target'
    label_map = {False: 0, True: 1}

    df, y, categorical_indicator, attribute_names = junshan_kit.kit.download_openml_data(data_name)

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv, df=df)

    return df


def Homesite_Quote_Conversion(data_name = "Homesite_Quote_Conversion", print_info = False, export_csv = False):
    data_type = "binary"
    csv_path = None
    missing_strategy = 'mode'

    drop_cols = ['QuoteNumber']
    label_col = 'QuoteConversion_Flag'
    label_map = {0: 0, 1: 1}

    time_info = {
        'time_col_name': 'Original_Quote_Date',
        'trans_type': 2
    }

    df, y, categorical_indicator, attribute_names = junshan_kit.kit.download_openml_data(data_name)

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv, df=df, time_info = time_info, missing_strategy = missing_strategy)

    return df

def IEEE_CIS_Fraud_Detection(data_name = "IEEE-CIS_Fraud_Detection", print_info = False, export_csv = False, export_mat = False):
    data_type = "binary"
    csv_path = None
    missing_strategy = 'mode'

    drop_cols = ['TransactionID']
    label_col = 'isFraud'
    label_map = {0: 0, 1: 1}

    Paras = {
        "export_mat": export_mat
    }

    df, y, categorical_indicator, attribute_names = junshan_kit.kit.download_openml_data(data_name)

    df = _run(csv_path, data_name, data_type, drop_cols, label_col, label_map, print_info, export_csv=export_csv, df=df, missing_strategy = missing_strategy, Paras = Paras)

    return df



