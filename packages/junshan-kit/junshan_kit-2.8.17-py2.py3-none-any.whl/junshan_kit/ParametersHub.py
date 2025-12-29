import numpy as np
import sys, os, torch, random, glob, json
import argparse
from datetime import datetime
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'src'))
from junshan_kit import ModelsHub, Check_Info


class args: 
    def __init__(self):
        pass
    
    # <args>
    def get_args(self):
        parser = argparse.ArgumentParser(description="Combined config argument example")

# <allowed_models>
        allowed_models = ["LS", "LRBL2", "ResNet18", "ResNet34", "VGG16", "DenseNet201"]
# <allowed_models>

# <allowed_optimizers>
        allowed_optimizers = [
            "ADAM",
            "ALR_SMAG",
            "Bundle",
            "SGD", 
            "SPBM_TR",
            "SPBM_PF",
            "SPSmax",
            "SPBM_PF_NoneCut",
            "SPBM_TR_NoneSpecial",
            "SPBM_TR_NoneCut",
            "SPBM_TR_NoneLower",
            "SPBM_PF_NoneLower",
        ]
# <allowed_optimizers>

# <allowed_datasets>
        allowed_datasets = [
            "MNIST", 
            "QMNIST",
            # "Food101",
            "Flowers102",
            "OxfordPet",
            "GTSRB",
            "CIFAR10",
            "CIFAR100",
            "Caltech101",
            "AIP", 
            "CCFD",
            "Duke",
            "Ijcnn",
            "DHI",
            "EVP",
            "GHP",
            "HL",
            "SVHN",
            "HQC",
            "TN_Weather",
        ]
# <allowed_datasets>  
        data_name_mapping = {
            "Duke": "Duke",
            "MNIST": "MNIST",
            "GTSRB": "GTSRB",
            "OxfordPet": "OxfordPet",
            "QMNIST": "QMNIST",
            "Food101": "Food101",
            "Flowers102": "Flowers102",
            "CIFAR10": "CIFAR10",
            "CIFAR100": "CIFAR100",
            "Caltech101": "Caltech101_Resize_32",
            "AIP": "Adult_Income_Prediction",
            "CCFD": "Credit_Card_Fraud_Detection",
            "Ijcnn": "Ijcnn",
            "SVHN": "SVHN",
            "RCV1": "RCV1",
            "w8a": "w8a",
            "DHI":"Diabetes_Health_Indicators",
            "EVP": "Electric_Vehicle_Population",
            "GHP": "Global_House_Purchase",
            "HL": "Health_Lifestyle",
            "HQC": "Homesite_Quote_Conversion",
            "TN_Weather": "TN_Weather_2020_2025",
        }

        optimizers_mapping = {
            "ADAM": "ADAM",
            "SGD": "SGD",
            "Bundle": "Bundle",
            "ALR_SMAG": "ALR-SMAG",
            "SPBM_TR": "SPBM-TR",
            "SPBM_PF": "SPBM-PF",
            "SPSmax": "SPSmax",
            "SPBM_TR_NoneSpecial": "SPBM-TR-NoneSpecial",
            "SPBM_TR_NoneLower": "SPBM-TR-NoneLower",
            "SPBM_TR_NoneCut": "SPBM-TR-NoneCut",
            "SPBM_PF_NoneSpecial": "SPBM-PF-NoneSpecial",
            "SPBM_PF_NoneLower": "SPBM-PF-NoneLower",
            "SPBM_PF_NoneCut": "SPBM-PF-NoneCut"
        }

        model_mapping = {
            "LS": "LeastSquares",
            "LRBL2": "LogRegressionBinaryL2",
            "ResNet18": "ResNet18",
            "ResNet34": "ResNet34",
            "VGG16": "VGG16",
            "DenseNet201": "DenseNet201"
        }

