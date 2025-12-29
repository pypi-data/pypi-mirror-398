import torch, time, pickle
import torch.nn as nn
import numpy as np
import torch.utils.data as Data
from torch.nn.utils import parameters_to_vector
from junshan_kit import DataHub, TrainingHub, Evaluate_Metrics, DataProcessor, Print_Info, ParametersHub

from junshan_kit.OptimizerHup import OptimizerFactory, SPBM

def chosen_loss_fn(model_name, Paras):
    # ---------------------------------------
    # There have an addition parameter
    if model_name == "LogRegressionBinaryL2":
        Paras["lambda"] = 1e-3
    # ---------------------------------------

    if model_name in ["LeastSquares"]:
        loss_fn = nn.MSELoss()

    else:
        if Paras["model_type"][model_name] == "binary":
            loss_fn = nn.BCEWithLogitsLoss()

        elif Paras["model_type"][model_name] == "multi":
            loss_fn = nn.CrossEntropyLoss()

        else:
            loss_fn = nn.MSELoss()
            assert False, "\033[91m The loss function is error!\033[0m"
            
    Paras["loss_fn"] = loss_fn
    return loss_fn, Paras


def load_data(model_name, data_name, Paras):
    # load data
    train_path = f"./exp_data/{data_name}/{data_name}_training"
    test_path = f"./exp_data/{data_name}/{data_name}_test"

    if Paras["model_type"][model_name] == "binary":
        Paras["binary"] = True
    else:
        Paras["binary"] = False
    
    # ---------------------------------------------------------
    if data_name == "MNIST":
        train_dataset, test_dataset, transform = DataHub.MNIST(
            binary=Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)
        )

    elif data_name == "QMNIST":
        train_dataset, test_dataset, transform = DataHub.QMNIST(
            binary=Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)
        )

    elif data_name == "CIFAR10":
        train_dataset, test_dataset, transform = DataHub.CIFAR10(
            binary=Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)
        )
    
    elif data_name == "CIFAR100":
        train_dataset, test_dataset, transform = DataHub.CIFAR100(
            binary=Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)    
        )

    elif data_name == "SVHN":
        train_dataset, test_dataset, transform = DataHub.SVHN(
            binary=Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)    
        )

    elif data_name == "Flowers102":
        train_dataset, test_dataset, transform = DataHub.Flowers102(
            binary=Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)
        )
    
    elif data_name == "OxfordPet":
        train_dataset, test_dataset, transform = DataHub.OxfordPet(
            binary=Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)
        )

    elif data_name == "GTSRB":
        train_dataset, test_dataset, transform = DataHub.GTSRB(
            binary = Paras["binary"],
            resize_size = ParametersHub.data_resize_size(model_name)
        )

    elif data_name == "Adult_Income_Prediction":
        train_dataset, test_dataset, transform = DataHub.Adult_Income_Prediction(Paras)

    elif data_name == "Credit_Card_Fraud_Detection":
        train_dataset, test_dataset, transform = DataHub.Credit_Card_Fraud_Detection(Paras)
    
    elif data_name == "Diabetes_Health_Indicators":
        train_dataset, test_dataset, transform = DataHub.Diabetes_Health_Indicators(Paras)

    elif data_name == "Electric_Vehicle_Population":
        train_dataset, test_dataset, transform = DataHub.Electric_Vehicle_Population(Paras)

    elif data_name == "Global_House_Purchase":
        train_dataset, test_dataset, transform = DataHub.Global_House_Purchase(Paras)

    elif data_name == "Health_Lifestyle":
        train_dataset, test_dataset, transform = DataHub.Health_Lifestyle(Paras)

    elif data_name == "Homesite_Quote_Conversion":
        train_dataset, test_dataset, transform = DataHub.Homesite_Quote_Conversion(Paras)
    
    elif data_name == "TN_Weather_2020_2025":
        train_dataset, test_dataset, transform = DataHub.TN_Weather_2020_2025(Paras)

    elif data_name == "Caltech101_Resize_32": 
        train_dataset, test_dataset, transform = DataHub.Caltech101_Resize_32(Paras["model_type"][model_name])

    # elif data_name in ["Vowel", "Letter", "Shuttle", "w8a"]:
    #     Paras["train_ratio"] = Paras["split_train_data"][data_name]
    #     train_dataset, test_dataset, transform = datahub.get_libsvm_data(
    #         train_path + ".txt", test_path + ".txt", data_name
    #     )

    elif data_name in ["RCV1", "Duke", "Ijcnn"]:
        train_dataset, test_dataset, transform = DataProcessor.get_libsvm_bz2_data(
            train_path + ".bz2", test_path + ".bz2", data_name, Paras
        )

    else:
        transform = None
        raise ValueError(f"The {data_name} is invalid!")

    # Computing the number of data
    Paras["train_data_num"], Paras["test_data_num"] = len(train_dataset), len(test_dataset)
    Paras["train_data_all_num"], Paras["test_data_all_num"] = len(train_dataset), len(test_dataset)
    Paras["transform"] = transform

    return train_dataset, test_dataset, Paras

