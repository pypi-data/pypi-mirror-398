"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin
>>> Last Updated : 2025-12-19
----------------------------------------------------------------------
"""
import math, os
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
from collections import defaultdict
from junshan_kit import kit, ParametersHub

def marker_schedule(marker_schedule=None):

    if marker_schedule == "SPBM":
        based_marker = {
            "ADAM": "s",  # square
            "ALR-SMAG": "h",  # pixel marker
            "Bundle": "o",  # circle
            "SGD": "p",  # pentagon
            "SPSmax": "4",  # tri-right
            "SPBM-PF": "*",  # star
            "SPBM-TR": "s",  # star
            "SPBM-PF-NoneCut": "s",  # circle
            "SPBM-TR-NoneCut": "s",  # circle
        }
        
    else:
        based_marker = {
            "point": ".",  # point marker
            "pixel": ",",  # pixel marker
            "circle": "o",  # circle
            "triangle_down": "v",  # down triangle
            "triangle_up": "^",  # up triangle
            "triangle_left": "<",  # left triangle
            "triangle_right": ">",  # right triangle
            "tri_down": "1",  # tri-down
            "tri_up": "2",  # tri-up
            "tri_left": "3",  # tri-left
            "tri_right": "4",  # tri-right
            "square": "s",  # square
            "pentagon": "p",  # pentagon
            "star": "*",  # star
            "hexagon1": "h",  # hexagon 1
            "hexagon2": "H",  # hexagon 2
            "plus": "+",  # plus
            "x": "x",  # x
            "diamond": "D",  # diamond
            "thin_diamond": "d",  # thin diamond
            "vline": "|",  # vertical line
            "hline": "_",  # horizontal line
        }

    return based_marker


def colors_schedule(colors_schedule=None):

    if colors_schedule == "SPBM":
        based_color = {
            "ADAM":      "#7f7f7f",  
            "ALR-SMAG":  "#796378",  
            "Bundle":    "#17becf",  
            "SGD":       "#2ca02c",  
            "SPSmax":    "#BA6262",  
            "SPBM-PF":   "#1f77b4",  
            "SPBM-TR":   "#d62728",  
            "SPBM-PF-NoneCut": "#8c564b",
            "SPBM-TR-NoneCut": "#e377c2",
        }

    else:
        based_color = {
            "ADAM":     "#1f77b4",
            "ALR-SMAG": "#ff7f0e",
            "Bundle":   "#2ca02c",
            "SGD":      "#d62728",
            "SPSmax":   "#9467bd",
            "SPBM-PF":  "#8c564b",
            "SPBM-TR":  "#e377c2",
            "dddd":     "#7f7f7f",
            "xxx":      "#bcbd22",
            "ED":       "#17becf",
        }
    return based_color


def Search_Paras(Paras, args, model_name, data_name, optimizer_name, metric_key = "training_loss"):

    param_dict = Paras["Results_dict"][model_name][data_name][optimizer_name]
    if Paras["epochs"] is not None:
        xlabel = "epochs"
    else:
        xlabel = "iterations"

    num_polts = len(param_dict)
    cols = 3
    rows = math.ceil(num_polts / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten()

    for idx, (param_str, info) in enumerate(param_dict.items()):
        ax = axes[idx]
        metric_list = info.get(metric_key, [])
        # duration = info.get('duration', 0)
        ax.plot(metric_list)
        # ax.set_title(f"time:{duration:.8f}s - seed: {Paras['seed']}, ID: {Paras['time_str']} \n params = {param_str}", fontsize=10)
        ax.set_title(f'time = {info["train_time"]:.2f}, seed: {Paras["seed"]}, ID: {Paras["time_str"]} \n params = {param_str}', fontsize=10)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ParametersHub.fig_ylabel(metric_key))
        ax.grid(True)
        if Paras.get('use_log_scale', False) and any(k in metric_key for k in ['loss', 'grad']):
            ax.set_yscale("log")


    # Delete the redundant subfigures
    for i in range(len(param_dict), len(axes)):
        fig.delaxes(axes[i])


    plt.suptitle(f'{model_name} on {data_name} - {optimizer_name}, (training, test) = ({Paras["train_data_num"]}/{Paras["train_data_all_num"]}, {Paras["test_data_num"]}/{Paras["test_data_all_num"]}), {Paras["device"]}, batch_size: {Paras["batch_size"]}, V-{Paras["version"]}', fontsize=16)
    # plt.suptitle(
    #     f'{model_name} on {data_name} - {optimizer_name} - (training, test) = ({Paras["train_data_num"]}/{Paras["train_data_all_num"]}, {Paras["test_data_num"]}/{Paras["test_data_all_num"]})\n'
    #     f'{Paras["device"]}, batch_size: {Paras["batch_size"]}',
    #     fontsize=16
    # )
    plt.tight_layout(rect=(0, 0, 1, 0.9))

    filename = f'{Paras["Results_folder"]}/{metric_key}_{ParametersHub.model_abbr(model_name)}_{data_name}_{optimizer_name}.pdf'
    fig.savefig(filename)
    fig.savefig(filename.replace(".pdf", ".png"))
    print(f"✅ Saved: {filename}")
    plt.close('all')


def Read_Results_from_pkl(info_dict, Exp_name, model_name):
    draw_data = defaultdict(dict)
    xlabels = {}
    for data_name, info in info_dict.items():
        for optimizer_name, info_opt in info["optimizer"].items():
            
            if info.get("epochs") is not None:
                pkl_path = f'{Exp_name}/seed_{info["seed"]}/{model_name}/{data_name}/{optimizer_name}/train_{info["train_test"][0]}_test_{info["train_test"][1]}/Batch_size_{info["batch_size"]}/epoch_{info["epochs"]}/{info_opt["ID"]}/Results_{ParametersHub.model_abbr(model_name)}_{data_name}_{optimizer_name}.pkl'
                xlabels[data_name] = "epochs"

            else:
                pkl_path = f'{Exp_name}/seed_{info["seed"]}/{model_name}/{data_name}/{optimizer_name}/train_{info["train_test"][0]}_test_{info["train_test"][1]}/Batch_size_{info["batch_size"]}/iter_{info["iter"]}/{info_opt["ID"]}/Results_{ParametersHub.model_abbr(model_name)}_{data_name}_{optimizer_name}.pkl'
                xlabels[data_name] = "iterations"

            data_ = kit.read_pkl_data(pkl_path)

            param_str = ParametersHub.opt_paras_str(info["optimizer"][optimizer_name])

            draw_data[data_name][optimizer_name] = {
                "metrics": data_[param_str][info["metric_key"]],
                "param_str": param_str
            }

    return draw_data, xlabels



def Mul_Plot(model_name, info_dict, Exp_name = "SPBM", cols = 3, save_path = None, save_name = None, fig_show = False):
    # matplotlib settings
    mpl.rcParams['font.family'] = 'Times New Roman'
    mpl.rcParams["mathtext.fontset"] = "stix"
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["font.size"] = 12
    mpl.rcParams["font.family"] = "serif"
    xlabels = {}
    
    # Read data
    draw_data = defaultdict(dict)
    for data_name, info in info_dict.items():
        for optimizer_name, info_opt in info["optimizer"].items():
            
            if info.get("epochs") is not None:
                pkl_path = f'{Exp_name}/seed_{info["seed"]}/{model_name}/{data_name}/{optimizer_name}/train_{info["train_test"][0]}_test_{info["train_test"][1]}/Batch_size_{info["batch_size"]}/epoch_{info["epochs"]}/{info_opt["ID"]}/Results_{ParametersHub.model_abbr(model_name)}_{data_name}_{optimizer_name}.pkl'
                xlabels[data_name] = "epochs"

            else:
                pkl_path = f'{Exp_name}/seed_{info["seed"]}/{model_name}/{data_name}/{optimizer_name}/train_{info["train_test"][0]}_test_{info["train_test"][1]}/Batch_size_{info["batch_size"]}/iter_{info["iter"]}/{info_opt["ID"]}/Results_{ParametersHub.model_abbr(model_name)}_{data_name}_{optimizer_name}.pkl'
                xlabels[data_name] = "iterations"

            data_ = kit.read_pkl_data(pkl_path)

            param_str = ParametersHub.opt_paras_str(info["optimizer"][optimizer_name])

            draw_data[data_name][optimizer_name] = data_[param_str][info["metric_key"]]
        
    
    # Draw figures
    num_datasets = len(draw_data)
    
    nrows = math.ceil(num_datasets / cols)
    
    fig, axes = plt.subplots(nrows, cols, figsize=(5 * cols, 4 * nrows), squeeze=False)
    axes = axes.flatten()

    for idx, (data_name, info) in enumerate(draw_data.items()):
        ax = axes[idx]
        for optimizer_name, metric_list in info.items():
            ax.plot(metric_list, label=optimizer_name, color = colors_schedule("SPBM")[optimizer_name])

            # marker
            if info_dict[data_name]["marker"] is not None:
                x = np.array(info_dict[data_name]["marker"])

                metric_list_arr = np.array(metric_list)

                ax.scatter(x, metric_list_arr[x], marker=marker_schedule("SPBM")[optimizer_name], color = colors_schedule("SPBM")[optimizer_name])

        ax.set_title(f'{data_name}', fontsize=12)
        ax.set_xlabel(xlabels[data_name], fontsize=12)
        ax.set_ylabel(ParametersHub.fig_ylabel(info_dict[data_name]["metric_key"]), fontsize=12) 
        if any(k in info_dict[data_name]["metric_key"] for k in ['loss', 'grad']):
            ax.set_yscale("log")
        ax.grid(True)

    # Hide redundant axes
    for ax in axes[num_datasets:]:
        ax.axis('off')

    # legend
    all_handles, all_labels = [], []
    for ax in axes[:num_datasets]:
        h, l = ax.get_legend_handles_labels()
        all_handles.extend(h)
        all_labels.extend(l)
    
    # duplicate removal
    unique = dict(zip(all_labels, all_handles))
    handles = list(unique.values())
    labels = list(unique.keys())
    
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=len(handles),
        fontsize=12
    )

    plt.tight_layout()
    if save_path is None:
        save_path_ = f'{model_name}.pdf'
    else:
        os.makedirs(save_path, exist_ok=True)
        save_path_ = f'{save_path}/{save_name}.pdf'
    plt.savefig(save_path_, bbox_inches="tight")
    plt.savefig(save_path_.replace("pdf", "png"), bbox_inches="tight")
    if fig_show:
        plt.show()
    plt.close()  # Colse the fig
    


def Opt_Paras_Plot(model_name, info_dict, Exp_name = "SPBM", save_path = None, save_name = None, fig_show = False):

    mpl.rcParams['font.family'] = 'Times New Roman'
    mpl.rcParams["mathtext.fontset"] = "stix"
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["font.size"] = 12
    mpl.rcParams["font.family"] = "serif"

    # Read data
    draw_data, xlabels = Read_Results_from_pkl(info_dict, Exp_name, model_name)

    if len(draw_data) >1:
        print('*' * 40)
        print("Only one data can be drawn at a time.")
        print(info_dict.keys())
        print('*' * 40)
        assert False

    plt.figure(figsize=(9, 6))  # Optional: set figure size
    
    data_name = None  

    for data_name, _info in draw_data.items():
        for optimizer_name, metric_dict in _info.items():
            plt.plot(metric_dict["metrics"], label=f'{optimizer_name}_{metric_dict["param_str"]}',
                    color=colors_schedule("SPBM")[optimizer_name])

    if data_name is not None:  
        plt.title(f'{data_name}')

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=1) 
    plt.grid(True)

    if any(k in info_dict[data_name]["metric_key"] for k in ['loss', 'grad']):
        plt.yscale("log")

    plt.tight_layout()  # Adjust layout so the legend fits
    plt.xlabel(xlabels[data_name])  # Or whatever your x-axis represents
    plt.ylabel(f'{ParametersHub.fig_ylabel(info_dict[data_name]["metric_key"])}')  
    if save_path is None:
        save_path_ = f'{model_name}.pdf'
    else:
        os.makedirs(save_path, exist_ok=True)
        save_path_ = f'{save_path}/{save_name}.pdf'
    plt.savefig(save_path_, bbox_inches="tight")
    plt.savefig(save_path_.replace("pdf", "png"), bbox_inches="tight")
    if fig_show:
        plt.show()
    
    plt.close()
    