# <args_from_command>
        parser.add_argument(
            "--train",
            type=str,
            nargs="+",                   # Allow multiple configs
            required=True,
            help = f"Format: model-dataset-optimizer (e.g., ResNet18-CIFAR100-ADAM). model: {allowed_models},\n datasets: {allowed_datasets},\n optimizers: {allowed_optimizers},"
        )

        parser.add_argument(
            "--e",
            type=int,
            help="Number of training epochs. Example: --e 50"
        )

        parser.add_argument(
            "--iter",
            type=int,
            help="Number of iteration. Example: --iter 50"
        )

        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for experiment reproducibility. Default: 42"
        )

        parser.add_argument(
            "--bs",
            type=int,
            required=True,
            help="Batch size for training. Example: --bs 128"
        )

        parser.add_argument(
            "--cuda",
            type=int,
            default=0,
            required=True,
            help="The number of cuda. Example: --cuda 1 (default=0) "
        )

        parser.add_argument(
            "--s",
            type=float, 
            default=1.0, 
            # required=True,
            help="Proportion of dataset to use for training split. Example: --s 0.8 (default=1.0)"
        )

        parser.add_argument(
            "--subset",
            type=float,
            nargs=2,
            # required=True,
            help = "Two subset ratios (train, test), e.g., --subset 0.7 0.3 or --subset 500 500"
        )

        parser.add_argument(
            "--time_str",
            type=str,
            nargs=1,
            # required=True,
            help = "the str of time"
        )

        parser.add_argument(
            "--send_email",
            type=str,
            nargs=3,
            # required=True,
            help = "from_email to_email, from_pwd"
        )

        parser.add_argument(
            "--user_search_grid",
            type=int,
            nargs=1,
            # required=True,
            help = "search_grid: 1: "
        )

        parser.add_argument(
            "--OptParas",
            type=int,
            nargs=1,
            help="Number of optimization steps for parameter tuning (default: 1)"
        )

        parser.add_argument(
            "--works",
            type=int,
            nargs=1,
            default=4,
            help=""
        )

        parser.add_argument(
            "--debug",
            type=int,
            nargs=1,
            default=4,
            help=""
        )
# <args_from_command>

        args = parser.parse_args()
        args.model_name_mapping = model_mapping
        args.data_name_mapping = data_name_mapping
        args.optimizers_name_mapping = optimizers_mapping

# <Check_Info>    
        Check_Info.check_args(args, parser, allowed_models, allowed_optimizers, allowed_datasets)
        return args
# <args>

def UpdateOtherParas(args, OtherParas):
    # <time_str>
    if args.time_str is not None:
        time_str = args.time_str[0]
    else:
        time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # <user_search_grid> 
    if args.user_search_grid is not None:
        OtherParas["user_search_grid"] = args.user_search_grid[0]
    else:
        OtherParas["user_search_grid"] = None

    # <send_email>
    if args.send_email is not None:
        OtherParas["from_email"] = args.send_email[0]
        OtherParas["to_email"] = args.send_email[1]
        OtherParas["from_pwd"] = args.send_email[2]
        OtherParas["send_email"] = True
    else:
        OtherParas["send_email"] = False
    
    # OptParas
    if args.OptParas is not None:
        OtherParas["SeleParasOn"] = False
    else:
        OtherParas["SeleParasOn"] = True
    
    # debug
    if args.debug is not None:
        OtherParas["debug"] = True
    else:
        OtherParas["debug"] = False
    
    OtherParas["time_str"] = time_str
    OtherParas["results_folder_name"] = f'Results_{OtherParas["exp_name"]}'

    return OtherParas

def get_train_group(args):
    training_group = []
    for cfg in args.train:
        model, dataset, optimizer = cfg.split("-")
        training_group.append((args.model_name_mapping[model], args.data_name_mapping[dataset], args.optimizers_name_mapping[optimizer]))

    return training_group


