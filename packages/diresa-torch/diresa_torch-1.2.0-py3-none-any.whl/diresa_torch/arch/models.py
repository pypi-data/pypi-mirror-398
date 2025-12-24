import torch
import torch.nn as nn

from diresa_torch.arch.modules import DenseLayer, DistanceLayer, CNNLayer, OrderingLayer
from diresa_torch.arch.config import DiresaSetup, DiresaConfig
from typing import Tuple, Optional
from functools import reduce, wraps
import operator

import logging


def _cnn_output_flat(nb_stack, dims, cnn_output_filter):
    """
    Computes intermediate dimensions from CNN to FNN.
    Output dimensions of CNN is `(original_x / 2^len(stack)) * (orignal_y / 2^len(stack)) * output filter`.
    :param nb_stack: number of stacks in CNN models. Len of nb_stack defines how many times the input dimensions are divided by 2 due to the MaxPool2d layer.
    :param dims: original input dimensions
    :param cnn_output_filter: filters of the last CNN layer.
    """
    spatial_dims = [dim // (2**nb_stack) for dim in dims]
    return reduce(operator.mul, spatial_dims + [cnn_output_filter])


class _Encoder(nn.Module):
    """
    Provides the encoder for DIRESA.

    :param config: `DiresaConfig` object built by the static builder method DiresaSetup.create_config()
    """

    def __init__(self, config: DiresaConfig):
        super().__init__()

        if config.dense_config and not config.cnn_config:
            # NOTE:
            # Input of dense_units is input_shape[0].
            # By passing input dimension (config.input_shape[0])
            # by copy here we do not modify the original input_shape
            # If we mutate config.input_shape here in place we need to remember to NOT
            # modify it a second time in the decoder otherwise 2 layers are added.
            dense_units = (config.input_shape[0],) + tuple(config.dense_config.dense_units)
            self.network = DenseLayer(dense_units, config.activation)

            # This removes the last activation layer as DenseLayer always puts an activation function
            # after each Layer
            del self.network[-1]

        elif config.cnn_config and not config.dense_config:

            self.cnn_encoder = CNNLayer(
                config.cnn_config.stack,
                config.cnn_config.stack_filters,
                config.cnn_config.kernel_size,
                config.input_shape,
                config.activation,
            )

            # NOTE: If no dense_config is specified, there should be no activation function in the last layer.
            # In last block (-1) we remove the last RELU (-2). We do not change this in CNNLayer object as it
            # would require to pass in information about the structure of DIRESA into the CNNLayer class.
            # Fusing CNN and FFN structures should be done in the Encoder/Decoder models and not in submodules.
            del self.cnn_encoder[-1][-2]  # -2 as there is a MaxPool2D at [-1]

            self.flatten = nn.Flatten()

            self.network = nn.Sequential(
                self.cnn_encoder,
                self.flatten,
            )

        elif config.cnn_config and config.dense_config:

            self.cnn_encoder = CNNLayer(
                config.cnn_config.stack,
                config.cnn_config.stack_filters,
                config.cnn_config.kernel_size,
                config.input_shape,
                config.activation,
            )

            ffn_input = _cnn_output_flat(
                len(config.cnn_config.stack),
                config.input_shape[1:],
                config.cnn_config.stack_filters[-1],
            )

            dense_units = (ffn_input,) + tuple(config.dense_config.dense_units)

            self.ffn_encoder = DenseLayer(dense_units, config.activation)

            # need to delete last layer which is the activation function
            del self.ffn_encoder[-1]

            self.flatten = nn.Flatten()

            self.network = nn.Sequential(
                self.cnn_encoder, self.flatten, self.ffn_encoder
            )

    def __getitem__(self, key):
        """Enable subscriptable access"""
        return self.network[key]

    def __delitem__(self, key):
        """Enable item deletion"""
        del self.network[key]

    def forward(self, x):
        return self.network(x)


class _Decoder(nn.Module):
    def __init__(self, config: DiresaConfig):
        super().__init__()

        if config.dense_config and not config.cnn_config:
            # NOTE: Do not change config.input_shape in place, see comment in Encoder
            # Case where we only have dense units. Input of dense_units is input_shape[0]
            # (3, 64, 64, 2) where 3 is input and 2 is latent space will become
            # (64, 64, 3) when reversing.
            dense_units = (config.input_shape[0],) + tuple(config.dense_config.dense_units)

            self.network = DenseLayer(dense_units, config.activation, reverse=True)

            # this deletes the last activation layer as DenseLayer always puts an activation function
            # after each Linear layer.
            del self.network[-1]

        elif config.cnn_config and not config.dense_config:
            # spatial dimensions at the end of the CNN layer
            spatial_dims = [
                dim // (2 ** len(config.cnn_config.stack))
                for dim in config.input_shape[1:]
            ]

            # flatten output from the cnn which depends on dimensions of x/y and the final number
            # of filters.
            cnn_flat_dims = _cnn_output_flat(
                len(config.cnn_config.stack),
                config.input_shape[1:],
                config.cnn_config.stack_filters[-1],
            )

            unflatten_shape = (
                cnn_flat_dims // (spatial_dims[0] * spatial_dims[1]),
                *spatial_dims,
            )

            # need to unflatten from latent space to correct cnn input dimension
            self.unflatten = nn.Unflatten(1, unflatten_shape)

            self.cnn_decoder = CNNLayer(
                config.cnn_config.stack,
                config.cnn_config.stack_filters,
                config.cnn_config.kernel_size,
                config.input_shape,
                config.activation,
                reverse=True,
            )

            # Activation function is at the last position in the decoder
            del self.cnn_decoder[-1][-1]

            self.network = nn.Sequential(self.unflatten, self.cnn_decoder)

        elif config.cnn_config and config.dense_config:
            ffn_input = _cnn_output_flat(
                len(config.cnn_config.stack),
                config.input_shape[1:],
                config.cnn_config.stack_filters[-1],
            )

            # NOTE:
            # Will be reversed when buildind dense layers such that
            # last layer of fully connected feeding into CNN has the right (flatten) output
            # dimension.
            dense_units = (ffn_input,) + tuple(config.dense_config.dense_units)

            self.ffn_decoder = DenseLayer(dense_units, config.activation, reverse=True)

            spatial_dims = [
                dim // (2 ** len(config.cnn_config.stack))
                for dim in config.input_shape[1:]
            ]

            unflatten_shape = (config.cnn_config.stack_filters[-1], *spatial_dims)

            self.unflatten = nn.Unflatten(1, unflatten_shape)

            self.cnn_decoder = CNNLayer(
                config.cnn_config.stack,
                config.cnn_config.stack_filters,
                config.cnn_config.kernel_size,
                config.input_shape,
                config.activation,
                reverse=True,
            )
            # Delete activation function which is last element in last block
            del self.cnn_decoder[-1][-1]

            self.network = nn.Sequential(
                self.ffn_decoder, self.unflatten, self.cnn_decoder
            )

    def __getitem__(self, key):
        """Enable subscriptable access"""
        return self.network[key]

    def __delitem__(self, key):
        """Enable item deletion"""
        del self.network[key]

    def forward(self, x):
        return self.network(x)


class Diresa(nn.Module):
    """
    Distance Regularized Autoencoder.

    Can be built using class method ``from_hyper_param`` which builds the encoder and decoder from a list of hyper parameters.
    DIRESA can also be built by providing a custom encoder and decoder using class method ``from_custom``.
    """

    @classmethod
    def from_hyper_param(
        cls,
        # Global parameters
        input_shape: Tuple[int, ...] = (),
        activation: nn.Module = nn.ReLU(),
        # Dense parameters
        dense_units: Optional[Tuple[int, ...]] = None,
        # CNN parameters
        stack: Optional[tuple[int, ...]] = None,
        stack_filters: Optional[Tuple[int, ...]] = None,
        kernel_size: Tuple[int, int] = (3, 3),
    ):
        """
        Builds DIRESA from hyperparameters.
        DIRESA can be built using fully connected layers, CNN layers or a combination of both.

        The argument `dense_units` is used to add fully connected layers, where the length of the tuple represents depth of
        the network and each individual value represents the number of nodes per layer. First element describes the first
        hidden layer. Last layer defines the output layer which is the size of latent space. E.g. ``dense_units = (16, 32, 64)``
        is a fully connected network with two hidden layers `(16, 32)` and last layer which defines latent space of size `64`.
        When only one value is present it represents a linear projection on to a latent space with dimensions of that value
        (as for the last layer no activation is used).

        To build a convolutional encoder, parameters `stack` and `stack_filters` have to be provided. `stack` handles the number
        of convolutional layers per block and `stack_filters` handles the number of filters per block. That is, if
        ``stack = (2, 1)`` and ``stack_filters = (16, 8)``, the encoder network is going to be split as
        `[Conv2D 16 -> Activation -> Conv2D 16 -> Activation] -> MaxPool -> [Conv2D 8] -> MaxPool -> Flatten`.
        Each block is always followed by a `MaxPool` layer and at the end a `Flatten` layer is added.

        If dense parameters and convolutional parameters are both specified the network is built as follows:
        `[CNN] -> [Dense] -> LatentSpace -> [Dense] -> [CNN]`.


        :param input_shape: is the shape of input features
        :param activation: activation function used by all layers, except for the last layer of the encoder/decoder, which doesn't have an activation function
        :param stack: the number of Conv2D layers in each block
        :param stack_filters: number of filters (out channels) for the Conv2D layers in each block, `len(stack_filters)` has always to be equal to `len(stack)`
        :param kernel_size: kernel size for all Conv2D layers
        :param dense_units: tuple which describes the width of each fully connected layer
        """

        # Create global configuration with sub-configs
        # General config is not saved at the moment in DIRESA class.
        # => Not possible to retrieve it by calling Diresa.config.
        config = DiresaSetup.create_config(
            stack=stack,
            stack_filters=stack_filters,
            kernel_size=kernel_size,
            input_shape=input_shape,
            dense_units=dense_units,
            activation=activation,
        )

        return cls(_Encoder(config), _Decoder(config))

    @classmethod
    def from_custom(cls, encoder: nn.Module, decoder: nn.Module):
        """
        Builds Diresa from custom provided encoder and decoder. Distance and
        ordering layers are added through the Diresa class.

        :param encoder: encoder model
        :param decoder: decoder model
        """
        return cls(encoder, decoder)

    # Could make constructor private to avoid direct instanciation.
    # Does not make a difference at the moment as there are
    # no additional checks in `from_custom`.

    def __init__(self, encoder: nn.Module, decoder: nn.Module):
        super().__init__()

        # Called base as those are the simple encoders/decoders which
        # produce latent space and decode latent space
        # but do not provide any additional features such as distance computation
        # or ordering
        self.base_encoder = encoder
        self.dist_layer: DistanceLayer = DistanceLayer(dim_less=True)
        self.base_decoder = decoder
        self.ordering_layer = OrderingLayer()

    def __random_ordering_index(self, x: torch.Tensor) -> torch.Tensor:
        """
        Shuffles batch x.
        """
        batch_size = x.shape[0]
        perm_indices = torch.randperm(batch_size, device=x.device)
        return perm_indices

    def get_ordering(self) -> Optional[torch.Tensor]:
        """
        :return: Tensor representing ordering of the latent components by `R2-score` or `None` if no ordering has been computed yet.
        """
        return self.ordering_layer.order

    def is_ordered(self) -> bool:
        """
        Returns `True` if ordering of the latent components has been computed on the model, `False` otherwise.

        :return: Ordering status
        """
        return self.ordering_layer.order is not None

    def reset_ordering(self) -> Optional[torch.Tensor]:
        """
        Removes current ordering and returns it.

        :return: Tensor representing current ordering or `None` if no ordering has been computed yet.
        """
        current = self.ordering_layer.order
        self.ordering_layer.order = None
        return current

    @staticmethod
    def __warn_ordering(f):
        """
        Decorator used to produce a warning when no ordering has been computed
        """

        # used to display docs from wrapped function
        @wraps(f)
        def check_order(*args, **kwargs):
            self = args[0]
            if not self.is_ordered():
                # NOTE: Could improve doc here
                logging.warning(
                    "Latent components of Diresa have not yet been ordered. To produce an ordering of latent components call order_diresa() from trainer module"
                )
            return f(*args, **kwargs)

        return check_order

    @__warn_ordering
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Runs encoder to provide latent space representation, latent components are ordered by `R2-score` if ordering has been previously computed.

        :param x: batch of original data
        :return: encoded batch, ordered if ordering has been previously computed.
        """
        encoded = self.base_encoder(x)
        ordered = self.ordering_layer(encoded)
        return ordered

    @__warn_ordering
    def decode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Runs decoder to provide reconstructed data from latent space representation (keeping ordering of the latent components in mind if ordering has been computed).

        :param x: batch of latent data.
        :return: decoded batch
        """
        reversed_ordering = self.ordering_layer(x, reverse=True)
        return self.base_decoder(reversed_ordering)

    # TODO: Could find a a naming scheme here to show
    # that this is part of the DIRESA arch.
    def _encode_with_distance(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encodes batch `x` into latent space and compute distance between encoder
        and twin encoder in original and latent space.

        :param x: Batch to encode
        :return: (latent, distance) which are the encoded latent variables as well as
            the distance between the encoder and twin_encoder in original and latent space.
        """
        x1 = x
        y1: torch.Tensor = self.base_encoder(x1)

        # Twin encoder
        index = self.__random_ordering_index(x)
        x2 = x1[index]
        y2 = y1[index]

        dist: torch.Tensor = self.dist_layer(x1, x2, y1, y2)
        return y1, dist

    # NOTE: We could have different approaches here
    # - Could either run the full model in train mode and restrict eval mode to
    #   only do encoder/decoder steps without computing distances and covariance.
    #   This enables faster inference but makes it impossible to evaluate distance
    #   and cov losses
    # - Or could use full model as well in eval mode. This would make it possible
    #   to get distance and cov loss on val/test sets. Then provide an additional
    #   method which skips internal layers and does simple encoder/decoder steps
    #   for inference purposes only.
    # Current approach: No difference between training and validation. Both use the
    # full model. Use trainer.predict function to bypass distance layer.
    #

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Produces ``reconstructed``, ``latent`` and ``distance`` information
        """
        latent, dist = self._encode_with_distance(x)

        reconstructed = self.base_decoder(latent)

        # returns reconstrcuted for reconstruction loss
        # y1 is latent, used for covariance loss
        # returns distances between points for distance loss
        return reconstructed, latent, dist

    def fast_eval(self, x: torch.Tensor) -> torch.Tensor:
        """
        Produces an reconstructed output by using only encoder and decoder.
        This skips the distance layer and ordering layer.

        :param x: batch to evaluate.
        """
        return self.base_decoder(self.base_encoder(x))
