"""
KAN_TVAE.py

Modified TVAE Implementation with Kolmogorov–Arnold Networks (KAN).

This file is based on the original TVAE implementation from:
https://github.com/sdv-dev/CTGAN/blob/main/ctgan/synthesizers/tvae.py

Main Modifications (*):
- Replaced the Encoder and Decoder (originally MLP-based) with KAN-based architectures.
- Introduced new KAN-specific hyperparameters (e.g., grid size, spline order).
- Adjusted activation and reconstruction mechanisms to suit KAN layers.

All other logic, structure, and function docstrings have been retained from the original source,
unless explicitly noted otherwise. Any line or block marked with (*) indicates a user-introduced
modification to the original TVAE codebase.

For reference on TVAE:
Xu, L., Skoularidou, M., Cuesta-Infante, A., & Veeramachaneni, K. (2019).
Modeling Tabular data using Conditional GAN. NeurIPS 2019.
https://arxiv.org/abs/1907.00503
"""

import numpy as np
import pandas as pd
import torch
from ctgan.data_transformer import DataTransformer
from ctgan.synthesizers.base import BaseSynthesizer, random_state
from torch.nn import Module, Parameter, Sequential
from torch.nn.functional import cross_entropy
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

# (*) Additional import for Kolmogorov–Arnold Networks
from .KAN import KANLinear


# (*) KAN ENCODER
class KAN_Encoder(Module):
    """
    Encoder module for KAN-TVAE.

    This encoder replaces the standard MLP-based layers from the original TVAE
    with Kolmogorov–Arnold Network (KAN) components. It maps high-dimensional
    input data into a latent space represented by a mean and variance vector,
    using stacked KANLinear layers followed by two independent KAN output heads.

    Unlike the original MLP-based encoder, this version introduces flexible
    spline-based function approximators to capture complex nonlinear
    dependencies in tabular data.

    Args:
        data_dim (int): Dimensionality of the input data.
        compress_dims (list or tuple of int): Sizes of intermediate hidden layers in the encoder.
        embedding_dim (int): Size of the latent space vector (i.e., output dimensionality).
        grid_size (int): Number of grid points per input dimension in each KAN layer (default: 5).
        spline_order (int): Order of the spline interpolation used in KAN layers (default: 3).
        scale_noise (float): Standard deviation of noise applied to KAN spline components.
        scale_base (float): Scaling factor for the base component in KAN layers.
        scale_spline (float): Scaling factor for the spline component in KAN layers.
        base_activation (torch.nn.Module): Activation function used for the base component.
        grid_eps (float): Numerical stability epsilon for grid initialization.
        grid_range (list of float): Value range over which KAN grid points are distributed.
    """

    def __init__(
        self,
        data_dim,
        compress_dims,
        embedding_dim,
        grid_size=5,
        spline_order=3,
        scale_noise=0.1,
        scale_base=1.0,
        scale_spline=1.0,
        base_activation=torch.nn.SiLU,
        grid_eps=0.02,
        grid_range=[-1, 1],
    ):
        super(KAN_Encoder, self).__init__()

        # Single KAN with final output size = 2 * embedding_dim
        dim = data_dim
        seq = []
        for item in list(compress_dims):
            seq += [
                KANLinear(
                    dim,
                    item,
                    grid_size=grid_size,
                    spline_order=spline_order,
                    scale_noise=scale_noise,
                    scale_base=scale_base,
                    scale_spline=scale_spline,
                    base_activation=base_activation,
                    grid_eps=grid_eps,
                    grid_range=grid_range,
                )
            ]
            dim = item

        self.seq = Sequential(*seq)
        self.kan_fc1 = KANLinear(dim, embedding_dim)  # Optionally add KAN hyperparameters
        self.kan_fc2 = KANLinear(dim, embedding_dim)

    def forward(self, x):
        """Encode the passed input x."""
        # x: [batch, data_dim]
        feature = self.seq(x)  # [batch, 2*embedding_dim]
        # Splits the outpt into two equal parts along the feature dimension
        # Since out has shape [batch, 2*embedding_dim], the following code
        # will return a tuple of two tensors, each of shape [batch, embedding_dim]
        mu = self.kan_fc1(feature)
        logvar = self.kan_fc2(feature)
        std = torch.exp(0.5 * logvar)
        return mu, std, logvar