def get_dataloader(data_name, train_dataset, test_dataset, Paras):
    ParametersHub.set_seed(Paras["seed"])
    g = torch.Generator()
    g.manual_seed(Paras["seed"])
    
    train_loader = Data.DataLoader(
            dataset=train_dataset,
            shuffle=True,
            batch_size=Paras["batch_size"],
            generator=g,
            num_workers=Paras["num_workers"],
        )
    
    test_loader = Data.DataLoader(
            dataset=test_dataset,
            shuffle=False,
            batch_size=Paras["batch_size"],
            generator=g,
            num_workers=Paras["num_workers"],
        )
    
    return train_loader, test_loader

def chosen_optimizer(optimizer_name, model, hyperparams, Paras):
    if optimizer_name == "SGD":
        optimizer = torch.optim.SGD(model.parameters(), lr=hyperparams["alpha"])

    elif optimizer_name == "ADAM":
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=hyperparams["alpha"],
            betas=(hyperparams["beta1"], hyperparams["beta2"]),
            eps=hyperparams["epsilon"],
        )
    
    elif optimizer_name in ["Bundle"]:
        optimizer = OptimizerFactory.Bundle(
            model.parameters(), model, hyperparams, Paras
        )
    
    elif optimizer_name in ["ALR-SMAG"]:
        optimizer = OptimizerFactory.ALR_SMAG(
            model.parameters(), model, hyperparams, Paras
        )
    
    elif optimizer_name in ["SPBM-TR"]:
        optimizer = SPBM.TR(model.parameters(), model, hyperparams, Paras)

    elif optimizer_name in ["SPBM-TR-NoneLower"]:
        optimizer = SPBM.TR_NoneLower(model.parameters(), model, hyperparams, Paras)
    
    elif optimizer_name in ["SPBM-TR-NoneSpecial"]:
        optimizer = SPBM.TR_NoneSpecial(model.parameters(), model, hyperparams, Paras)
    
    elif optimizer_name in ["SPBM-TR-NoneCut"]:
        optimizer = SPBM.TR_NoneCut(model.parameters(), model, hyperparams, Paras)

    elif optimizer_name in ["SPBM-PF-NoneLower"]:
        optimizer = SPBM.PF_NoneLower(model.parameters(), model, hyperparams, Paras)

    elif optimizer_name in ["SPBM-PF"]:
        optimizer = SPBM.PF(model.parameters(), model, hyperparams, Paras)
    
    elif optimizer_name in ["SPBM-PF-NoneCut"]:
        optimizer = SPBM.PF_NoneCut(model.parameters(), model, hyperparams, Paras)

    elif optimizer_name in ["SPSmax"]:
        optimizer = OptimizerFactory.SPSmax(
            model.parameters(), model, hyperparams, Paras
        )

    else:
        raise NotImplementedError(f"{optimizer_name} is not supported.")

    return optimizer

def load_model_dataloader(base_model_fun, initial_state_dict, data_name, train_dataset, test_dataset, Paras):
    ParametersHub.set_seed(Paras["seed"])
    model = base_model_fun()
    model.load_state_dict(initial_state_dict)
    model.to(Paras["device"])
    train_loader, test_loader = TrainingHub.get_dataloader(data_name, train_dataset, test_dataset, Paras)

    return model, train_loader, test_loader
# <training>
def train(train_loader, optimizer_name, optimizer, model, loss_fn, Paras):
    train_time = time.time()
    metrics = ParametersHub.metrics()
    for epoch in range(Paras["epochs"]):
        epoch_time = time.time()
        for index, (X, Y) in enumerate(train_loader):
            X, Y = X.to(Paras["device"]), Y.to(Paras["device"])

            if epoch == 0 and index == 0:
                # # compute gradient norm
                # with torch.no_grad():
                #     g_k = parameters_to_vector(
                #         [
                #             p.grad if p.grad is not None else torch.zeros_like(p)
                #             for p in model.parameters()
                #         ]
                #     )
                #     metrics["grad_norm"].append(torch.norm(g_k, p=2).detach().cpu().item())
                #     print(metrics["grad_norm"][-1])
                
                # initial training loss
                initial_time = time.time()
                initial_loss, initial_correct = Evaluate_Metrics.get_loss_acc(train_loader, model, loss_fn, Paras)
                metrics["training_loss"].append(initial_loss)
                metrics["training_acc"].append(initial_correct)

                Print_Info.per_epoch_info(Paras, -1, metrics, time.time() - initial_time)

            # Update the model
            if optimizer_name in ["SGD", "ADAM"]:
                optimizer.zero_grad()
                loss = Evaluate_Metrics.loss(X, Y, model, loss_fn, Paras)
                loss.backward()
                optimizer.step()

            elif optimizer_name in [
                "Bundle",
                "SPBM-TR",
                "SPBM-PF",
                "ALR-SMAG",
                "SPSmax",
                "SPBM-TR-NoneSpecial",
                "SPBM-TR-NoneLower",
                "SPBM-TR-NoneCut",
                "SPBM-PF-NoneCut",
            ]:
                def closure():
                    optimizer.zero_grad()
                    loss = Evaluate_Metrics.loss(X, Y, model, loss_fn, Paras)
                    loss.backward()
                    return loss

                loss = optimizer.step(closure)

            else:
                loss = 0
                raise NotImplementedError(f"{optimizer_name} is not supported.")

        # Evaluation
        training_loss, training_acc = Evaluate_Metrics.get_loss_acc(train_loader, model, loss_fn, Paras)

        
        metrics["training_loss"].append(training_loss)
        metrics["training_acc"].append(training_acc)

        Print_Info.per_epoch_info(Paras, epoch, metrics, time.time() - epoch_time)
    
    time_cost = time.time() - train_time
    metrics["train_time"] = time_cost 

    return metrics
