import torch
from typing import Optional, Dict
import logging
from torch.utils.data import DataLoader
from diresa_torch.arch.models import Diresa
from diresa_torch.utils.utils import _r2_score, _set_components_to_mean
from operator import add


def __compute_losses(outputs, targets, criteria, loss_weights):
    """
    Helper function to compute losses given outputs, targets, criteria and weights.

    :param outputs: Model outputs (tuple of 3 elements: reconstructed, latent, distance)
    :param targets: Target values (tuple of 3 elements: data, None, None)
    :param criteria: List of loss functions [ReconstructionLoss, CovarianceLoss, DistanceLoss]
    :param loss_weights: Weighting factor for the different losses
    :return: Tuple of (individual_losses, total_weighted_loss)
    """
    individual_losses = [c(o, t) for c, o, t in zip(criteria, outputs, targets)]
    weighted_losses = [w * l for w, l in zip(loss_weights, individual_losses)]
    total_weighted_loss = torch.stack(weighted_losses).sum()

    return individual_losses, total_weighted_loss


def __set_non_trainable(model):
    for param in model.parameters():
        param.requires_grad = False


def __loss_string_repr(criteria, suffix=""):
    """
    Helper functions producing string criteria of
    losses. String repr is used to log each loss with an
    understandable name.
    """
    # Ordering of loss output values
    # Use class name without the last () as name for the loss
    loss_names = [f"{c}"[:-2] for c in criteria] + ["WeightedLoss"]

    # Criteria list can change depending on training mode.
    # When running normal criteria[0] is Reconstruction loss (and len(criteria == 3))
    # During staged training, when encoder is trained
    # criteria[0] is LatentCovLoss (and len(criteria == 2)).
    # When decoder is trained criteria[0] is Recon (and len(criteria == 1))
    if len(criteria) == 3 or len(criteria) == 1:
        loss_names[0] = "Recon" + loss_names[0]

    # add "train" suffix for output
    loss_names = list(map(lambda x: x + suffix, loss_names))
    return loss_names


def __evaluate(
    produce_output: callable,
    produce_target: callable,
    test_loader: DataLoader,
    criteria: list,
    device: torch.device,  # device is still required here as this function does not have access to model
    loss_weights: list,
    input_filter: callable,
    target_filter: callable,
    loss_suffix: str,
) -> Dict[str, float]:
    """
    Evaluate DIRESA (does not track gradient) by computing all three losses (reconstruction, covariance, distance) with help of the ``produce_output`` and ``produce_input`` functions. Those functions are provided as lambdas which makes it easier to match the outputs, targets and criteria together for evaluation purposes.

    :param produce_output: callable function producing outputs from model. Takes as input batch data.
    :param produce_target: callable function producing target values for criterion. Takes as input batch data.
    :param test_loader: Test data loader
    :param criteria: List of loss functions, depends on what part is being evaluated.
    :param device: Device to evaluate on
    :param loss_weights: Weighting factor for the different losses (in order [Reconstruction, Covariance, Distance])
    :param loss_suffix: Appends a suffix to the loss as __eval can be used for validation during training or evaluation (when passing in test set)
    :param input_filter: Function used to filter input data
    :param target_filter: Function used to filter target data
    :return: Dictionary with average losses: individual losses + weighted total loss
    """
    total_losses = [0.0] * (len(criteria) + 1)
    num_batches = 0

    loss_names = __loss_string_repr(criteria, loss_suffix)

    with torch.no_grad():
        for _, data in enumerate(test_loader):
            data = data.to(device)

            input_data = input_filter(data)
            target_data = target_filter(data)
            targets = produce_target(target_data)
            outputs = produce_output(input_data)

            # outputs_losses, loss = _compute_losses(outputs, target, criteria, loss_weights)
            outputs_losses, loss = __compute_losses(
                outputs, targets, criteria, loss_weights
            )

            # Accumulate losses
            all_losses = outputs_losses + [loss]
            total_losses = list(
                map(add, total_losses, [loss.item() for loss in all_losses])
            )
            num_batches += 1

    avg_losses = [loss / num_batches for loss in total_losses]

    result = {name: avg_loss for name, avg_loss in zip(loss_names, avg_losses)}

    return result


