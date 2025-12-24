"""
Hybrid_TVAE_Code.py

Hybrid TVAE Implementation with Partial Kolmogorov–Arnold Networks (KAN).

This file is based on the original TVAE implementation from:
https://github.com/sdv-dev/CTGAN/blob/main/ctgan/synthesizers/tvae.py

Main Modifications (*):
- Replaced one layer in the Encoder and Decoder (originally MLP-based) with KANLinear layers.
- Introduced the ability to specify the position (`kan_layer_idx`) of the KAN block in both modules.
- Maintained full compatibility with TVAE’s VAE loss (reconstruction + KL divergence).
- Added support for KAN-specific hyperparameters such as grid size, spline order, and scaling factors.

This hybrid approach allows experimentation with partially KAN-based architectures,
which may offer a trade-off between representational power and training stability.

All other logic, structure, and function docstrings have been retained from the original source,
unless explicitly noted otherwise. Any line or block marked with (*) indicates a user-introduced
modification to the original TVAE codebase.

For reference on TVAE:
Xu, L., Skoularidou, M., Cuesta-Infante, A., & Veeramachaneni, K. (2019).
Modeling Tabular Data using Conditional GAN. NeurIPS 2019.
https://arxiv.org/abs/1907.00503
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from ctgan.data_transformer import DataTransformer
from ctgan.synthesizers.base import BaseSynthesizer, random_state
from torch.nn import Linear, Module, Parameter, ReLU, Sequential
from torch.nn.functional import cross_entropy
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

# (*) Additional import for Kolmogorov–Arnold Networks
from .KAN import KANLinear


# (*) Hybrid KAN ENCODER
class HybridEncoder(Module):
    """
    Encoder module for Hybrid-KAN-TVAE.

    This encoder introduces a hybrid architecture that combines standard MLP-based
    layers with a single Kolmogorov–Arnold Network (KAN) block at a configurable
    position (`kan_layer_idx`). The rest of the layers remain unchanged from the
    original TVAE encoder.

    The encoder maps input tabular data into a latent space characterized by its
    mean and log-variance vectors. Only one of the intermediate layers is replaced
    with a spline-based KANLinear layer, which enables localized nonlinear
    approximation with grid-based flexibility.

    This approach allows for partial integration of KAN components while retaining
    much of the simplicity and speed of the original MLP-based design.

    Args:
        data_dim (int): Dimensionality of the input data.
        compress_dims (list or tuple of int): Sizes of the intermediate hidden layers.
        embedding_dim (int): Dimensionality of the latent representation.
        kan_layer_idx (int): Index of the encoder layer to be replaced with a KANLinear block.
        grid_size (int): Number of grid points per input dimension in the KAN layer (default: 5).
        spline_order (int): Order of the spline interpolation used in the KAN layer (default: 3).
        scale_noise (float): Standard deviation of noise applied to the KAN spline component.
        scale_base (float): Scaling factor for the base component in the KAN layer.
        scale_spline (float): Scaling factor for the spline component in the KAN layer.
        base_activation (torch.nn.Module): Activation function used for the KAN base component.
        grid_eps (float): Small epsilon added for numerical stability during grid setup.
        grid_range (list of float): Value range over which the KAN grid points are distributed.
    """

    def __init__(
        self,
        data_dim,
        compress_dims,
        embedding_dim,
        kan_layer_idx=0,
        grid_size=5,
        spline_order=3,
        scale_noise=0.1,
        scale_base=1.0,
        scale_spline=1.0,
        base_activation=torch.nn.SiLU,
        grid_eps=0.02,
        grid_range=[-1, 1],
    ):
        super(HybridEncoder, self).__init__()
        self.kan_layer_idx = kan_layer_idx

        # Swapping KAN layer when needed
        layers = []
        dim = data_dim
        for i, out_dim in enumerate(compress_dims):
            if i == kan_layer_idx:
                layers += [
                    KANLinear(
                        dim,
                        out_dim,
                        grid_size=grid_size,
                        spline_order=spline_order,
                        scale_noise=scale_noise,
                        scale_base=scale_base,
                        scale_spline=scale_spline,
                        base_activation=base_activation,
                        grid_eps=grid_eps,
                        grid_range=grid_range,
                    ),
                    nn.SiLU(),
                ]
            else:
                layers += [Linear(dim, out_dim), ReLU()]
            dim = out_dim

        self.seq = Sequential(*layers)
        # Final VAE heads unchanged
        self.fc_mu = Linear(dim, embedding_dim)
        self.fc_logvar = Linear(dim, embedding_dim)

    def forward(self, x):
        """Encode the passed input x."""
        h = self.seq(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        std = torch.exp(0.5 * logvar)
        return mu, std, logvar


# (*) Hybrid KAN DECODER
class HybridDecoder(Module):
    """
    Decoder module for Hybrid-KAN-TVAE.

    This decoder combines standard MLP-based layers with a single Kolmogorov–Arnold
    Network (KAN) block at a configurable position (`kan_layer_idx`). All other layers
    remain consistent with the original TVAE decoder architecture.

    The decoder reconstructs tabular data from latent representations by projecting
    from the embedding space back into the original data domain. Incorporating a single
    KAN layer allows for the introduction of localized nonlinearities via spline-based
    approximations, without fully replacing the lightweight structure of MLP layers.

    This hybrid approach is useful for testing how partial KAN integration affects
    reconstruction quality and downstream sample fidelity.

    Args:
        embedding_dim (int): Dimensionality of the latent space input.
        decompress_dims (list or tuple of int): Sizes of the intermediate hidden layers in the decoder.
        data_dim (int): Number of features in the reconstructed data (i.e., output dimensionality).
        kan_layer_idx (int): Index of the decoder layer to be replaced with a KANLinear block.
        grid_size (int): Number of grid points per input dimension in the KAN layer (default: 5).
        spline_order (int): Order of the spline interpolation used in the KAN layer (default: 3).
        scale_noise (float): Standard deviation of noise applied to the KAN spline component.
        scale_base (float): Scaling factor for the base component in the KAN layer.
        scale_spline (float): Scaling factor for the spline component in the KAN layer.
        base_activation (torch.nn.Module): Activation function used for the KAN base component.
        grid_eps (float): Small epsilon added for numerical stability during grid setup.
        grid_range (list of float): Value range over which the KAN grid points are distributed.
    """

    def __init__(
        self,
        embedding_dim,
        decompress_dims,
        data_dim,
        kan_layer_idx=0,
        grid_size=5,
        spline_order=3,
        scale_noise=0.1,
        scale_base=1.0,
        scale_spline=1.0,
        base_activation=torch.nn.SiLU,
        grid_eps=0.02,
        grid_range=[-1, 1],
    ):
        super(HybridDecoder, self).__init__()
        self.kan_layer_idx = kan_layer_idx
        # Swapping KAN layer when needed
        layers = []
        dim = embedding_dim
        for i, out_dim in enumerate(decompress_dims):
            if i == kan_layer_idx:
                layers += [
                    KANLinear(
                        dim,
                        out_dim,
                        grid_size=grid_size,
                        spline_order=spline_order,
                        scale_noise=scale_noise,
                        scale_base=scale_base,
                        scale_spline=scale_spline,
                        base_activation=base_activation,
                        grid_eps=grid_eps,
                        grid_range=grid_range,
                    ),
                    nn.SiLU(),
                ]
            else:
                layers += [Linear(dim, out_dim), ReLU()]
            dim = out_dim

        # Final projection to data_dim
        layers.append(Linear(dim, data_dim))

        self.seq = Sequential(*layers)
        self.sigma = Parameter(torch.ones(data_dim) * 0.1)

    def forward(self, z):
        """Decode the passed input z"""
        x_recon = self.seq(z)
        return x_recon, self.sigma


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


# (*) Main TVAE class override: uses Hybrid KAN Generator and Discriminator
class HYBRID_KAN_TVAE(BaseSynthesizer):
    """
    Hybrid Kolmogorov–Arnold Variational Autoencoder for Tabular Data (Hybrid-KAN-TVAE).

    This class implements a hybrid version of the TVAE architecture
    (https://github.com/sdv-dev/CTGAN), where one layer in both the encoder and decoder
    is replaced with a Kolmogorov–Arnold Network (KAN) layer. All other layers remain
    standard MLP components, as in the original implementation.

    The purpose of this hybrid model is to investigate whether inserting a single
    nonlinear spline-based KAN block can enhance the representational power of
    TVAE while maintaining computational efficiency and architectural familiarity.

    The training objective, latent prior (Gaussian), and data generation strategy
    follow the original TVAE formulation. The decoder outputs both a reconstruction
    and a learned standard deviation for each continuous variable, and the loss
    combines reconstruction error with Kullback-Leibler divergence.

    Note:
        - The encoder consists of MLP layers with a single KAN layer inserted at a configurable index.
        - The decoder follows the same hybrid structure, combining MLPs with one KAN block.
        - Only one KAN block is introduced per component (encoder/decoder) for controlled experimentation.
        - Uses tanh or softmax postprocessing depending on the feature type in output reconstruction.
        - Designed to evaluate the contribution of KANs in low-intrusion settings.

    Args:
        embedding_dim (int): Size of the latent space vector (default: 128).
        compress_dims (tuple of int): Hidden layer sizes for the encoder (default: (128, 128)).
        decompress_dims (tuple of int): Hidden layer sizes for the decoder (default: (128, 128)).
        grid_size_enc (int): Grid size for the spline basis in the encoder KAN layer (default: 5).
        spline_order_enc (int): Spline order used in the encoder KAN (default: 3).
        grid_size_dec (int): Grid size for the spline basis in the decoder KAN layer (default: 5).
        spline_order_dec (int): Spline order used in the decoder KAN (default: 5).
        l2scale (float): Weight decay (L2 regularization) used in the Adam optimizer (default: 1e-5).
        batch_size (int): Number of samples per training batch (default: 500).
        epochs (int): Number of training epochs (default: 300).
        loss_factor (float): Weight of the reconstruction term in the loss (default: 2).
        cuda (bool or str): Whether to use GPU (True), CPU (False), or specify device name (e.g., 'cuda:0').
        verbose (bool): Whether to print training progress (default: False).
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

    @random_state
    def fit(self, train_data, discrete_columns=()):
        """Fit the HYBRID_KAN_TVAE Synthesizer models to the training data.

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
        # (*) Use HybridEncder and HybridDecoder
        encoder = HybridEncoder(data_dim, self.compress_dims, self.embedding_dim).to(self._device)
        self.decoder = HybridDecoder(self.embedding_dim, self.decompress_dims, data_dim).to(
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