def set_paras(args, OtherParas):
    Paras = {
        # Name of the folder where results will be saved.
        "results_folder_name": OtherParas["results_folder_name"],

        # Print loss every N epochs.
        "epoch_log_interval": 1,

        "use_log_scale": True,
        
        # Timestamp string for result saving.
        "time_str": OtherParas["time_str"],

        # Random seed
        "seed": args.seed,

        # Device used for training.
        "cuda": f"cuda:{args.cuda}",

        # batch-size 
        "batch_size": args.bs,

        # split_train_data
        "split_train_data": args.s,

        # select_subset
        "select_subset": args.subset,

        # Results_dict
        "Results_dict": {},

        # type: bool
        "user_search_grid": OtherParas["user_search_grid"],

        # n_workers
        "num_workers": args.works,

        # debug
        "debug": OtherParas["debug"],

    }
    Paras["iter"] = args.iter
    Paras["epochs"] = args.e
    Paras = model_list(Paras)
    Paras = model_type(Paras)
    Paras = data_list(Paras)
    Paras = optimizer_paras_dict(Paras, OtherParas)
    Paras = device(Paras)
    Paras = find_version(Paras)
    
    return Paras

def set_seed(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def device(Paras) -> dict:
    device = torch.device(f"{Paras['cuda']}" if torch.cuda.is_available() else "cpu")
    Paras["device"] = device
    use_color = sys.stdout.isatty()
    Paras["use_color"] = use_color

    return Paras

def model_list(Paras) -> dict:
    model_list = [
        "ResNet18",
        "ResNet34",
        "VGG16",
        "DenseNet201",
        "LeastSquares",
        "LogRegressionBinary",
        "LogRegressionBinaryL2",
    ]
    Paras["model_list"] = model_list
    return Paras

def model_type(Paras) -> dict:
    model_type = {
        "ResNet18": "multi",
        "ResNet34": "multi",
        "VGG16": "multi",
        "DenseNet201": "multi",
        "LeastSquares": "multi",
        "LogRegressionBinary": "binary",
        "LogRegressionBinaryL2": "binary",
    }

    Paras["model_type"] = model_type
    return Paras

def data_list(Paras) -> dict:
    data_list = [
        "Duke",
        "Ijcnn",
        "w8a",
        "RCV1",
        "Shuttle",
        "Letter",
        "Vowel",
        "MNIST",
        "QMNIST",
        "SVHN",
        "CIFAR10",
        "CIFAR100",
        "GTSRB",
        "OxfordPet",
        "Flowers102",
        "Food101",
        "Caltech101_Resize_32",
        "Adult_Income_Prediction",
        "Credit_Card_Fraud_Detection",
        "Diabetes_Health_Indicators",
        "Electric_Vehicle_Population",
        "Global_House_Purchase",
        "Health_Lifestyle",
        "Homesite_Quote_Conversion",
        "TN_Weather_2020_2025"
    ]
    Paras["data_list"] = data_list
    return Paras

def find_version(Paras):
    try:
        import junshan_kit, importlib.metadata
        Paras["version"] = importlib.metadata.version("junshan_kit")
    except:
        Paras["version"] = "0.0.0"
    return Paras


def optimizer_paras_dict(Paras, OtherParas)->dict:
    optimizer_dict = {
    # ----------------- ADAM --------------------
    "ADAM": {
        "params": {
            # "alpha": [2 * 1e-3],
            "alpha": (
                [0.5 * 1e-3, 1e-3, 2 * 1e-3]
                if OtherParas["SeleParasOn"]
                else [1e-3]
            ),
            "epsilon": [1e-8],
            "beta1": [0.9],
            "beta2": [0.999],
        },
    },
    # ------------- ALR-SMAG --------------------
    "ALR-SMAG": {
        "params": {
            "c": ([0.1, 0.5, 1, 5, 10] if OtherParas["SeleParasOn"] else [0.1]),
            "eta_max": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [0.125]
            ),
            "beta": [0.9],
        },
    },
    # ------------ Bundle -----------------------
    "Bundle": {
        "params": {
            "delta": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [0.01]
            ),
            "cutting_number": [10],
        },
    },
    # ------------------- SGD -------------------
    "SGD": {
        "params": {
            "alpha": (
                [2**i for i in range(-8, 9)] if OtherParas["SeleParasOn"] else [0.001]
            )
        }
    },
    # ------------------- SPSmax ----------------
    "SPSmax": {
        "params": {
            "c": ([0.1, 0.5, 1, 5, 10] if OtherParas["SeleParasOn"] else [0.1]),
            "gamma": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [0.125]),
        },
    },
    # -------------- SPBM-PF --------------------
    "SPBM-PF": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(9, 20)]
                if OtherParas["SeleParasOn"]
                else [1]
            ),
            "cutting_number": [10],
        },
    },
    # -------------- SPBM-TR --------------------
    "SPBM-TR": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(9, 20)]
                if OtherParas["SeleParasOn"]
                else [256]
            ),
            "cutting_number": [10],
        },
    },
    
    # ----------- SPBM-TR-NoneLower -------------
    "SPBM-TR-NoneLower": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(0, 9)]
                if OtherParas["SeleParasOn"]
                else [256]
            ),
            "cutting_number": [10],
        },
    },
    # ----------- SPBM-TR-NoneSpecial -----------
    "SPBM-TR-NoneSpecial": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [1]
            ),
            "cutting_number": [10],
        },
    },
    # ----------- SPBM-TR-NoneCut -----------
    "SPBM-TR-NoneCut": {
        "params": {
            "delta": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [100]
            ),
            "cutting_number": [10],
        },
    },

    # ------------- SPBM-PF-NoneLower -----------
    "SPBM-PF-NoneLower": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(0, 9)]
                if OtherParas["SeleParasOn"]
                else [0]
            ),
            "cutting_number": [10],
        },
    },
    # ----------- SPBM-PF-NoneCut -----------
    "SPBM-PF-NoneCut": {
        "params": {
            "delta": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [100]
            ),
            "cutting_number": [10],
        },
    },
    }

    Paras["optimizer_search_grid"] = optimizer_dict
    return Paras