def train_diresa(
    model: Diresa,
    train_loader: DataLoader,
    criteria: list,
    optimizer: torch.optim.Optimizer,
    num_epochs: int = 10,
    val_loader: Optional[DataLoader] = None,
    loss_weights: list = [1.0, 1.0, 1.0],
    staged_training: bool = False,
    input_filter: callable = lambda data: data,
    target_filter: callable = lambda data: data,
    callbacks: Optional[list] = None,  # Not IMPL at the moment
) -> dict[str, dict[str, list[float]]]:
    """
    Trains `model`. Needs to provide multiple loss function in order to train de different parts of the model.
    CovarianceLoss and DistanceLoss are used to produce an interpretable latent space
    while ReconstructionLoss is used to produce an output.

    :param model: The model to train
    :param train_loader: Training data loader
    :param criteria: List of Loss function. With order [ReconstructionLoss, CovarianceLoss, DistanceLoss]
    :param optimizer: Optimizer
    :param num_epochs: Number of epochs
    :param val_loader: Optional validation loader
    :param loss_weights: Weighting factor for the different losses. With order [ReconstructionLoss, CovarianceLoss, DistanceLoss]
    :param staged_training: If set to True will train the encoder and the decoder separately for `num_epochs` each.
    :param input_filter: Function used to filter input data, default is no filtering
    :param target_filter: Function used to filter target data, default is no filtering
    :param callbacks: Optional list of callback functions
    :return: Dict with training (losses, metrics) and validation (if val_loader is provided).
    """
    assert (
        callbacks is None
    ), "Callbacks are not tested at the moment. Remove param or set to None"

    def __train_for_epochs(
        produce_output: callable,
        produce_target: callable,
        criteria,
        loss_weights,
        device,
        prepend_log="DIRESA",
    ):
        """
        Nested function for training loop. Factors out common functionalities for training,
        while providing custom information about what loss to train for used to differentiate
        between staged training and full training.

        :param produce_output: callable function producing outputs from model. Takes as input batch data.
        :param produce_target: callable function producing target values for criterion. Takes as input batch data.
        :param criteria: List of loss functions
        :param loss_weights: weights for each loss function
        :param device: hardware device used.
        :param prepend_log: String to prepend to logging output
        """
        assert len(criteria) == len(
            loss_weights
        ), "Number of criteria and their associated weights does not match"

        loss_names = __loss_string_repr(criteria, "_train")
        history = {name: [] for name in loss_names}

        for epoch in range(num_epochs):
            # each criterion loss + combined weighted loss
            epoch_loss = [0.0] * (len(criteria) + 1)
            num_batches = 0

            for _, data in enumerate(train_loader):
                data = data.to(device)
                input_data = input_filter(data)
                target_data = target_filter(data)
                target = produce_target(target_data)
                outputs = produce_output(input_data)

                optimizer.zero_grad()
                outputs_losses, loss = __compute_losses(
                    outputs, target, criteria, loss_weights
                )

                # accumulates gradient in each tensor -> Backprop
                # backpropagated loss in weighted sum of each loss.
                loss.backward()

                optimizer.step()

                # add weighted loss to final losses
                all_losses = outputs_losses + [loss]
                epoch_loss = list(
                    map(add, epoch_loss, [loss.item() for loss in all_losses])
                )
                num_batches += 1

                if callbacks:
                    raise NotImplementedError
                    # for callback in callbacks:
                    #     callback(epoch, batch_idx, loss.item())

            avg_loss = list(map(lambda loss: loss / num_batches, epoch_loss))

            for name, loss in zip(loss_names, avg_loss):
                history[name].append(loss)

            # val loader is defined in exterior function
            if val_loader:
                val_dict = __evaluate(
                    produce_output,
                    produce_target,
                    val_loader,
                    criteria,
                    device,
                    loss_weights,
                    input_filter,
                    target_filter,
                    loss_suffix="_val",
                )
                for name, loss in val_dict.items():
                    if name in history:
                        history[name].append(loss)
                    else:
                        history[name] = [loss]

            # print out last entry in history for each epoch
            log_str = ", ".join(
                [f"{name}: {values[-1]:.4e}" for name, values in history.items()]
            )
            logging.info(f"{prepend_log}: Epoch {epoch + 1}/{num_epochs} - {log_str}")

        return history

    # End of nested function

    # takes the device onto which the first tensor is registered
    device = next(model.parameters()).device

    if staged_training:
        # train encoder, cov and dist loss
        hist_encoder = __train_for_epochs(
            produce_output=lambda data: model._encode_with_distance(data),
            produce_target=lambda _: (None, None),
            criteria=criteria[1:],  # cov and dist criteria
            loss_weights=loss_weights[1:],  # cov and dist weights
            device=device,
            prepend_log="Encoder",
        )

        # freeze encoder weights
        __set_non_trainable(model.base_encoder)

        # train decoder, only rec loss
        hist_decoder = __train_for_epochs(
            produce_output=lambda data: model.base_decoder(model.base_encoder(data)),
            produce_target=lambda data: data,
            criteria=criteria[:1],
            loss_weights=loss_weights[:1],
            device=device,
            prepend_log="Decoder",
        )

        hist = {"Encoder": hist_encoder, "Decoder": hist_decoder}
        return hist

    else:
        # data is produced by forward pass of model.
        hist_diresa = __train_for_epochs(
            lambda data: model(data),
            lambda data: (data, None, None),
            criteria,
            loss_weights,
            device=device,
            prepend_log="Encoder_Decoder",
        )

        # To keep consistency with staged training where encoder
        # and decoder losses are accessed via a key, the same is done
        # when all weights are trained simultaneously.
        hist = {"Encoder_Decoder": hist_diresa}
        return hist


