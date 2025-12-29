"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin
>>> Last Updated : 2025-10-12
----------------------------------------------------------------------
"""

import pandas as pd
import numpy as np
import torch, bz2
from typing import Optional
from torch.utils.data import random_split, Subset
from sklearn.datasets import load_svmlight_file
from sklearn.preprocessing import StandardScaler
from junshan_kit import ParametersHub


class CSV_TO_Pandas:
    def __init__(self):
        pass
    
    def _trans_time_fea(self, df, time_info: dict):
        """
        Transform and extract time-based features from a specified datetime column.

        This function converts a given column to pandas datetime format and
        extracts different time-related features based on the specified mode.
        It supports two extraction modes:
        - type = 0: Extracts basic components (year, month, day, hour)
        - type = 1: Extracts hour, day of week, and weekend indicator

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame containing the datetime column.
        time_info: 
            - time_col_name : str
                Name of the column containing time or datetime values.
            - trans_type : int, optional, default=1
                - 0 : Extract ['year', 'month', 'day', 'hour']
                - 1 : Extract ['hour', 'dayofweek', 'is_weekend']

        Returns
        -------
        pandas.DataFrame
            The DataFrame with newly added time-based feature columns.

        Notes
        -----
        - Rows that cannot be parsed as valid datetime will be dropped automatically.
        - 'dayofweek' ranges from 0 (Monday) to 6 (Sunday).
        - 'is_weekend' equals 1 if the day is Saturday or Sunday, otherwise 0.

        Examples
        --------
        >>> import pandas as pd
        >>> data = pd.DataFrame({
        ...     'timestamp': ['2023-08-01 12:30:00', '2023-08-05 08:15:00', 'invalid_time']
        ... })
        >>> df = handler._trans_time_fea(data, {"time_col_name": "timestamp", "trans_type": 1})
        >>> print(df)
                    timestamp  hour  dayofweek  is_weekend
        0 2023-08-01 12:30:00    12          1           0
        1 2023-08-05 08:15:00     8          5           1
        """
    
        time_col_name, trans_type = time_info['time_col_name'], time_info['trans_type']

        df[time_col_name] = pd.to_datetime(df[time_col_name], errors="coerce")

        # Drop rows where the datetime conversion failed, and make an explicit copy
        df = df.dropna(subset=[time_col_name]).copy()

        if trans_type == 0:
            df.loc[:, "year"] = df[time_col_name].dt.year
            df.loc[:, "month"] = df[time_col_name].dt.month
            df.loc[:, "day"] = df[time_col_name].dt.day
            df.loc[:, "hour"] = df[time_col_name].dt.hour

            user_text_fea = ['year','month','day', 'hour']
            df = pd.get_dummies(df, columns=user_text_fea, dtype=int)

        elif trans_type == 1:
            df.loc[:, "hour"] = df[time_col_name].dt.hour
            df.loc[:, "dayofweek"] = df[time_col_name].dt.dayofweek
            df.loc[:, "is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)

            user_text_fea = ['hour','dayofweek','is_weekend']
            df = pd.get_dummies(df, columns=user_text_fea, dtype=int)

        elif trans_type == 2:
            df.loc[:, "year"] = df[time_col_name].dt.year
            df.loc[:, "month"] = df[time_col_name].dt.month
            df.loc[:, "day"] = df[time_col_name].dt.day


            user_text_fea = ['year','month','day']
            df = pd.get_dummies(df, columns=user_text_fea, dtype=int)
        else:
            print("error!")

        df = df.drop(columns=[time_col_name])

        return df

    def preprocess_dataset(
        self,
        df,
        drop_cols: list,
        label_col: str,
        label_map: dict,
        title_name: str,
        user_one_hot_cols=[],
        print_info=False,
        time_info: dict | None = None,
        missing_strategy = 'drop',  # [drop, mode]
    ):
        """
        Preprocess a CSV dataset by performing data cleaning, label mapping, and feature encoding.

        This function loads a dataset from a CSV file, removes specified non-feature columns,
        drops rows with missing values, maps the target label to numerical values, and
        one-hot encodes categorical features. Optionally, it can print dataset statistics
        before and after preprocessing.

        Args:
            csv_path (str):
                Path to the input CSV dataset.
            drop_cols (list):
                List of column names to drop from the dataset.
            label_col (str):
                Name of the target label column.
            label_map (dict):
                Mapping dictionary for label conversion (e.g., {"yes": 1, "no": -1}).
            print_info (bool, optional):
                Whether to print preprocessing information and dataset statistics.
                Defaults to False.
            title_name (str):
                Title used for the summary table or report that documents
                the preprocessing steps and dataset statistics.

        Returns:
            pandas.DataFrame:
                The cleaned and preprocessed dataset ready for model input.

        Steps:
            1. Load the dataset from CSV.
            2. Drop non-informative or irrelevant columns.
            3. Remove rows with missing values.
            4. Map label column to numerical values according to `label_map`.
            5. One-hot encode categorical (non-label) text features.
            6. Optionally print dataset information and summary statistics.

        Example:
            >>> label_map = {"positive": 1, "negative": -1}
            >>> df = data_handler.preprocess_dataset(
            ...     csv_path="data/raw.csv",
            ...     drop_cols=["id", "timestamp"],
            ...     label_col="sentiment",
            ...     label_map=label_map,
            ...     print_info=True
            ... )
        """
        # Step 0: Load the dataset
        # df = pd.read_csv(csv_path)
        columns = df.columns

        # Save original size
        m_original, n_original = df.shape

        # Step 1: Drop non-informative columns
        df = df.drop(columns=drop_cols)

        # Step 2: Remove rows with missing values
        if missing_strategy == 'drop':
            df = df.dropna(axis=0, how="any")

        elif missing_strategy == 'mode':
            for col in df.columns:
                if df[col].notna().any():  
                    mode_val = df[col].mode()[0]
                    df[col] = df[col].fillna(mode_val)

        m_encoded, n_encoded = df.shape

        if time_info is not None:
            df = self._trans_time_fea(df, time_info)

        # Step 3: Map target label (to 0 and +1)
        df[label_col] = df[label_col].map(label_map)

        # Step 4: Encode categorical features (exclude label column)
        text_feature_cols = df.select_dtypes(
            include=["object", "string", "category"]
        ).columns
        text_feature_cols = [
            col for col in text_feature_cols if col != label_col
        ]  # ✅ exclude label

        df = pd.get_dummies(
            df, columns=text_feature_cols + user_one_hot_cols, dtype=int
        )
        m_cleaned, n_cleaned = df.shape

        # print info
        if print_info:
            pos_count = (df[label_col] == 1).sum()
            neg_count = (df[label_col] == 0).sum()

            # Step 6: Print dataset information
            print("\n" + "=" * 80)
            print(f"{f'{title_name} - Summary':^70}")
            print("=" * 80)
            print(f"{'Original size:':<40} {m_original} rows x {n_original} cols")
            print(
                f"{'Dropped non-feature columns:':<40} {', '.join(drop_cols) if drop_cols else 'None'}"
            )
            print(f"{'missing_strategy:':<40} {missing_strategy}")
            print(
                f"{'Dropping NaN & non-feature cols:':<40} {m_encoded} rows x {n_encoded} cols"
            )
            print(f"{'Positive samples (1):':<40} {pos_count}")
            print(f"{'Negative samples (0):':<40} {neg_count}")
            print(
                f"{'Size after one-hot encoding:':<40} {m_cleaned} rows x {n_cleaned} cols"
            )
            print("-" * 80)
            print(f"{'More details about preprocessing':^70}")
            print("-" * 80)
            print(f"{'Label column:':<40} {label_col}")
            print(f"{'label_map:':<40} {label_map}")
            print(f"{'time column:':<40} {time_info}")
            if time_info is not None:
                if time_info["trans_type"] == 0:
                    print("- 0 : Extract ['year', 'month', 'day', 'hour']")
                elif time_info["trans_type"] == 1:
                    print("- 1 : Extract ['hour', 'dayofweek', 'is_weekend']")
                elif time_info["trans_type"] == 2:
                    print("- 2 : Extract ['year', 'month', 'day']")
                else:
                    assert False
            print(
                f"{'text fetaure columns:':<40} {', '.join(list(text_feature_cols)) if list(text_feature_cols) else 'None'}"
            )
            # print("-" * 80)
            # print("all columns:")
            # print(list(columns))
            print("=" * 80 + "\n")

        return df
    

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset

class Pandas_TO_Torch(Dataset):

    def __init__(self, df: pd.DataFrame, 
                label_col: str, 
                ):
        self.df = df
        self.label_col = label_col

        # Identify feature columns automatically (all except the label)
        self.label_col = label_col
        self.feature_cols = [col for col in self.df.columns if col != label_col]

        # Extract features and labels
        self.features = self.df[self.feature_cols].values.astype("float32")
        self.labels = self.df[self.label_col].values.astype("int64")


    def __len__(self):
        """Return the total number of samples."""
        return len(self.features)

    def __getitem__(self, idx):
        x = torch.tensor(self.features[idx], dtype=torch.float32)
        y = torch.tensor(self.labels[idx], dtype=torch.long)
        
        return x, y

    def __repr__(self):
        info = (
            f"Dataset CustomNumericDataset\n"
            f"    Number of datapoints: {len(self)}\n"
            f"    Features: {self.features.shape[1]}\n"
        )
        return info
    
    def to_torch(self, transform, seed=42):
        fea_cols = [col for col in self.df.columns if col != self.label_col]

        if transform["normalization"]:
            scaler = StandardScaler()
            self.df[fea_cols] = scaler.fit_transform(self.df[fea_cols])
        
        # Train/test split
        
        train_df, test_df = train_test_split(self.df, train_size=transform["train_size"], random_state=seed, stratify=self.df[self.label_col])
        
        # Create datasets
        train_dataset = Pandas_TO_Torch(train_df, self.label_col)
        test_dataset  = Pandas_TO_Torch(test_df, self.label_col)

        return train_dataset, test_dataset, transform


class TXT_TO_Numpy:
    def __init__(self):
        pass


class bz2_To_Numpy:
    def __init__(self):
        pass






class StepByStep:
    def __init__(self):
        pass

    def print_text_fea(self, df, text_feature_cols):
        for col in text_feature_cols:
            print(f"\n{'-'*80}")
            print(f'Feature: "{col}"')
            print(f"{'-'*80}")
            print(
                f"Unique values ({len(df[col].unique())}): {df[col].unique().tolist()}"
            )


class LibSVMDataset_bz2(Dataset):
    def __init__(self, path, data_name = None, Paras = None):
        with bz2.open(path, 'rb') as f:
            X, y = load_svmlight_file(f) # type: ignore

        self.X, self.path = X, path
        
        y = np.asanyarray(y)

        if data_name is not None:
            data_name = data_name.lower()

            # Binary classification, with the label -1/1
            if data_name in ["rcv1"]:
                y = (y > 0).astype(int)  # Convert to 0/1
            
            # Multi-category, labels usually start with 1
            elif data_name in [""]:  
                y = y - 1  # Start with 0

        else:
            # Default policy: Try to avoid CrossEntropyLoss errors
            if np.min(y) < 0:  # e.g. [-1, 1]
                y = (y > 0).astype(int)
            elif np.min(y) >= 1:
                y = y - 1

        self.y = y

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, idx):
        xi = torch.tensor(self.X.getrow(idx).toarray(), dtype=torch.float32).squeeze(0)
        yi = torch.tensor(self.y[idx], dtype=torch.float32)
        return xi, yi
    
    def __repr__(self):
        num_samples = len(self.y)
        num_features = self.X.shape[1]
        num_classes = len(np.unique(self.y))
        return (f"LibSVMDataset_bz2(\n"
                f"  num_samples = {num_samples},\n"
                f"  num_features = {num_features},\n"
                f"  num_classes = {num_classes}\n"
                f"  path = {self.path}\n"
                f")")
    
def get_libsvm_bz2_data(train_path, test_path, data_name, Paras, split = True):
    
    transform = "-1 → 0 for binary, y-1 for multi-class"
    train_data = LibSVMDataset_bz2(train_path)

    if data_name in ["Duke", "Ijcnn", "RCV1"]:
        test_data = LibSVMDataset_bz2(test_path)
        split = False
    else:
        test_data = Subset(train_data, [])
        
    
    if split:
        total_size = len(train_data)
        train_size = int(Paras["train_ratio"] * total_size)
        test_size = total_size - train_size

        train_dataset, test_dataset = random_split(train_data, [train_size, test_size])

    else:
        train_dataset = train_data
        # # Empty test dataset, keep the structure consistent
        # test_dataset = Subset(train_data, []) 
        test_dataset = test_data

    # print(test_dataset) 
    # assert False

    return train_dataset, test_dataset, transform


def subset(dataset, ratio_or_num, seed=None) -> Subset:
    """
    Randomly sample a subset from a dataset.

    Parameters
    ----------
    dataset : torch.utils.data.Dataset
        The dataset to sample from.
    ratio_or_num : float or int
        If float in (0, 1], treated as sampling ratio.
        Otherwise, treated as absolute number of samples.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    torch.utils.data.Subset
        A randomly sampled subset of the dataset.
    """

    if ratio_or_num < 0:
        raise ValueError(f"ratio_or_num must be non-negative, got {ratio_or_num}")

    dataset_len = len(dataset)

    # Determine number of samples
    if isinstance(ratio_or_num, float) and 0 < ratio_or_num <= 1:
        num = max(1, int(round(dataset_len * ratio_or_num)))
    else:
        num = int(ratio_or_num)

    # Clamp to valid range
    num = min(max(num, 1), dataset_len)

    # Create and seed generator
    generator = torch.Generator()
    if seed is not None:
        generator.manual_seed(seed)

    # Random sampling
    indices = torch.randperm(dataset_len, generator=generator)[:num].tolist()

    return Subset(dataset, indices)

    
def get_binary_dataset(dataset, class0, class1):
    # Method: directly filter the dataset (recommended)
        _indices = []

        # Get training set indices
        for i in range(len(dataset)):
            label = dataset[i][1]
            if label in [class0, class1]:
                _indices.append(i)

        # get the subset dataset
        _dataset = Subset(dataset, _indices)

        return _dataset

def get_one_shape(dataset):
    return dataset[0][0].shape

# class BinaryDataset(Dataset):
#     def __init__(self, dataset, class0: int, class1: int):
#         self.dataset = dataset
#         self.class0 = class0
#         self.class1 = class1
#         self.indices = [
#             i for i in range(len(dataset))
#             if dataset[i][1] in (class0, class1)
#         ]

#     def __len__(self):
#         return len(self.indices)

#     def __getitem__(self, idx):
#         x, y = self.dataset[self.indices[idx]]
#         y = 0 if y == self.class0 else 1
#         return x, y


# def get_binary_dataset(
#     dataset: Dataset,
#     class0: int,
#     class1: int
# ) -> Dataset:
#     return BinaryDataset(dataset, class0, class1)