def metrics()->dict:
    metrics = {
        "epoch_loss": [],
        "training_loss": [],
        "test_loss": [],
        "iter_loss": [],
        "training_acc": [],
        "test_acc": [],
        "grad_norm": [],
        "per_epoch_loss": []
    }
    return metrics


def hyperparas_and_path(Paras, model_name, data_name, optimizer_name, params_gird):

    keys, values = list(params_gird.keys()), list(params_gird.values())

    if Paras["epochs"] is not None:
        Paras["Results_folder"] = f'./{Paras["results_folder_name"]}/seed_{Paras["seed"]}/{model_name}/{data_name}/{optimizer_name}/train_{Paras["train_data_num"]}_test_{Paras["test_data_num"]}/Batch_size_{Paras["batch_size"]}/epoch_{Paras["epochs"]}/{Paras["time_str"]}'
    
    elif Paras["iter"] is not None:
        Paras["Results_folder"] = f'./{Paras["results_folder_name"]}/seed_{Paras["seed"]}/{model_name}/{data_name}/{optimizer_name}/train_{Paras["train_data_num"]}_test_{Paras["test_data_num"]}/Batch_size_{Paras["batch_size"]}/iter_{Paras["iter"]}/{Paras["time_str"]}'
    
    else:
        assert "one of --e or --iter must be specified"

    os.makedirs(Paras["Results_folder"], exist_ok=True)

    return keys, values, Paras


def fig_ylabel(str_name):

    ylabel = {
        "training_loss": "training loss",
        "test_loss": "test loss",
        "training_acc": "training accuracy",
        "test_acc": "test accuracy",
        "grad_norm": "grad norm",
        "per_epoch_loss": "per epoch loss",
        "epoch_loss": "epoch loss",
    }
    return ylabel[str_name]

def model_abbr(model_name):
    name_map = {
        "LogRegressionBinaryL2": "LRBL2",
        "ResNet18": "ResNet18",
        "ResNet34": "ResNet34",
        "VGG16": "VGG16",
        "LstSquares": "LS",
        "DenseNet201": "DenseNet201",
    }
    return name_map[model_name]

