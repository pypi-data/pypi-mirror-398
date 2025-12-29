import torch
from torch.nn.utils import parameters_to_vector
import torch.nn.functional as F

def loss(X, y, model, loss_fn, Paras):
    pred = model(X)
    _, c = pred.shape

    if c == 1:
        # Logistic Regression with L2 (binary)
        if isinstance(loss_fn, torch.nn.BCEWithLogitsLoss):
            pred = pred.view(-1).float()
            loss = loss_fn(pred, y.float())
            if Paras["model_name"] == "LogRegressionBinaryL2":
                x = parameters_to_vector(model.parameters())
                lam = Paras["lambda"]
                loss = loss + 0.5 * lam * torch.norm(x, p=2) ** 2

        else:
            assert False

    else:
        # Least Square (mutil)
        if isinstance(loss_fn, torch.nn.MSELoss):
            # loss
            y_onehot = F.one_hot(y.long(), num_classes=c).float()
            pred_prob = torch.softmax(pred, dim=1)
            loss = 0.5 * loss_fn(pred_prob, y_onehot) * float(c)

        elif isinstance(loss_fn, torch.nn.CrossEntropyLoss):
            # loss
            loss = loss_fn(pred, y.long())

        else:
            print(
                f"\033[34m **** isinstance(loss_fn, torch.nn.MSELoss)? {loss_fn} **** \033[0m"
            )
            assert False

    return loss

def compute_loss_acc(X, y, model, loss_fn, Paras):
    pred = model(X)
    m, c = pred.shape

    if c == 1:
        # Logistic Regression (binary)
        if isinstance(loss_fn, torch.nn.BCEWithLogitsLoss):
            pred = pred.view(-1).float()
            loss = loss_fn(pred, y).item()

            if Paras["model_name"] == "LogRegressionBinaryL2":
                x = parameters_to_vector(model.parameters())
                lam = Paras["lambda"]
                loss = (loss + 0.5 * lam * torch.norm(x, p=2) ** 2).item()

            pred_label = (torch.sigmoid(pred) > 0.5).float()
            correct = (pred_label == y).sum().item()

        else:
            assert False

    else:

        # Least Square （mutil）
        if isinstance(loss_fn, torch.nn.MSELoss):
            # loss
            y_onehot = F.one_hot(y.long(), num_classes=c).float()
            pred_label = pred.argmax(1).long()
            pred_ont = F.one_hot(pred_label, num_classes=c).float()
            loss = 0.5 * loss_fn(pred_ont, y_onehot).item() * c

            # acc
            correct = (pred_label == y).sum().item()

        elif isinstance(loss_fn, torch.nn.CrossEntropyLoss):

            # loss
            loss = loss_fn(pred, y.long()).item()

            # acc
            # acc
            pred_label = pred.argmax(1).long()
            correct = (pred_label == y).sum().item()

        else:
            print(
                f"\033[34m **** isinstance(loss_fn, torch.nn.MSELoss)? {isinstance(loss_fn, torch.nn.MSELoss)} **** \033[0m"
            )
            assert False

    return loss, correct

def get_loss_acc(dataloader, model, loss_fn, Paras):
    # model.eval()
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    loss, correct = 0, 0

    device = Paras["device"]

    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device).float(), y.to(device).float()
            per_loss, per_acc = compute_loss_acc(X, y, model, loss_fn, Paras)

            loss += per_loss
            correct += per_acc

    loss /= num_batches
    correct /= size

    return loss, correct