import torch
from diresa_torch.arch.models import Diresa


def save_diresa(model: Diresa, path: str):
    """
    Saves Diresa model parameters to disk

    :param model: Diresa model to save
    :param path: path/file to save model paramaters
    """
    torch.save(model.state_dict(), path)


def load_diresa(model: Diresa, path: str) -> Diresa:
    """
    Loads Diresa model parameters from disk

    :param model: Diresa model to load
    :param path: path/file to load model parameters
    :return: Diresa model
    """
    diresa_state = torch.load(path)
    if 'ordering_layer._order' in diresa_state:
        model.ordering_layer.order = diresa_state['ordering_layer._order']
    model.load_state_dict(diresa_state)
    return model


def _r2_score(y: torch.Tensor, y_pred: torch.Tensor):
    """
    :param y: original dataset
    :param y_pred: predicted dataset
    :return: R2 score between y and y_pred
    """
    error = torch.sum(torch.square(y - y_pred))
    var = torch.sum(torch.square(y - torch.mean(y, dim=0)))
    r2 = 1.0 - error / var
    return r2.item()  # Convert to Python scalar


def _set_components_to_mean(latent: torch.Tensor, retain_idxs: list):
    """
    Set all latent components to mean except the ones in retain_idxs.
    retain_idxs may be a single int or a list of ints, corresponding to the indexes of these dimensions.

    :param latent: latent dataset
    :param retain_idxs: list of indexes which will be retained and thus not set to their mean value
    :return: a new latent dataset with the dimensions which were not in retain_idxs set to their mean value
    """
    if isinstance(retain_idxs, int):
        retain_idxs = [retain_idxs]

    with torch.no_grad():
        mean_values = latent.mean(dim=0, keepdim=True)

        mask = torch.ones_like(latent, dtype=torch.bool)
        mask[:, retain_idxs] = False  # these dims keep original values

        result = torch.where(mask, mean_values, latent)
    return result