# (*) KAN DECODER
class KAN_Decoder(Module):
    """
    Decoder module for KAN-TVAE.

    This decoder reconstructs tabular data from latent representations using
    Kolmogorov–Arnold Network (KAN) components instead of standard MLPs.
    It maps a latent vector sampled from a Gaussian distribution to the
    original data space through a sequence of KANLinear layers, followed by
    a trainable output variance (sigma) parameter.

    Args:
        embedding_dim (int): Dimensionality of the latent representation (input to the decoder).
        decompress_dims (list or tuple of int): Sizes of hidden layers within the decoder.
        data_dim (int): Dimensionality of the output data (i.e., the number of columns in the transformed table).
        grid_size (int): Number of grid points per input dimension in each KAN layer (default: 5).
        spline_order (int): Order of the spline interpolation used in KAN layers (default: 3).
        scale_noise (float): Standard deviation of noise added to the spline component (default: 0.1).
        scale_base (float): Scaling factor for the base (linear) component of KAN layers.
        scale_spline (float): Scaling factor for the spline (nonlinear) component of KAN layers.
        base_activation (torch.nn.Module): Activation function used for the base (default: SiLU).
        grid_eps (float): Numerical offset to prevent overlapping grid boundaries (default: 0.02).
        grid_range (list of float): Value range over which grid points are distributed (default: [-1, 1]).
    """

    def __init__(
        self,
        embedding_dim,
        decompress_dims,
        data_dim,
        grid_size=5,
        spline_order=3,
        scale_noise=0.1,
        scale_base=1.0,
        scale_spline=1.0,
        base_activation=torch.nn.SiLU,
        grid_eps=0.02,
        grid_range=[-1, 1],
    ):
        super(KAN_Decoder, self).__init__()
        dim = embedding_dim
        seq = []
        for item in list(decompress_dims):
            seq += [
                KANLinear(
                    dim,
                    item,
                    grid_size=grid_size,
                    spline_order=spline_order,
                    scale_noise=scale_noise,
                    scale_base=scale_base,
                    scale_spline=scale_spline,
                    base_activation=base_activation,
                    grid_eps=grid_eps,
                    grid_range=grid_range,
                ),
                torch.nn.SiLU(),
            ]  # Use SiLU activation for KAN
            dim = item

        seq.append(KANLinear(dim, data_dim))
        self.seq = Sequential(*seq)
        self.sigma = Parameter(torch.ones(data_dim) * 0.1)

    def forward(self, z):
        """Decode the passed input z"""
        return self.seq(z), self.sigma


def _loss_function(recon_x, x, sigmas, mu, logvar, output_info, factor):
    st = 0
    loss = []
    for column_info in output_info:
        for span_info in column_info:
            if span_info.activation_fn != "softmax":
                ed = st + span_info.dim
                std = sigmas[st]
                eq = x[:, st] - torch.tanh(recon_x[:, st])
                loss.append((eq**2 / 2 / (std**2)).sum())
                loss.append(torch.log(std) * x.size()[0])
                st = ed

            else:
                ed = st + span_info.dim
                loss.append(
                    cross_entropy(
                        recon_x[:, st:ed], torch.argmax(x[:, st:ed], dim=-1), reduction="sum"
                    )
                )
                st = ed

    assert st == recon_x.size()[1]
    KLD = -0.5 * torch.sum(1 + logvar - mu**2 - logvar.exp())
    return sum(loss) * factor / x.size()[0], KLD / x.size()[0]


