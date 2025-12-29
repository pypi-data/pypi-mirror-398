from junshan_kit import DataSets, ParametersHub


# -------------------------------------------------------------
def training_group(training_group):
    print(f"--------------------- training_group ------------------")
    for g in training_group:
        print(g)
    print(f"-------------------------------------------------------")


def training_info(data_name, optimizer_name, hyperparams, Paras, model_name):
    if Paras['use_color']:
        print('\033[90m' + '-' * 115 + '\033[0m')
        print(
            f'\033[32m✅ \033[34mDataset:\033[32m {data_name}, \t'
            f'\033[34mBatch-size:\033[32m {Paras["batch_size"]}, \t'
            f'\033[34m(training, test) = \033[32m '
            f'({Paras["train_data_num"]}/{Paras["train_data_all_num"]}, '
            f'{Paras["test_data_num"]}/{Paras["test_data_all_num"]}), \t'
            f'\033[34mdevice:\033[32m {Paras["device"]}'
        )
        print(
            f'\033[32m✅ \033[34mOptimizer:\033[32m {optimizer_name}, \t'
            f'\033[34mParams:\033[32m {hyperparams}'
        )
        print(
            f'\033[32m✅ \033[34mmodel:\033[32m {model_name}, \t'
            f'\033[34mmodel type:\033[32m {Paras["model_type"][model_name]}, \t'
            f'\033[34mloss_fn:\033[32m {Paras["loss_fn"]}'
        )
        print(
            f'\033[32m✅ \033[34mtransform:\033[32m {Paras["transform"]}'
        )
        print(
            f'\033[32m✅ \033[34mResults_folder:\033[32m {Paras["Results_folder"]}'
        )
        print('\033[90m' + '-' * 115 + '\033[0m')

    else:
        print('-' * 115)
        print(
            f'✅ Dataset: {data_name}, \t'
            f'Batch-size: {Paras["batch_size"]}, \t'
            f'(training, test) = '
            f'({Paras["train_data_num"]}/{Paras["train_data_all_num"]}, '
            f'{Paras["test_data_num"]}/{Paras["test_data_all_num"]}), \t'
            f'device: {Paras["device"]}'
        )
        print(f'✅ Optimizer: {optimizer_name}, \tParams: {hyperparams}')
        print(
            f'✅ model: {model_name}, \t'
            f'model type: {Paras["model_type"][model_name]}, \t'
            f'loss_fn: {Paras["loss_fn"]}'
        )
        print(f'✅ transform: {Paras["transform"]}')
        print(f'✅ Results_folder: {Paras["Results_folder"]}')
        print('-' * 115)
# <Step_7_2>

def per_epoch_info(Paras, epoch, metrics, epoch_time):
    if Paras.get('epochs') is not None:
        progress = f'{epoch + 1}/{Paras["epochs"]}'
        progress_label = 'epochs'
    else:
        progress = f'{epoch + 1}/{Paras["iter"]}'
        progress_label = 'iters'

    if Paras['use_color']:
        print(
            f'\033[34m {progress_label} = \033[32m{progress}\033[0m,\t'
            f'\033[34m training_loss = \033[32m{metrics["training_loss"][epoch + 1]:.4e}\033[0m,\t'
            f'\033[34m training_acc = \033[32m{100 * metrics["training_acc"][epoch + 1]:.2f}%\033[0m,\t'
            f'\033[34m time = \033[32m{epoch_time:.2f}s\033[0m'
        )
    else:
        print(
            f'{progress_label} = {progress},\t'
            f'training_loss = {metrics["training_loss"][epoch + 1]:.4e},\t'
            f'training_acc = {100 * metrics["training_acc"][epoch + 1]:.2f}%,\t'
            f'time = {epoch_time:.2f}s'
        )


def print_per_epoch_info(epoch, Paras, epoch_loss, training_loss, training_acc, test_loss, test_acc, run_time):
    epochs = Paras["epochs"][Paras["data_name"]]
    # result = [(k, f"{v:.4f}") for k, v in run_time.items()]
    if Paras["use_color"]:
        print(
            f'\033[34m epochs = \033[32m{epoch+1}/{epochs}\033[0m,\t\b'
            f'\033[34m epoch_loss = \033[32m{epoch_loss[epoch+1]:.4e}\033[0m,\t\b'
            f'\033[34m train_loss = \033[32m{training_loss[epoch+1]:.4e}\033[0m,\t\b'
            f'\033[34m train_acc = \033[32m{100 * training_acc[epoch+1]:.2f}%\033[0m,\t\b'
            f'\033[34m test_acc = \033[32m{100 * test_acc[epoch+1]:.2f}%\033[0m,\t\b'
            f'\033[34m time (ep, tr, te) = \033[32m({run_time["epoch"]:.2f}, {run_time["train"]:.2f}, {run_time["test"]:.2f})\033[0m')
    else:
        print(
        f'epochs = {epoch+1}/{epochs},\t'
        f'epoch_loss = {epoch_loss[epoch+1]:.4e},\t'
        f'train_loss = {training_loss[epoch+1]:.4e},\t'
        f'train_acc = {100 * training_acc[epoch+1]:.2f}%,\t'
        f'test_acc = {100 * test_acc[epoch+1]:.2f}%,\t'
        f'time (ep, tr, te) = ({run_time["epoch"]:.2f}, {run_time["train"]:.2f}, {run_time["test"]:.2f})')


def all_data_info():
    print(ParametersHub.data_list.__doc__)

def data_info_DHI():
    data = DataSets.adult_income_prediction(print_info=True, export_csv=False)

def data_info_CCFD():
    data = DataSets.credit_card_fraud_detection(print_info=True, export_csv=False)

def data_info_AIP():
    data = DataSets.adult_income_prediction(print_info=True, export_csv=False)

def data_info_EVP():
    data = DataSets.electric_vehicle_population(print_info=True, export_csv=False)

def data_info_GHP():
    data = DataSets.global_house_purchase(print_info=True, export_csv=False)

def data_info_HL():
    data = DataSets.health_lifestyle(print_info=True, export_csv=False)

def data_info_HQC():
    data = DataSets.Homesite_Quote_Conversion(print_info=True)

def data_info_IEEE_CIS():
    data = DataSets.IEEE_CIS_Fraud_Detection(print_info=True)

def data_info_MICP():
    data = DataSets.medical_insurance_cost_prediction(print_info=True)

def data_info_PPE():
    data = DataSets.particle_physics_event_classification(print_info=True)


def data_info(binary, class0, class1, train_dataset, test_dataset, _image_shape, transform):
    if binary:
            task_type = f"Binary ({class0} -> 0 vs {class1} -> 1)"
    else:
        task_type = "Multi-class (0-9)"

    print("\n" + "=" * 80)
    print(f"{'Summary':^80}")
    print("=" * 80)
    print(f"Task Type     : {task_type}")
    print(f"Train Samples : {len(train_dataset):,}")
    print(f"Test Samples  : {len(test_dataset):,}")
    print(f"Image Shape   : {_image_shape}")
    print(f"Transform     : {transform}")
    print("\n" + "=" * 80)