# <training>

# <training_iteration>
def train_iteration(train_loader, optimizer_name, optimizer, model, loss_fn, Paras):
    train_time = time.time()
    metrics = ParametersHub.metrics()
    for iter in range(Paras["iter"]):
        iter_time = time.time()
        for index, (X, Y) in enumerate(train_loader):
            X, Y = X.to(Paras["device"]), Y.to(Paras["device"])

            if iter == 0 and index == 0:
                initial_time = time.time()
                initial_loss, initial_correct = Evaluate_Metrics.get_loss_acc(train_loader, model, loss_fn, Paras)
                metrics["training_loss"].append(initial_loss)
                metrics["training_acc"].append(initial_correct)

                Print_Info.per_epoch_info(Paras, -1, metrics, time.time() - initial_time)

            # Update the model
            if optimizer_name in ["SGD", "ADAM"]:
                optimizer.zero_grad()
                loss = Evaluate_Metrics.loss(X, Y, model, loss_fn, Paras)
                loss.backward()
                optimizer.step()

            elif optimizer_name in [
                "Bundle",
                "SPBM-TR",
                "SPBM-PF",
                "ALR-SMAG",
                "SPSmax",
                "SPBM-TR-NoneSpecial",
                "SPBM-TR-NoneLower",
                "SPBM-TR-NoneCut",
                "SPBM-PF-NoneCut",
            ]:
                def closure():
                    optimizer.zero_grad()
                    loss = Evaluate_Metrics.loss(X, Y, model, loss_fn, Paras)
                    loss.backward()
                    return loss

                loss = optimizer.step(closure)

            else:
                loss = 0
                raise NotImplementedError(f"{optimizer_name} is not supported.")

        # Evaluation
        training_loss, training_acc = Evaluate_Metrics.get_loss_acc(train_loader, model, loss_fn, Paras)

        metrics["training_loss"].append(training_loss)
        metrics["training_acc"].append(training_acc)

        Print_Info.per_epoch_info(Paras, iter, metrics, time.time() - iter_time)
    
    time_cost = time.time() - train_time
    metrics["train_time"] = time_cost 

    return metrics
# <training_iteration>

def Record_Results(hyperparams,data_name, model_name, optimizer_name, metrics, Paras):

    keys = list(hyperparams.keys())
    values = list(hyperparams.values())

    param_str = "_".join(f"{k}_{v}" for k, v in zip(keys, values))

    if model_name not in Paras["Results_dict"]:
        Paras["Results_dict"][model_name] = {}

    if data_name not in Paras["Results_dict"][model_name]:
        Paras["Results_dict"][model_name][data_name] = {}

    
    if optimizer_name not in Paras["Results_dict"][model_name][data_name]:
        Paras["Results_dict"][model_name][data_name][optimizer_name] = {}

    
    Paras["Results_dict"][model_name][data_name][optimizer_name][param_str] = {
        "training_acc": metrics["training_acc"],
        "training_loss": metrics["training_loss"],
        "train_time": metrics["train_time"]
    }

    return Paras  


def Save_Results(Paras, model_name, data_name, optimizer_name):
    """
    Save the result dictionary for a specific (model, dataset, optimizer) combination.

    Parameters
    ----------
    Paras : dict or Namespace
        A container holding all experiment-related information, where:
            - Paras["Results_folder"] : str
                Directory to save result files.
            - Paras["Results_dict"] : dict
                Nested dictionary storing experiment results.

    model_name : str
        Full name of the model (e.g., "LeastSquares").

    data_name : str
        Name of the dataset used in the experiment.

    optimizer_name : str
        Name of the optimizer for which the results are saved.

    Notes
    -----
    The function generates a filename in the format:
        Results_{model_abbr}_{dataset_abbr}_{optimizer}.pkl
    and dumps the corresponding result dictionary to disk.
    """

    # Construct the output file path using model/dataset abbreviations
    filename = (
        f'{Paras["Results_folder"]}/'
        f'Results_{ParametersHub.model_abbr(model_name)}_'
        f'{data_name}_'
        f'{optimizer_name}.pkl'
    )

    # Save the nested results dict to disk
    with open(filename, "wb") as f:
        pickle.dump(Paras["Results_dict"][model_name][data_name][optimizer_name], f)