def evaluate_diresa(
    model: Diresa,
    test_loader: DataLoader,
    criteria: list,
    loss_weights: list = [1.0, 1.0, 1.0],
    input_filter: callable = lambda data: data,
    target_filter: callable = lambda data: data,
) -> Dict[str, float]:
    """
    Evaluates `model` using `test_loader`

    :param model: The model to evaluate
    :param test_loader: Test data loader
    :param criteria: List of loss functions [ReconstructionLoss, CovarianceLoss, DistanceLoss]
    :param loss_weights: Weighting factor for the different losses
    :param input_filter: Function used to filter input data, default is no filtering
    :param target_filter: Function used to filter target data, default is no filtering
    :return: Dictionary with averaged losses: individual criterion loss + weighted total loss
    """
    assert (
        len(criteria) == 3
    ), "Need to provide 3 criteria for DIRESA evaluation, namely [ReconstructionLoss, CovarianceLoss, DistanceLoss]"

    device: torch.device = next(model.parameters()).device

    eval_dict = __evaluate(
        # model.forward(data) produces (reconstructed, latent, dist)
        lambda data: model.forward(data),
        lambda data: (data, None, None),
        test_loader=test_loader,
        device=device,
        criteria=criteria,
        loss_weights=loss_weights,
        input_filter=input_filter,
        target_filter=target_filter,
        loss_suffix="_eval",
    )
    log_str = ", ".join([f"{name}: {value:.4e}" for name, value in eval_dict.items()])
    logging.info(log_str)
    return eval_dict


def predict_diresa(
    model: Diresa,
    data_loader: DataLoader,
    input_filter: callable = lambda data: data,
) -> torch.Tensor:
    """
    predict_diresa is the reconstructed dataset from `data_loader` passed through `model`.
    Provides faster inference as distance and covariance are not computed for inference.

    :param model: model to use to produce a prediction
    :param data_loader: data to be reconstructed
    :param input_filter: function used to filter input data, default is no filtering
    :return: prediction
    """

    device = next(model.parameters()).device
    predictions = []

    with torch.no_grad():
        for _, data in enumerate(data_loader):
            data = data.to(device)
            input_data = input_filter(data)
            outputs = model.fast_eval(input_data)
            predictions.append(outputs.cpu())

    return torch.cat(predictions, dim=0)


