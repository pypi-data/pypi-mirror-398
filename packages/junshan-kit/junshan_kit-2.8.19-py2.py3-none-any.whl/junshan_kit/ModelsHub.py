import torchvision,torch, random
import numpy as np
from torchvision.models import resnet18,resnet34, ResNet18_Weights, ResNet34_Weights, vgg16, densenet201
import torch.nn as nn
import torchvision.models

# <ResNet18>
#**************************************************************
# ------------------------- ResNet18 --------------------------
#**************************************************************
# ---------------- Build ResNet18 - Caltech101 -----------------------
def Build_ResNet18_Caltech101_Resize_32():
    model = resnet18(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False) # 1
    model.fc = nn.Linear(model.fc.in_features, 101) # 2

    return model
# ---------------- Build ResNet18 - CIFAR100 -----------------------
def Build_ResNet18_CIFAR10():
    model = resnet18(weights=None)
    # model = resnet18(weights=ResNet18_Weights.DEFAULT)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 10)  # 2

    return model

# ---------------- Build ResNet18 - CIFAR100 -----------------------
def Build_ResNet18_CIFAR100():
    model = resnet18(weights=None)
    # model = resnet18(weights=ResNet18_Weights.DEFAULT)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 100)  # 2

    return model

# ---------------- Build ResNet18 - MNIST ----------------------------
def Build_ResNet18_MNIST():
    model = resnet18(weights=None)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 10)  # 2

    return model
# ---------------- Build ResNet18 - QMNIST ----------------------------
def Build_ResNet18_QMNIST():
    model = resnet18(weights=None)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 10)  # 2

    return model

# ---------------- Build ResNet18 - MNIST ----------------------------
def Build_ResNet18_SVHN():
    model = resnet18(weights=None)
    # model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)  # 1
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 10)  # 2

    return model

def Build_ResNet18_GTSRB():
    model = resnet18(weights=None)
    #. 28 x 28
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 43)

    return model

def Build_ResNet18_Flowers102():
    model = resnet18(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 102)

    return model

def Build_ResNet18_OxfordPet():
    model = resnet18(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 37)

    return model


# <ResNet34>
#**************************************************************
# ------------------------- ResNet34 --------------------------
#**************************************************************
# ---------------- Build ResNet18 - CIFAR10 ----------------------------
def Build_ResNet34_CIFAR10():
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False) 
    model.fc = nn.Linear(model.fc.in_features, 10)  

    return model
# ---------------- Build ResNet18 - CIFAR100 ----------------------------
def Build_ResNet34_CIFAR100():
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False) 
    model.fc = nn.Linear(model.fc.in_features, 100)  

    return model

# ---------------- Build ResNet18 - MNIST ----------------------------
def Build_ResNet34_MNIST():
    model = resnet34(weights=None)  
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=1, bias=False)  
    model.fc = nn.Linear(model.fc.in_features, 10)  

    return model

# ---------------- Build ResNet34 - Caltech101 -----------------------
def Build_ResNet34_Caltech101_Resize_32():
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 101)

    return model

# ---------------- Build ResNet34 - GTSRB ---- -----------------------
def Build_ResNet34_GTSRB():
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 43)

    return model

# ---------------- Build ResNet34 - Flowers102 -----------------------
def Build_ResNet34_Flowers102():
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 102)

    return model

def Build_ResNet34_SVHN():
    model = resnet34(weights=None)
    # model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)  # 1
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 10)  # 2

    return model

def Build_ResNet34_OxfordPet():
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 37)

    return model

# <ResNet34>

# <VGG16>
#**************************************************************
# ------------------------- VGG16 -----------------------------
#**************************************************************

# ---------------- Build VGG16 - CIFAR10 ----------------------
def Build_VGG16_CIFAR10():
    model = vgg16()
    model.classifier[6] = nn.Linear(4096, 10)

    return model

# ---------------- Build VGG16 - CIFAR100 ----------------------
def Build_VGG16_CIFAR100():
    model = vgg16()
    model.classifier[6] = nn.Linear(4096, 100)

    return model


# VGG16: Don't crop the input image too smal
def Build_VGG16_GTSRB():
    model = vgg16()
    model.classifier[6] = nn.Linear(4096, 43)

    return model

# ---------------- Build VGG16 - Caltech101 ------------------
def Build_VGG16_Caltech101_Resize_32():
    model = vgg16()
    model.classifier[6] = nn.Linear(4096, 101)

    return model

# ---------------- Build VGG16 - Flowers102 ------------------
def Build_VGG16_Flowers102():
    model = vgg16()
    model.classifier[6] = nn.Linear(4096, 102)

    return model

# ---------------- Build VGG16 - SVHN ------------------------
def Build_VGG16_SVHN():
    model = vgg16()
    model.classifier[6] = nn.Linear(4096, 10)

    return model

# ---------------- Build VGG16 - OxfordPet --------------------
def Build_VGG16_OxfordPet():
    model = vgg16()
    model.classifier[6] = nn.Linear(4096, 37)

    return model




