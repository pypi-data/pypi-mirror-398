import torch
from torch.utils.data import DataLoader
from diresa_torch.arch.models import Diresa
from diresa_torch.utils.utils import _r2_score, _set_components_to_mean


def latent_r2_per_variable(
    model: Diresa,
    data_loader: DataLoader,
    incr: bool = False,
    input_filter: callable = lambda data: data,
    target_filter: callable = lambda data: data,
    verbose: bool = False,
) -> list:
    """
    Computes R2 scores of latent components per variable. Variables should be on axis 1 (first is 0).
    If this is not the case, input_filter and target_filter can be used to swap axes.
    Prerequisite: latent components are already ordered.

    :param model: Diresa model
    :param data_loader: DataLoader
    :param var_axis: Axis (first is 0) of variables in output after target_filter (batch_size, ...), default is 1
    :param incr: If True incremental R2 score are calculated, default is False
    :param input_filter: Function used to filter input data, default is no filtering
    :param target_filter: Function used to filter target data, default is no filtering
    :param verbose: If True, prints most important component per variable, default is False
    :return: R2 scores of latent components per variable, shape (latent_dim, nbr of variables)
    """
    assert model.is_ordered(), "Model must be ordered"
    device = next(model.parameters()).device
    num_batches = len(data_loader)
    r2 = 0

    # var_axis IS NOT USED!!! test conv input!!! same for latent vectors???
    with torch.no_grad():
        for _, data in enumerate(data_loader):
            data = data.to(device)
            input_data = input_filter(data)
            target_data = target_filter(data)
            latent = model.base_encoder(input_data)  # (batch_size, latent_size)
            latent_size = latent.shape[1]
            nbr_vars = target_data.shape[1]
            r2_batch = torch.zeros(latent_size, nbr_vars, device=device)

            # For each latent dimension i:
            #   mask others -> decode -> compute R2 per field
            for i in range(latent_size):
                if not incr:
                    latent_masked = _set_components_to_mean(latent, i)  # (batch_size, latent_size)
                else:
                    latent_masked = _set_components_to_mean(latent, list(range(0, i+1)))
                # decode
                pred = model.base_decoder(latent_masked)
                # compute R2 per output field j
                for j in range(nbr_vars):
                    r2_batch[i, j] = _r2_score(target_data[:, j], pred[:, j])
            r2 += r2_batch
        r2 /= num_batches  # shape (latent_size, nbr_vars)

    if incr:
        for i in range(latent_size - 1, 0, -1):
            r2[i] = r2[i] - r2[i - 1]

    if verbose:
        if incr:
            print("Latent R² scores are incremental!")
        for i in range(latent_size):
            # best field index for latent dim i
            j_best = torch.argmax(r2[i]).item()
            score = r2[i, j_best].item()
            print(f"Latent dimension {i:02d} is most useful for reproducing "
                  f"{j_best} (R² = {score:.4f})")
        for j in range(nbr_vars):
            i_best = torch.argmax(r2[:, j]).item()
            score = r2[i_best, j].item()
            print(f"Field {j:02d} is best explained by latent dimension {i_best:02d} (R² = {score:.4f})")

    return r2


def latent_vectors(
    model: Diresa,
    data_loader: DataLoader,
    factor: float = 0.5,
    incr: bool = False,
    input_filter: callable = lambda data: data,
) -> torch.Tensor:
    """
    Calculates decoded latent vectors. Prerequisite: model must be ordered.
    See: https://journals.ametsoc.org/view/journals/aies/4/3/AIES-D-24-0034.1.xml
    Appendix D: c.Latent variable interpretation.

    :param model: Diresa model
    :param data_loader: DataLoader
    :param factor: Multiplication factor for  standard deviation
    :param incr: If True incremental vectors are calculated, default is False
    :param input_filter: Function used to filter input data, default is no filtering
    :return: Decoded latent vectors
    """
    assert model.is_ordered(), "Model must be ordered"
    device = next(model.parameters()).device
    num_batches = len(data_loader)
    mean_values = 0.
    std_dev = 0.

    with torch.no_grad():
        for _, data in enumerate(data_loader):
            data = data.to(device)
            input_data = input_filter(data)
            latent = model.base_encoder(input_data)  # (batch_size, latent_size)

            mean_values += torch.mean(latent, dim=0)
            std_dev += torch.std(latent, dim=0)

        mean_values /= num_batches
        std_dev /= num_batches

        latent_dim = mean_values.shape[0]
        latent_plus = mean_values.repeat(latent_dim, 1)  # (latent_size, latent_size)
        latent_minus = mean_values.repeat(latent_dim, 1)

        if not incr:
            for i in range(latent_dim):
                latent_plus[i, i] += factor * std_dev[i]
                latent_minus[i, i] -= factor * std_dev[i]
        else:
            for i in range(latent_dim):
                latent_plus[i, :i+1] += factor * std_dev[:i+1]
                latent_minus[i, :i+1] -= factor * std_dev[:i+1]

        decoded_plus = model.base_decoder(latent_plus)  # (latent_size, ...)
        decoded_minus = model.base_decoder(latent_minus)
        vectors = decoded_plus - decoded_minus  # (latent_size, ...)

        if incr:
            for i in range(latent_dim - 1, 0, -1):
                vectors[i] = vectors[i] - vectors[i-1]

    return vectors