def dataset_abbr(model_name):
    name_map = {
        "MNIST": "MNIST",
        "CIFAR100": "CIFAR100",
        "Duke": "Duke",
        "Ijcnn": "Ijcnn",
        "Adult_Income_Prediction": "AIP",
        "Credit_Card_Frau_Detection": "CCFD",
        "Diabetes_Health_Indicators": "DHI",
        "Electric_Vehicle_Population": "EVP",
        "Global_House_Purchase": "GHP",
        "Health_Lifestyle": "HL",
    }
    return name_map[model_name]

def model_full_name(model_name):
    model_mapping = {
        "LS": "LeastSquares",
        "LRBL2": "LogRegressionBinaryL2",
        "ResNet18": "ResNet18",
    }
    return model_mapping[model_name]

def data_resize_size(model_name):
    _dict = {
        "ResNet18": 32,
        "ResNet34": 32,
        "VGG16": 224,
        "DenseNet201": 224,
        "LogRegressionBinaryL2": 32,
    }
    return _dict[model_name]

# <optimizers_full_name>
def optimizers_full_name(optimizer_name):
    name_map = {
        "ADAM": "ADAM",
        "SGD": "SGD",
        "Bundle": "Bundle",
        "ALR_SMAG": "ALR-SMAG",
        "SPBM_TR": "SPBM-TR",
        "SPBM_PF": "SPBM-PF",
        "SPSmax": "SPSmax",
        "SPBM_TR_NoneSpecial": "SPBM-TR-NoneSpecial",
        "SPBM_TR_NoneLower": "SPBM-TR-NoneLower",
        "SPBM_TR_NoneCut": "SPBM-TR-NoneCut",
        "SPBM_PF_NoneSpecial": "SPBM-PF-NoneSpecial",
        "SPBM_PF_NoneLower": "SPBM-PF-NoneLower",
        "SPBM_PF_NoneCut": "SPBM-PF-NoneCut"
    }
    return name_map[optimizer_name]
# <optimizers_full_name>

# <dataset_full_name>
def dataset_full_name(dataset_name):
    name_map = {
        "MNIST": "MNIST",
        "CIFAR100": "CIFAR100",
        "Caltech101": "Caltech101_Resize_32",
        "Duke": "Duke",
        "AIP": "Adult_Income_Prediction",
        "CCFD": "Credit_Card_Fraud_Detection",
        "Ijcnn": "Ijcnn",
        "DHI":"Diabetes_Health_Indicators",
        "EVP": "Electric_Vehicle_Population",
        "GHP": "Global_House_Purchase",
        "HL": "Health_Lifestyle",
        "HQC": "Homesite_Quote_Conversion",
        "TN_Weather": "TN_Weather_2020_2025",
        }
    return name_map[dataset_name]
# <dataset_full_name>

def opt_paras_str(opt_paras_dict):
    # Example: "k1_v1_k2_v2_..."

    keys = list(opt_paras_dict.keys())
    values = list(opt_paras_dict.values())

    param_str = "_".join(f"{k}_{v}" for k, v in zip(keys, values) if k != "ID")

    return param_str
# <set_marker_point>
def set_marker_point(epoch_num: int) -> list:
    marker_point = {
        1: [0],
        3: [0, 2],
        4: [0, 2, 4],
        6: [0, 2, 4, 6],
        8: [0, 2, 4, 6, 8],
        10: [0, 2, 4, 6, 8, 10],
        50: [0, 10, 20, 30, 40, 50],
        100: [0, 20, 40, 60, 80, 100],
        200: [0, 40, 80, 120, 160, 200],
    }
    if epoch_num not in marker_point:
        raise ValueError(f"No marker defined for epoch {epoch_num}")
    
    return marker_point[epoch_num]

