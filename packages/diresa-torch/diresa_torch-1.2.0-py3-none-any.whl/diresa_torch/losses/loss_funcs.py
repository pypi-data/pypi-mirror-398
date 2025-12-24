import torch
import torch.nn as nn


class LatentCovLoss(nn.Module):
    """
    Computes Covariance Loss on input batch.
    """

    # TODO: Simulated Annealing. Not present by default in pytorch. Needs custom implementation
    # With staged training might not really need it anymore as parameters are tuned independently

    def __init__(self):
        super().__init__()

    def forward(self, latent, _):
        """
        :param latent: is the latent space representation of the current batch
        :return: covariance loss
        """
        cov = torch.cov(torch.transpose(latent, 0, 1), correction=1)
        cov_square = cov * cov  # elem wise mult
        # number of covariance entries (need to subtract 1 to not take into account diagonal variance metrics)
        nbr_of_cov = latent.shape[-1] * (latent.shape[-1] - 1)
        cov_loss = (torch.sum(cov_square) - torch.trace(cov_square)) / float(nbr_of_cov)
        return cov_loss


class MAEDistLoss(nn.Module):
    """
    Absolute Error between original and latent distances
    """

    def __init__(self):
        super().__init__()

    def forward(self, distances, _):
        """
        :param distances: batch of original and latent distances between twins
        :return: mean of absolute errors
        """
        ae = torch.abs(distances[:, 0] - distances[:, 1])
        return torch.mean(ae)


class MALEDistLoss(nn.Module):
    """
    Absolute Error between logarithm of original and latent distances
    """

    def __init__(self, factor=1.):
        """
        :param factor: distance multiplication factor
        """
        super().__init__()
        self.factor = factor

    def forward(self, distances, _):
        """
        :param distances: batch of original and latent distances between twins
        :return: mean of absolute logarithmic errors
        """
        ale = torch.abs(torch.log1p(self.factor * distances[:, 0]) - torch.log1p(self.factor * distances[:, 1]))
        return torch.mean(ale)


class MAPEDistLoss(nn.Module):
    """
    Absolute Percentage Error between original and latent distances
    """

    def __init__(self):
        super().__init__()

    def forward(self, distances, _):
        """
        :param distances: batch of original and latent distances between twins
        :return: mean of absolute percentage errors
        """
        epsilon = 1e-8
        ape = torch.abs(
            (distances[:, 0] - distances[:, 1]) / (distances[:, 0] + epsilon)
        )
        return torch.mean(ape)


class MSEDistLoss(nn.Module):
    """
    Squared Error between original and latent distances
    """

    def __init__(self):
        super().__init__()

    def forward(self, distances, _):
        """
        :param distances: batch of original and latent distances between twins
        :return: mean of squared errors
        """
        se = torch.square(distances[:, 0] - distances[:, 1])
        return torch.mean(se)


class MSLEDistLoss(nn.Module):
    """
    Squared Error between logarithm of original and latent distances
    """

    def __init__(self, factor=1.):
        """
        :param factor: distance multiplication factor
        """
        super().__init__()
        self.factor = factor

    def forward(self, distances, _):
        """
        :param distances: batch of original and latent distances between twins
        :return: mean of squared logarithmic errors
        """
        sle = torch.square(torch.log1p(self.factor * distances[:, 0]) - torch.log1p(self.factor * distances[:, 1]))
        return torch.mean(sle)


class CorrDistLoss(nn.Module):
    """
    Correlation loss between original and latent distances
    """

    def __init__(self):
        super().__init__()

    def forward(self, distances, _):
        """
        :param distances: batch of original and latent distances between twins
        :return: 1 - correlation coefficient
        """
        cov = torch.cov(torch.transpose(distances, 0, 1), correction=1)
        cov_sqrt = torch.sqrt(torch.abs(cov))
        corr = 1 - cov[0, 1] / (cov_sqrt[0, 0] * cov_sqrt[1, 1])
        return 1 - corr


class CorrLogDistLoss(nn.Module):
    """
    Correlation loss between  logarithm of original and latent distances
    """

    def __init__(self, factor=1.):
        """
        :param factor: distance multiplication factor
        """
        super().__init__()
        self.factor = factor

    def forward(self, distances, _):
        """
        :param distances: batch of original and latent distances between twins
        :return: 1 - correlation coefficient (of logarithmic distances)
        """
        cov = torch.cov(torch.transpose(torch.log1p(self.factor * distances), 0, 1), correction=1)
        cov_sqrt = torch.sqrt(torch.abs(cov))
        corr = 1 - cov[0, 1] / (cov_sqrt[0, 0] * cov_sqrt[1, 1])
        return 1 - corr