def order_diresa(
    model: Diresa,
    data_loader: DataLoader,
    cumul=False,
    input_filter: callable = lambda data: data,
    target_filter: callable = lambda data: data,
) -> list:
    """
    Sets ordering of the OrderingLayer.
    Limitations: assumes a flat latent space (rank of latent is 2).
    If `cumul` is set to true it iteratively selects next component based on
    additional combined explanatory power with previously selected components, if it is set
    to false it only sorts based on the R² of each latent dimension separately.

    :param model: The model on which to produce the ordering
    :param data_loader: The data_loader from which to produce the ordering
    :param cumul: If `False` only sorts based on single-dimension R²
    :param input_filter: Function used to filter input data, default is no filtering
    :param target_filter: Function used to filter target data, default is no filtering
    :return: (cumulative) R² scores of latent components
    """

    logging.info(f"Batch size for ordering is {data_loader.batch_size}")

    device = next(model.parameters()).device
    first_r2_scores = []

    with torch.no_grad():
        R2_full = []
        # produce R2 per batch
        for _, data in enumerate(data_loader):
            data = data.to(device)

            # 1. Produce latent dataset
            input_data = input_filter(data)
            target_data = target_filter(data)
            latent = model.base_encoder(input_data)
            assert len(latent.shape) == 2, "Latent space is not flattened"
            R2_full.append(_r2_score(target_data, model.base_decoder(latent)))

            # 2. Produce l latent samples for which every latent dimensions is averaged except the l-th one
            averaged = map(
                lambda i: _set_components_to_mean(latent, i),
                range(latent.shape[1]),
            )

            # 3. Produce l decoded samples from l latent samples
            decoded = map(lambda latent: model.base_decoder(latent), averaged)

            # 4. Compute R2 by comparing l decoded with original x
            r2 = list(map(lambda pred: _r2_score(target_data, pred), decoded))

            first_r2_scores.append(r2)

        first_r2_scores = torch.tensor(first_r2_scores, device=device).mean(dim=0)
        logging.info(f"Total R² score is: {torch.tensor(R2_full, device=device).mean(dim=0)}")

        first_ordering = torch.argsort(first_r2_scores, descending=True)

        if not cumul:
            ordering = first_ordering
            r2_scores = first_r2_scores[ordering].tolist()

        else:
            # Full cumulative iterative selection
            ordering = [first_ordering[0].item()]
            # Start the selection with the best single-R2 dimension. Ordering keeps track of selected latent components in order
            # Remaining will be a set of all the latent indices, except for the ones we already chose
            # So it will hold the possible candidates
            remaining = set(range(first_r2_scores.shape[0])) - set(ordering)
            # Now we compute the r2 score of the first latent, to see what we are improving upon
            r2_scores = [first_r2_scores[ordering[0]].item()]

            # Now we want to loop n-1 times, until all dimensions are fixed.
            while remaining:
                candidate_scores = {}  # Dictionary with key = candidate index, value = combined R2 scores if we would add this one next

                for cand in remaining:
                    r2_subscores = []
                    for _, data in enumerate(data_loader):
                        data = data.to(device)

                        input_data = input_filter(data)
                        target_data = target_filter(data)
                        latent = model.base_encoder(input_data)

                        # Keep only ordering + this candidate active
                        active_dims = list(set(ordering) | {cand})
                        # Now we isolate the combined effect of the excluded dimensions:
                        mod_latent = _set_components_to_mean(latent, active_dims)
                        decoded = model.base_decoder(mod_latent)
                        r2_subscores.append(_r2_score(target_data, decoded))

                    cand_score = torch.tensor(r2_subscores,
                                              device=device).mean().item()
                    candidate_scores[cand] = cand_score

                # Select the next best latent
                # When comparing tuples (index, score), sort by the score, so element 1 
                next_best = max(candidate_scores.items(), key=lambda x: x[1])
                ordering.append(next_best[0])
                remaining.remove(next_best[0])
                r2_scores.append(next_best[1])

            ordering = torch.tensor(ordering, device=device)

        model.ordering_layer.order = ordering
        logging.info(f"Ordered R² scores are: {r2_scores}")

        return r2_scores