# <DenseNet201>
#**************************************************************
# ------------------------- DenseNet201 -----------------------

# ------------- Build DenseNet201 - CIFAR10 -------------------
def Build_DenseNet201_CIFAR10():
    model = densenet201()
    model.classifier = nn.Linear(1920, 10)

    return model

# ------------- Build DenseNet201 - CIFAR100 ------------------
def Build_DenseNet201_CIFAR100():
    model = densenet201()
    model.classifier = nn.Linear(1920, 100)

    return model

# ------------- Build DenseNet201 - CALTH101 ------------------
def Build_DenseNet201_Caltech101_Resize_32():
    model = densenet201()
    model.classifier = nn.Linear(1920, 101)

    return model


#**************************************************************
def Build_DenseNet201_GTSRB():
    model = densenet201()
    model.classifier = nn.Linear(1920, 43)

    return model

# ------------- Build DenseNet201 - Flowers102 ----------------
def Build_DenseNet201_Flowers102():
    model = densenet201()
    model.classifier = nn.Linear(1920, 102)

    return model


# ------------- Build DenseNet201 - SVHN ----------------------
def Build_DenseNet201_SVHN():
    model = densenet201()
    model.classifier = nn.Linear(1920, 10)

    return model




# <LogRegressionBinaryL2>
#**************************************************************
# ------------- LogRegressionBinaryL2 -------------------------
#**************************************************************

def Build_LogRegressionBinaryL2_RCV1():
    return nn.Sequential(                    
        nn.Linear(47236, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_MNIST():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(28 * 28, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_QMNIST():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(28 * 28, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_SVHN():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3 * 32 * 32, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_Caltech101_Resize_32():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3 * 32 * 32, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_CIFAR10():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3* 32 * 32, 1))
# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_CIFAR100():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3* 32 * 32, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_GTSRB():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3 * 28 * 28, 1))

def Build_LogRegressionBinaryL2_Food101():
    return nn.Sequential(                   
        nn.Linear(121, 1))

def Build_LogRegressionBinaryL2_Flowers102():
    return nn.Sequential(                   
        nn.Linear(3 * 28 * 28, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_Duke():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(7129, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_Ijcnn():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(22, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_w8a():
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(300, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_Adult_Income_Prediction():
    return nn.Sequential(                   
        nn.Linear(108, 1))


def Build_LogRegressionBinaryL2_Credit_Card_Fraud_Detection():
    return nn.Sequential(                   
        nn.Linear(30, 1))


def Build_LogRegressionBinaryL2_Diabetes_Health_Indicators():
    return nn.Sequential(                   
        nn.Linear(52, 1))


def Build_LogRegressionBinaryL2_Electric_Vehicle_Population():
    return nn.Sequential(                   
        nn.Linear(835, 1))

def Build_LogRegressionBinaryL2_Global_House_Purchase():
    return nn.Sequential(                   
        nn.Linear(81, 1))

def Build_LogRegressionBinaryL2_Health_Lifestyle():
    return nn.Sequential(                   
        nn.Linear(15, 1))

def Build_LogRegressionBinaryL2_Homesite_Quote_Conversion():
    return nn.Sequential(                   
        nn.Linear(655, 1))

def Build_LogRegressionBinaryL2_TN_Weather_2020_2025():
    return nn.Sequential(                   
        nn.Linear(121, 1))



# <LogRegressionBinaryL2>

















#**************************************************************
# ---------------------- LeastSquares -------------------------
#**************************************************************
# ---------------- LeastSquares - MNIST -----------------------
def Build_LeastSquares_MNIST():
    """
    1. flatten MNIST images (1x28x28 → 784)
    2. Use a linear layer for multi-classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(28 * 28, 10))

# ---------------- LeastSquares - CIFAR100 --------------------
def Build_LeastSquares_CIFAR100():
    """
    1. flatten MNIST images (3 * 32 * 32 → 784)
    2. Use a linear layer for multi-classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3 * 32 * 32, 100))

# ---------------- LeastSquares - Caltech101 ------------------
def Build_LeastSquares_Caltech101_Resize_32():
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(3*32*32, 101)
    )


#*************************************************************
# --------------- LogRegressionBinary ------------------------
#*************************************************************
# -------------- LogRegressionBinary - MNIST ------------------
def Build_LogRegressionBinary_MNIST():
    """
    1. flatten MNIST images (1x28x28 → 784)
    2. Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(28 * 28, 1))


# --------------- LogRegressionBinary - CIFAR100 --------------
def Build_LogRegressionBinary_CIFAR100():
    """
    1. flatten CIFAR100 images 
    2. Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3* 32 * 32, 1))

# -------------- LogRegressionBinary - RCV1 ------------------
def Build_LogRegressionBinary_RCV1():
    """
    1. Use a linear layer for binary classification
    """
    return nn.Sequential(                    
        nn.Linear(47236, 1))