# (*) Main TVAE class override: uses KAN Encoder and Decoder
class KAN_TVAE(BaseSynthesizer):
    """
    Kolmogorov–Arnold Variational Autoencoder for Tabular Data (KAN-TVAE).

    This class implements a modified version of the original TVAE architecture
    (https://github.com/sdv-dev/CTGAN), where both the encoder and decoder—originally
    built with MLPs—are replaced by Kolmogorov–Arnold Networks (KANs) to capture
    richer nonlinear relationships in tabular data.

    The KAN-TVAE model follows the same training objective and structure as the original
    TVAE, including a Gaussian latent prior and a mixed output decoder that handles
    both continuous and categorical features. It uses spline-based KAN layers to map
    inputs to latent space and reconstruct samples during generation.

    Note:
        - The encoder replaces MLP layers with KANLinear layers and outputs (μ, logσ²).
        - The decoder replaces MLP layers with KANLinear layers and reconstructs inputs
          with a trainable per-feature standard deviation.
        - The loss combines a data reconstruction term and KL divergence.
        - The output is postprocessed with `tanh` or softmax, depending on the column type.

    Args:
        embedding_dim (int): Size of the latent space vector (default: 128).
        compress_dims (tuple of int): Hidden layer sizes for the encoder (default: (128, 128)).
        decompress_dims (tuple of int): Hidden layer sizes for the decoder (default: (128, 128)).
        grid_size_enc (int): Grid size for spline basis in KAN encoder layers (default: 5).
        spline_order_enc (int): Spline order in encoder (default: 3).
        grid_size_dec (int): Grid size for spline basis in KAN decoder layers (default: 5).
        spline_order_dec (int): Spline order in decoder (default: 5).
        l2scale (float): Weight decay (L2 regularization) used in Adam optimizer (default: 1e-5).
        batch_size (int): Number of samples per training batch (default: 500).
        epochs (int): Number of training epochs (default: 300).
        loss_factor (float): Weight of the reconstruction term in the loss (default: 2).
        cuda (bool or str): Whether to use GPU (True), CPU (False), or device name (e.g. 'cuda:0').
        verbose (bool): Whether to print progress during training (default: False).
    """

    def __init__(
        self,
        embedding_dim=128,
        compress_dims=(128, 128),
        decompress_dims=(128, 128),
        grid_size_enc=5,
        spline_order_enc=3,
        grid_size_dec=5,
        spline_order_dec=5,
        l2scale=1e-5,
        batch_size=500,
        epochs=300,
        loss_factor=2,
        cuda=True,
        verbose=False,
    ):
        self.embedding_dim = embedding_dim
        self.compress_dims = compress_dims
        self.decompress_dims = decompress_dims

        # (*) KAN HYPERPARAMETERS
        self.grid_size_enc = grid_size_enc
        self.spline_order_enc = spline_order_enc
        self.grid_size_dec = grid_size_dec
        self.spline_order_dec = spline_order_dec

        self.l2scale = l2scale
        self.batch_size = batch_size
        self.loss_factor = loss_factor
        self.epochs = epochs
        self.loss_values = pd.DataFrame(columns=["Epoch", "Batch", "Loss"])
        self.verbose = verbose

        if not cuda or not torch.cuda.is_available():
            device = "cpu"
        elif isinstance(cuda, str):
            device = cuda
        else:
            device = "cuda"

        self._device = torch.device(device)

    # (*) KAN_TVAE Fit
    @random_state
    def fit(self, train_data, discrete_columns=()):
        """Fit the KAN_TVAE Synthesizer models to the training data.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        self.transformer = DataTransformer()
        self.transformer.fit(train_data, discrete_columns)
        train_data = self.transformer.transform(train_data)
        dataset = TensorDataset(torch.from_numpy(train_data.astype("float32")).to(self._device))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, drop_last=False)

        data_dim = self.transformer.output_dimensions
        # (*) Use KAN_Encder and KAN_Decoder
        encoder = KAN_Encoder(data_dim, self.compress_dims, self.embedding_dim).to(self._device)
        self.decoder = KAN_Decoder(self.embedding_dim, self.decompress_dims, data_dim).to(
            self._device
        )
        optimizerAE = Adam(
            list(encoder.parameters()) + list(self.decoder.parameters()), weight_decay=self.l2scale
        )

        self.loss_values = pd.DataFrame(columns=["Epoch", "Batch", "Loss"])
        iterator = tqdm(range(self.epochs), disable=(not self.verbose))
        if self.verbose:
            iterator_description = "Loss: {loss:.3f}"
            iterator.set_description(iterator_description.format(loss=0))

        for i in iterator:
            loss_values = []
            batch = []
            for id_, data in enumerate(loader):
                optimizerAE.zero_grad()
                real = data[0].to(self._device)
                mu, std, logvar = encoder(real)
                eps = torch.randn_like(std)
                emb = eps * std + mu
                rec, sigmas = self.decoder(emb)
                loss_1, loss_2 = _loss_function(
                    rec,
                    real,
                    sigmas,
                    mu,
                    logvar,
                    self.transformer.output_info_list,
                    self.loss_factor,
                )
                loss = loss_1 + loss_2
                loss.backward()
                optimizerAE.step()
                self.decoder.sigma.data.clamp_(0.01, 1.0)

                batch.append(id_)
                loss_values.append(loss.detach().cpu().item())

            epoch_loss_df = pd.DataFrame(
                {
                    "Epoch": [i] * len(batch),
                    "Batch": batch,
                    "Loss": loss_values,
                }
            )
            if not self.loss_values.empty:
                self.loss_values = pd.concat([self.loss_values, epoch_loss_df]).reset_index(
                    drop=True
                )
            else:
                self.loss_values = epoch_loss_df

            if self.verbose:
                iterator.set_description(
                    iterator_description.format(loss=loss.detach().cpu().item())
                )

    @random_state
    def sample(self, samples):
        """Sample data similar to the training data.

        Args:
            samples (int):
                Number of rows to sample.

        Returns:
            numpy.ndarray or pandas.DataFrame
        """
        self.decoder.eval()

        steps = samples // self.batch_size + 1
        data = []
        for _ in range(steps):
            mean = torch.zeros(self.batch_size, self.embedding_dim)
            std = mean + 1
            noise = torch.normal(mean=mean, std=std).to(self._device)
            fake, sigmas = self.decoder(noise)
            fake = torch.tanh(fake)
            data.append(fake.detach().cpu().numpy())

        data = np.concatenate(data, axis=0)
        data = data[:samples]
        return self.transformer.inverse_transform(data, sigmas.detach().cpu().numpy())

    def set_device(self, device):
        """Set the `device` to be used ('GPU' or 'CPU)."""
        self._device = device
        self.decoder.to(self._device)
