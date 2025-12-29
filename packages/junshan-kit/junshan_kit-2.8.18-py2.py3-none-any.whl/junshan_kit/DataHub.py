"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin  
>>> Last Updated : 2025-10-28
----------------------------------------------------------------------
"""

import torchvision
import torchvision.transforms as transforms
from torch.utils.data import random_split, Subset
from typing import List, Callable
from junshan_kit import DataSets, DataProcessor, Print_Info

def Adult_Income_Prediction(seed=42, print_info = False):

    df = DataSets.adult_income_prediction(print_info=print_info) 
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='income'

    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform

def Credit_Card_Fraud_Detection(seed=42, print_info = False):
    df = DataSets.credit_card_fraud_detection(print_info=print_info)
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='Class'

    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform

def Diabetes_Health_Indicators(seed=42, print_info = False):
    df = DataSets.diabetes_health_indicators(print_info=print_info)
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='diagnosed_diabetes'

    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform

def Electric_Vehicle_Population(seed=42, print_info = False): 
    df = DataSets.electric_vehicle_population(print_info=print_info)
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='Electric Vehicle Type'
    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform

def Global_House_Purchase(seed=42, print_info = False): 
    df = DataSets.global_house_purchase(print_info=print_info)
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='decision'
    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform

def Health_Lifestyle(seed=42, print_info = False): 
    df = DataSets.health_lifestyle(print_info=print_info)
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='disease_risk'
    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform

def Homesite_Quote_Conversion(seed=42, print_info = False): 
    df = DataSets.Homesite_Quote_Conversion(print_info=print_info)
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='QuoteConversion_Flag'
    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform

def TN_Weather_2020_2025(seed=42, print_info = False): 
    df = DataSets.TamilNadu_weather_2020_2025(print_info=print_info)
    transform = {
        "train_size": 0.7,
        "normalization": True
    }
    label_col='rain_tomorrow'
    train_dataset, test_dataset, transform = DataProcessor.Pandas_TO_Torch(df, label_col).to_torch(transform, seed)

    return train_dataset, test_dataset, transform


# <multi-datasets>
#----------------------- CIFAR10 ----------------------------
def CIFAR10(binary, print_info=False, class0=0, class1=1, root="./exp_data/CIFAR10", 
            normalize = True, resize_size = (32,32)):

    # transform
    transform_list: List[Callable] = [
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    if normalize:
        normalize_op = transforms.Normalize(
            mean=[0.4914, 0.4822, 0.4465],
            std=[0.2023, 0.1994, 0.2010]
        )
        transform_list.append(normalize_op)
        
    transform = transforms.Compose(transform_list)

    # train_dataset
    train_dataset = torchvision.datasets.CIFAR10(
        root=root,
        train=True,
        download=True,
        transform=transform
    )

    # test_dataset
    test_dataset = torchvision.datasets.CIFAR10(
        root=root,
        train=False,
        download=True,
        transform=transform
    )

    _image_shape = train_dataset[0][0].shape

    if binary:
        train_dataset = DataProcessor.get_binary_dataset(train_dataset, class0, class1)
        test_dataset = DataProcessor.get_binary_dataset(test_dataset, class0, class1)
        

    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform

#----------------------- CIFAR100 ----------------------------
def CIFAR100(binary = False, print_info=False, class0=0, class1=1, 
                root="./exp_data/CIFAR100", normalize = True,
                resize_size = (32,32)):
    
    # transform
    transform_list: List[Callable] = [
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    if normalize:
        normalize_op = transforms.Normalize(
            mean=[0.5071, 0.4867, 0.4408],
            std=[0.2675, 0.2565, 0.2761]
        )
        transform_list.append(normalize_op)

    transform = transforms.Compose(transform_list)

    train_dataset = torchvision.datasets.CIFAR100(
        root=root,
        train=True,
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.CIFAR100(
        root=root,
        train=False,
        download=True,
        transform=transform
    )
    _image_shape = train_dataset[0][0].shape

    if binary:
        train_dataset = DataProcessor.get_binary_dataset(train_dataset, class0, class1)
        test_dataset = DataProcessor.get_binary_dataset(test_dataset, class0, class1)

    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform



def QMNIST(binary, print_info=False, class0=0, class1=1, 
            root="./exp_data/QMNIST", resize_size = (28,28)):
    
    transform_list: List[Callable] = [
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    transform = transforms.Compose(transform_list)

    train_dataset = torchvision.datasets.QMNIST(
        root=root,
        what="train",
        compat=True,         
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.QMNIST(
        root=root,
        what="test",
        compat=True,
        download=True,
        transform=transform
    )
    _image_shape = train_dataset[0][0].shape

    if binary:
        train_dataset = DataProcessor.get_binary_dataset(train_dataset, class0, class1)
        test_dataset = DataProcessor.get_binary_dataset(test_dataset, class0, class1)

    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform

def MNIST(binary, print_info=False, class0=0, class1=1,
            root="./exp_data/MNIST", resize_size = (28,28)):
    
    # transform
    transform_list: List[Callable] = [
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    transform = transforms.Compose(transform_list)
    train_dataset = torchvision.datasets.MNIST(
        root=root,
        train=True,
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.MNIST(
        root=root,
        train=False,
        download=True,
        transform=transform
    )
    _image_shape = train_dataset[0][0].shape

    if binary:
        train_dataset = DataProcessor.get_binary_dataset(train_dataset, class0, class1)
        test_dataset = DataProcessor.get_binary_dataset(test_dataset, class0, class1)


    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform


def Caltech101_Resize_32(binary, print_info=False, class0=0, class1=1, 
                            train_ratio=0.7, split=True, 
                            root="./exp_data/Caltech101",
                            normalize=True,
                            resize_size = (32,32)
                            ):
    # transform
    transform_list: List[Callable] = [
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    if normalize:
        normalize_op = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],  
            std=[0.229, 0.224, 0.225]    
        )
        transform_list.append(normalize_op)
        
    transform = transforms.Compose(transform_list)
    
    full_dataset = torchvision.datasets.Caltech101(
        root=root,
        download=True,
        transform=transform
    )

    _image_shape = full_dataset[0][0].shape

    # --------- binary classification ---------
    if binary:
        full_dataset = DataProcessor.get_binary_dataset(full_dataset, class0, class1)

    # --------- train / test split ---------
    if split:
        total_size = len(full_dataset)
        train_size = int(train_ratio * total_size)
        test_size = total_size - train_size
        train_dataset, test_dataset = random_split(
            full_dataset, [train_size, test_size]
        )
    else:
        train_dataset = full_dataset
        test_dataset = Subset(full_dataset, [])

    # --------- print_info ---------
    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform

def SVHN(binary, class0=0, class1=1, root="./exp_data/SVHN", 
            print_info = False, normalize = True,
            resize_size = (32,32)):

    # transform
    transform_list: List[Callable] = [
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    if normalize:
        normalize_op = transforms.Normalize(
            mean=[0.4914, 0.4822, 0.4465],
            std=[0.2023, 0.1994, 0.2010]
        )
        transform_list.append(normalize_op)
        
    transform = transforms.Compose(transform_list)

    # Load dataset
    train_dataset = torchvision.datasets.SVHN(
        root=root,
        split="train",
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.SVHN(
        root=root,
        split="test",
        download=True,
        transform=transform
    )

    _image_shape = train_dataset[0][0].shape

    # Handle binary classification case
    if binary:
        train_dataset = DataProcessor.get_binary_dataset(train_dataset, class0, class1)
        test_dataset = DataProcessor.get_binary_dataset(test_dataset, class0, class1)

    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform


def GTSRB(binary, class0=0, class1=1, root="./exp_data/GTSRB", 
            print_info = False, normalize = True, resize_size = (32, 32)):
    # transform
    transform_list: List[Callable] = [transforms.Resize(resize_size),  
                                        transforms.ToTensor()]

    if normalize:
        normalize_op = transforms.Normalize(
            mean=[0.3403, 0.3121, 0.3214],
            std=[0.2724, 0.2608, 0.2669]
        )
        transform_list.append(normalize_op)
        
    transform = transforms.Compose(transform_list)

    # Load the dataset
    train_dataset = torchvision.datasets.GTSRB(
        root=root,
        split="train",
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.GTSRB(
        root=root,
        split="test",
        download=True,
        transform=transform
    )

    _image_shape = train_dataset[0][0].shape

    # Handle binary classification case
    if binary:
        train_dataset = DataProcessor.get_binary_dataset(train_dataset, class0, class1)
        test_dataset = DataProcessor.get_binary_dataset(test_dataset, class0, class1)
    
    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform

def Flowers102(binary=False, class0=0, class1=1, 
                root="./exp_data/Flowers102", print_info=False, 
                normalize=True, resize_size=(28, 28)):

    # transform
    transform_list: List[Callable] = [
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    if normalize:  # normalize
        normalize_op = transforms.Normalize(
            mean=[0.3403, 0.3121, 0.3214], 
            std=[0.2724, 0.2608, 0.2669]
        )
        transform_list.append(normalize_op)

    transform = transforms.Compose(transform_list)

    train_dataset = torchvision.datasets.Flowers102(
        root=root, split="train", download=True, transform=transform
    )

    test_dataset = torchvision.datasets.Flowers102(
        root=root, split="test", download=True, transform=transform
    )
    _image_shape = train_dataset[0][0].shape

    if binary:
        train_dataset = DataProcessor.get_binary_dataset(train_dataset, class0, class1)
        test_dataset = DataProcessor.get_binary_dataset(test_dataset, class0, class1)

    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)

    return train_dataset, test_dataset, transform

def OxfordPet(binary=False, class0=0, class1=1,
                root="./exp_data/OxfordPet", print_info = False, 
                normalize = True,
                resize_size = (28, 28)
            ):
    
    # transform
    transform_list: List[Callable] = [
        transforms.Resize(resize_size),
        transforms.ToTensor()
    ]

    if normalize:  # normalize
        normalize_op = transforms.Normalize(
            mean=[0.3403, 0.3121, 0.3214], 
            std=[0.2724, 0.2608, 0.2669]
        )
        transform_list.append(normalize_op)

    transform = transforms.Compose(transform_list)

    # Load the dataset
    train_dataset = torchvision.datasets.OxfordIIITPet(
        root=root,
        split="trainval",
        target_types = "category",
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.OxfordIIITPet(
        root=root,
        split="test",
        download=True,
        target_types = "category",
        transform=transform
    )

    _image_shape = train_dataset[0][0].shape

    if binary:
        assert False, "Not implemented" 
    
    # print_info
    if print_info:
        Print_Info.data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform)
    
    return train_dataset, test_dataset, transform

# <multi-datasets>