# <set_marker_point>
# <results_path_to_info>
def results_path_to_info(path_list):
    info_dict = {}

    for path in path_list:
        parts = path.split("/")
        seed = parts[1]
        model_name = parts[2]
        data_name = parts[3]
        optimizer = parts[4]
        train_test = parts[5].split("_")
        batch_size = parts[6].split("_")[2]
        epochs = parts[7].split("_")[1]
        ID = parts[8]

        if model_name not in info_dict:
            info_dict[model_name] = {}
        
        if data_name not in info_dict[model_name]:
            info_dict[model_name][data_name] = {}
        
        if optimizer not in info_dict[model_name][data_name]:
            info_dict[model_name][data_name][optimizer] = {}

        info_dict[model_name][data_name][optimizer][ID] = {
            "seed": seed.split("_")[1],
            "epochs": int(epochs),
            "train_test": (train_test[1], train_test[3]),
            "batch_size": batch_size,
            "marker": set_marker_point(int(epochs)),
            "optimizer":{
                f"{optimizer}":{
                    "ID": ID,
                    }
                }
        }

    return info_dict
# <results_path_to_info>

# <update_info_dict>
def update_info_dict(draw_data_list, draw_data, results_dict, model_name, info_dict, metric_key_dict):
    for data_name in draw_data_list:
        for i in draw_data[data_name]:
            optimizer_name, ID, Opt_Paras = i

            if data_name not in results_dict[model_name].keys():
                print('*' * 40)
                print(f'{data_name} not in results')
                print('*' * 40)
                assert False

            # Check if optimizer_name exists in results_dict
            if optimizer_name not in results_dict[model_name][data_name]:
                print('*' * 40)
                print(f'({data_name}, {optimizer_name}, {ID}) not in results_dict and \n {optimizer_name} is error.')
                print('*' * 40)
                assert False

            # Check if ID exists in results_dict
            if ID not in results_dict[model_name][data_name][optimizer_name]:
                print('*' * 60)
                print(f'({data_name}, {optimizer_name}, {ID}) not in results_dict and \n {ID} is error.')
                print('*' * 60)
                assert False

            # Initialize info_dict[data_name] if it does not exist
            if data_name not in info_dict:
                info_dict[data_name] = results_dict[model_name][data_name][optimizer_name][ID].copy()

            # Update optimizer parameters
            if "optimizer" not in info_dict[data_name]:
                info_dict[data_name]["optimizer"] = {}
            info_dict[data_name]["optimizer"][optimizer_name] = Opt_Paras
            info_dict[data_name]["optimizer"][optimizer_name]["ID"] = ID

            # Update metric_key
            info_dict[data_name]["metric_key"] = metric_key_dict[data_name]
    
    return info_dict
# <update_info_dict>

def get_results_all_pkl_path(results_folder):

    pattern = os.path.join(results_folder, "**", "*.pkl")

    return glob.glob(pattern, recursive=True)


def set_path_and_save_config_for_fig(info_dict, py_name, model_name, User_set_ID=None):
    metric_key_mapping = {
        "training_loss": "loss",
        "training_acc": "acc",
    }

    seed = 'seed'
    bs = 'bs'
    train_test = 'train_test'
    metric_key = 'metric_key'
    epochs = 'epochs'

    for keys, vlaures in info_dict.items():
        One_data_dict = {}
        One_data_dict[keys] = vlaures
        seed += '_' + str(info_dict[keys]["seed"])  
        epochs += '_' + str(info_dict[keys]["epochs"])
        bs += '_' + str(info_dict[keys]["batch_size"]) 
        train_test += '_' + str(info_dict[keys]["train_test"]).replace(', ', '-') 
        metric_key += '_' + metric_key_mapping[info_dict[keys]["metric_key"]]

    if User_set_ID is None:
        path = f'{py_name}/{model_name}/{seed}/{bs}/{epochs}/{train_test}/{metric_key}'
    else:
        path = f'{py_name}/{model_name}/{seed}/{bs}/{epochs}/{train_test}/{User_set_ID}/{metric_key}'

    if path:  
        os.makedirs(path, exist_ok=True)

    with open(f'{path}/config_pretty.json', 'w', encoding='utf-8') as f:
        json.dump(info_dict, f, indent=4, ensure_ascii=False)

    return path
