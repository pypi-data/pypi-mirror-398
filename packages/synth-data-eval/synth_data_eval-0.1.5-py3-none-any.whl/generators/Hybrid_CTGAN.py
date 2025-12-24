"""
Hybrid_CTGAN_code.py

Modified CTGAN Implementation with a Hybrid Kolmogorov-Arnold Network (KAN) architecture.

This file is based on the original CTGAN implementation from:
https://github.com/sdv-dev/CTGAN/blob/main/ctgan/synthesizers/ctgan.py

Main Modifications:

* Replaced a single Residual block in the Generator with a KAN-based residual layer.
* Replaced one Linear block in the Discriminator with a KANLinear block.
* Added flexible control over the position of the KAN layer via kan_layer_idx.
* Introduced KAN-specific hyperparameters (e.g., grid size, spline order).
* Adjusted activation and normalization to align with KAN principles.

All other logic, structure, and function docstrings have been retained from the original source,
unless explicitly noted otherwise.

For reference on CTGAN:
Xu, L., Nightingale, A., and Krishnan, R. (2019). Modeling Tabular Data Using Conditional GAN.
https://arxiv.org/abs/1907.00503
"""

import warnings

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from ctgan.data_sampler import DataSampler
from ctgan.data_transformer import DataTransformer
from ctgan.errors import InvalidDataError
from ctgan.synthesizers.base import BaseSynthesizer, random_state
from torch import optim
from torch.nn import BatchNorm1d, Linear, Module, ReLU, Sequential, functional
from tqdm import tqdm

# (*) Additional import for Kolmogorov-Arnold Networks
from .KAN import KANLinear


class Residual(Module):
    """Residual layer for the CTGAN."""

    def __init__(self, i, o):
        super(Residual, self).__init__()
        self.fc = Linear(i, o)
        self.bn = BatchNorm1d(o)
        self.relu = ReLU()

    def forward(self, input_):
        """Apply the Residual layer to the `input_`."""
        out = self.fc(input_)
        out = self.bn(out)
        out = self.relu(out)
        return torch.cat([out, input_], dim=1)


# (*) New residual KAN layer used in the Generator
class ResidualKAN(Module):
    "KAN residual layer"

    def __init__(
        self,
        i,
        o,
        grid_size=5,
        spline_order=3,
        scale_noise=0.1,
        scale_base=1.0,
        scale_spline=1.0,
        base_activation=torch.nn.SiLU,
        grid_eps=0.02,
        grid_range=[-1, 1],
    ):
        super().__init__()
        self.kan = KANLinear(
            i,
            o,
            grid_size=grid_size,
            spline_order=spline_order,
            scale_noise=scale_noise,
            scale_base=scale_base,
            scale_spline=scale_spline,
            base_activation=base_activation,
            grid_eps=grid_eps,
            grid_range=grid_range,
        )
        self.bn = BatchNorm1d(o)
        self.act = (
            torch.nn.SiLU()
        )  # Different from CTGAN, Preserving suggestion from KAN original paper

    def forward(self, x):
        out = self.kan(x)
        out = self.bn(out)
        out = self.act(out)
        return torch.cat([out, x], dim=1)


# (*) Custom Hybrid Generator implementation using KAN layers
class HybridGenerator(Module):
    """
    Generator for Hybrid-CTGAN with one Kolmogorov-Arnold Network (KAN) layer.

    This generator modifies the original CTGAN architecture by introducing a single
    KAN-based residual block at a specified layer index (`kan_layer_idx`). All other
    layers remain standard residual blocks (Linear + BatchNorm + ReLU), as in the
    original CTGAN implementation.

    Args:
        embedding_dim (int): Dimension of the input noise vector (z) + conditional vector.
        generator_dim (list of int): List of hidden layer sizes, one per residual block.
        data_dim (int): Output dimension (number of features to synthesize).
        kan_layer_idx (int): Index at which to insert the KAN residual block (default: 0).
        grid_size (int): Number of grid intervals per feature (KAN-specific).
        spline_order (int): Degree of the spline basis (KAN-specific).
        scale_noise (float): Noise scaling factor for KAN (default: 0.1).
        scale_base (float): Base scaling factor for KAN (default: 1.0).
        scale_spline (float): Spline scaling factor for KAN (default: 1.0).
        base_activation (callable): Activation function to use (default: torch.nn.SiLU).
        grid_eps (float): Epsilon to avoid zero-width grid spacing.
        grid_range (list): Lower and upper bounds for the grid used in KAN.
    """

    def __init__(
        self,
        embedding_dim,
        generator_dim,
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
        super(HybridGenerator, self).__init__()
        layers = []
        dim = embedding_dim
        for i, item in enumerate(generator_dim):
            if i == kan_layer_idx:
                layers.append(
                    ResidualKAN(
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
                )
                dim += item
            else:
                layers.append(Residual(dim, item))
                dim += item
        layers.append(nn.Linear(dim, data_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        """
        Apply either the KANLinear or simple Residual.
        """
        return self.net(x)


# (*) Custom Hybrid Discriminator implementation using KAN layers
class HybridDiscriminator(Module):
    """
    Discriminator for Hybrid-CTGAN with one Kolmogorov-Arnold Network (KAN) layer.

    This discriminator modifies the CTGAN discriminator by inserting a single
    KANLinear layer at the specified index (`kan_layer_idx`). The rest of the
    layers remain standard Linear + LeakyReLU + Dropout blocks, preserving the
    original discriminator structure.

    The discriminator uses PACGAN-style grouping, multiplying the input dimension
    by `pac` to increase stability against mode collapse.

    Args:
        input_dim (int): Input feature dimension (after transformation).
        discriminator_dim (list of int): List of hidden layer sizes.
        pac (int): Number of samples grouped together for PACGAN (default: 10).
        kan_layer_idx (int): Index at which to insert the KANLinear layer.
        grid_size (int): Number of grid intervals per feature (KAN-specific).
        spline_order (int): Degree of the spline basis (KAN-specific).
        scale_noise (float): Noise scaling factor for KAN (default: 0.1).
        scale_base (float): Base scaling factor for KAN (default: 1.0).
        scale_spline (float): Spline scaling factor for KAN (default: 1.0).
        base_activation (callable): Activation function to use (default: torch.nn.SiLU).
        grid_eps (float): Epsilon to avoid zero-width grid spacing.
        grid_range (list): Lower and upper bounds for the grid used in KAN.
    """

    def __init__(
        self,
        input_dim,
        discriminator_dim,
        pac=10,
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
        super(HybridDiscriminator, self).__init__()
        # Compute the effective input dimension after applying the pac trick (as in the original CTGAN discriminator)
        dim = input_dim * pac
        self.pac = pac
        self.pacdim = dim
        layers = []

        for i, out_dim in enumerate(discriminator_dim):
            if i == kan_layer_idx:
                layers.append(
                    nn.Sequential(
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
                        nn.SiLU(0.2),  # Better for KAN
                        nn.Dropout(0.5),
                    )
                )
            else:
                layers.append(
                    nn.Sequential(nn.Linear(dim, out_dim), nn.LeakyReLU(0.2), nn.Dropout(0.5))
                )
            dim = out_dim

        # Final plain linear to a logit
        layers.append(nn.Linear(dim, 1))
        self.seq = nn.Sequential(*layers)

    # Calculate Gradient Penalty (Exact same as in the original implementation)
    def calc_gradient_penalty(self, real_data, fake_data, device="cpu", pac=10, lambda_=10):
        """Compute the gradient penalty."""
        alpha = torch.rand(real_data.size(0) // pac, 1, 1, device=device)
        alpha = alpha.repeat(1, pac, real_data.size(1))
        alpha = alpha.view(-1, real_data.size(1))

        interpolates = alpha * real_data + ((1 - alpha) * fake_data)

        disc_interpolates = self(interpolates)

        gradients = torch.autograd.grad(
            outputs=disc_interpolates,
            inputs=interpolates,
            grad_outputs=torch.ones(disc_interpolates.size(), device=device),
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0]

        gradients_view = gradients.view(-1, pac * real_data.size(1)).norm(2, dim=1) - 1
        gradient_penalty = ((gradients_view) ** 2).mean() * lambda_

        return gradient_penalty

    def forward(self, input_):
        """Apply the HybridDiscriminator to the `input_`."""
        assert input_.size()[0] % self.pac == 0
        return self.seq(input_.view(-1, self.pacdim))


# (*) Main CTGAN class override: uses Hybrid KAN Generator and Discriminator
class HYBRID_KAN_CTGAN(BaseSynthesizer):
    """
    Kolmogorov-Arnold Hybrid Conditional Table GAN (Hybrid KAN-CTGAN) Synthesizer.

    This class implements a hybrid variation of the original CTGAN architecture
    (https://github.com/sdv-dev/CTGAN), where only **one layer** in both the generator
    and discriminator—originally based on MLPs—has been replaced with Kolmogorov-Arnold
    Network (KAN) blocks.

    Except for these hybrid architectural substitutions, all logic and components from the
    original CTGAN implementation are preserved. For a complete description of the
    original model, refer to Xu, L., Nightingale, A., and Krishnan, R. (2019),
    "Modeling Tabular Data Using Conditional GAN", https://arxiv.org/abs/1907.00503

    Note:

        Only one hidden layer in the generator is replaced with a KANResidual block.
        Only one hidden layer in the discriminator is replaced with a KANLinear block.
        The specific KAN layer to substitute is chosen via kan_layer_idx.
        All other layers remain standard CTGAN (Residual + BatchNorm1d + ReLU in the generator;
        Linear + LeakyReLU + Dropout in the discriminator).
        Conditional sampling, gradient penalty, and activation logic follow the original CTGAN.

    Args:
        embedding_dim (int): Dimension of the input noise vector (default: 128).
        generator_dim (tuple of int): Hidden layer sizes in the generator (default: (256, 256)).
        discriminator_dim (tuple of int): Hidden layer sizes in the discriminator (default: (256, 256)).
        generator_lr (float): Learning rate for the generator optimizer (default: 2e-4).
        generator_decay (float): Weight decay for the generator optimizer (default: 1e-6).
        discriminator_lr (float): Learning rate for the discriminator optimizer (default: 2e-4).
        discriminator_decay (float): Weight decay for the discriminator optimizer (default: 1e-6).
        batch_size (int): Training batch size (default: 500).
        discriminator_steps (int): Number of discriminator updates per generator update (default: 1).
        log_frequency (bool): Whether to use log frequency in conditional sampling (default: True).
        verbose (bool): Whether to print training progress (default: False).
        epochs (int): Number of training epochs (default: 300).
        pac (int): Number of samples grouped for PACGAN (default: 10).
        cuda (bool or str): Use GPU if available, or specify device string (default: True).

        # KAN-specific hyperparameters:
        grid_size_gen (int): Grid size for the KAN generator layer (default: 5).
        spline_order_gen (int): Spline order for the KAN generator layer (default: 3).
        grid_size_desc (int): Grid size for the KAN discriminator layer (default: 5).
        spline_order_desc (int): Spline order for the KAN discriminator layer (default: 3).
    """

    # (*) Added KAN-specific hyperparameters
    def __init__(
        self,
        grid_size_gen=5,
        spline_order_gen=3,
        grid_size_desc=5,
        spline_order_desc=3,
        embedding_dim=128,
        generator_dim=(256, 256),
        discriminator_dim=(256, 256),
        generator_lr=2e-4,
        generator_decay=1e-6,
        discriminator_lr=2e-4,
        discriminator_decay=1e-6,
        batch_size=500,
        discriminator_steps=1,
        log_frequency=True,
        verbose=False,
        epochs=300,
        pac=10,
        cuda=True,
    ):
        assert batch_size % 2 == 0

        self._embedding_dim = embedding_dim
        self._generator_dim = generator_dim
        self._discriminator_dim = discriminator_dim

        # (*) KAN HYPERPARAMETERS
        self._grid_size_gen = grid_size_gen
        self._spline_order_gen = spline_order_gen
        self._grid_size_desc = grid_size_desc
        self._spline_order_desc = spline_order_desc

        self._generator_lr = generator_lr
        self._generator_decay = generator_decay
        self._discriminator_lr = discriminator_lr
        self._discriminator_decay = discriminator_decay

        self._batch_size = batch_size
        self._discriminator_steps = discriminator_steps
        self._log_frequency = log_frequency
        self._verbose = verbose
        self._epochs = epochs
        self.pac = pac

        if not cuda or not torch.cuda.is_available():
            device = "cpu"
        elif isinstance(cuda, str):
            device = cuda
        else:
            device = "cuda"

        self._device = torch.device(device)

        self._transformer = None
        self._data_sampler = None
        self._generator = None
        self.loss_values = None

    @staticmethod
    def _gumbel_softmax(logits, tau=1, hard=False, eps=1e-10, dim=-1):
        """Deals with the instability of the gumbel_softmax for older versions of torch.

        For more details about the issue:
        https://drive.google.com/file/d/1AA5wPfZ1kquaRtVruCd6BiYZGcDeNxyP/view?usp=sharing

        Args:
            logits […, num_features]:
                Unnormalized log probabilities
            tau:
                Non-negative scalar temperature
            hard (bool):
                If True, the returned samples will be discretized as one-hot vectors,
                but will be differentiated as if it is the soft sample in autograd
            dim (int):
                A dimension along which softmax will be computed. Default: -1.

        Returns:
            Sampled tensor of same shape as logits from the Gumbel-Softmax distribution.
        """
        for _ in range(10):
            transformed = functional.gumbel_softmax(logits, tau=tau, hard=hard, eps=eps, dim=dim)
            if not torch.isnan(transformed).any():
                return transformed

        raise ValueError("gumbel_softmax returning NaN.")

    def _apply_activate(self, data):
        """Apply proper activation function to the output of the generator."""
        data_t = []
        st = 0
        for column_info in self._transformer.output_info_list:
            for span_info in column_info:
                if span_info.activation_fn == "tanh":
                    ed = st + span_info.dim
                    data_t.append(torch.tanh(data[:, st:ed]))
                    st = ed
                elif span_info.activation_fn == "softmax":
                    ed = st + span_info.dim
                    transformed = self._gumbel_softmax(data[:, st:ed], tau=0.2)
                    data_t.append(transformed)
                    st = ed
                else:
                    raise ValueError(f"Unexpected activation function {span_info.activation_fn}.")

        return torch.cat(data_t, dim=1)

    def _cond_loss(self, data, c, m):
        """Compute the cross entropy loss on the fixed discrete column."""
        loss = []
        st = 0
        st_c = 0
        for column_info in self._transformer.output_info_list:
            for span_info in column_info:
                if len(column_info) != 1 or span_info.activation_fn != "softmax":
                    # not discrete column
                    st += span_info.dim
                else:
                    ed = st + span_info.dim
                    ed_c = st_c + span_info.dim
                    tmp = functional.cross_entropy(
                        data[:, st:ed], torch.argmax(c[:, st_c:ed_c], dim=1), reduction="none"
                    )
                    loss.append(tmp)
                    st = ed
                    st_c = ed_c

        loss = torch.stack(loss, dim=1)  # noqa: PD013

        return (loss * m).sum() / data.size()[0]

    def _validate_discrete_columns(self, train_data, discrete_columns):
        """Check whether ``discrete_columns`` exists in ``train_data``.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        if isinstance(train_data, pd.DataFrame):
            invalid_columns = set(discrete_columns) - set(train_data.columns)
        elif isinstance(train_data, np.ndarray):
            invalid_columns = []
            for column in discrete_columns:
                if column < 0 or column >= train_data.shape[1]:
                    invalid_columns.append(column)
        else:
            raise TypeError("``train_data`` should be either pd.DataFrame or np.array.")

        if invalid_columns:
            raise ValueError(f"Invalid columns found: {invalid_columns}")

    def _validate_null_data(self, train_data, discrete_columns):
        """Check whether null values exist in continuous ``train_data``.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        if isinstance(train_data, pd.DataFrame):
            continuous_cols = list(set(train_data.columns) - set(discrete_columns))
            any_nulls = train_data[continuous_cols].isna().any().any()
        else:
            continuous_cols = [i for i in range(train_data.shape[1]) if i not in discrete_columns]
            any_nulls = pd.DataFrame(train_data)[continuous_cols].isna().any().any()

        if any_nulls:
            raise InvalidDataError(
                "CTGAN does not support null values in the continuous training data. "
                "Please remove all null values from your continuous training data."
            )

    @random_state
    def fit(self, train_data, discrete_columns=(), epochs=None):
        """Fit the KAN_Hybrid_CTGAN Synthesizer models to the training data.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        self._validate_discrete_columns(train_data, discrete_columns)
        self._validate_null_data(train_data, discrete_columns)

        if epochs is None:
            epochs = self._epochs
        else:
            warnings.warn(
                (
                    "`epochs` argument in `fit` method has been deprecated and will be removed "
                    "in a future version. Please pass `epochs` to the constructor instead"
                ),
                DeprecationWarning,
            )

        self._transformer = DataTransformer()
        self._transformer.fit(train_data, discrete_columns)

        train_data = self._transformer.transform(train_data)

        self._data_sampler = DataSampler(
            train_data, self._transformer.output_info_list, self._log_frequency
        )

        data_dim = self._transformer.output_dimensions

        # (*) CHANGE GENERATOR AND DISCRIMINATOR
        self._generator = HybridGenerator(
            self._embedding_dim + self._data_sampler.dim_cond_vec(),
            self._generator_dim,
            data_dim,
            grid_size=self._grid_size_gen,
            spline_order=self._spline_order_gen,
        ).to(self._device)

        discriminator = HybridDiscriminator(
            data_dim + self._data_sampler.dim_cond_vec(),
            self._discriminator_dim,
            pac=self.pac,
            grid_size=self._grid_size_desc,
            spline_order=self._spline_order_desc,
        ).to(self._device)

        optimizerG = optim.Adam(
            self._generator.parameters(),
            lr=self._generator_lr,
            betas=(0.5, 0.9),
            weight_decay=self._generator_decay,
        )

        optimizerD = optim.Adam(
            discriminator.parameters(),
            lr=self._discriminator_lr,
            betas=(0.5, 0.9),
            weight_decay=self._discriminator_decay,
        )

        mean = torch.zeros(self._batch_size, self._embedding_dim, device=self._device)
        std = mean + 1

        self.loss_values = pd.DataFrame(columns=["Epoch", "Generator Loss", "Distriminator Loss"])

        epoch_iterator = tqdm(range(epochs), disable=(not self._verbose))
        if self._verbose:
            description = "Gen. ({gen:.2f}) | Discrim. ({dis:.2f})"
            epoch_iterator.set_description(description.format(gen=0, dis=0))

        steps_per_epoch = max(len(train_data) // self._batch_size, 1)
        for i in epoch_iterator:
            for id_ in range(steps_per_epoch):
                for n in range(self._discriminator_steps):
                    fakez = torch.normal(mean=mean, std=std)

                    condvec = self._data_sampler.sample_condvec(self._batch_size)
                    if condvec is None:
                        c1, m1, col, opt = None, None, None, None
                        real = self._data_sampler.sample_data(
                            train_data, self._batch_size, col, opt
                        )
                    else:
                        c1, m1, col, opt = condvec
                        c1 = torch.from_numpy(c1).to(self._device)
                        m1 = torch.from_numpy(m1).to(self._device)
                        fakez = torch.cat([fakez, c1], dim=1)

                        perm = np.arange(self._batch_size)
                        np.random.shuffle(perm)
                        real = self._data_sampler.sample_data(
                            train_data, self._batch_size, col[perm], opt[perm]
                        )
                        c2 = c1[perm]

                    fake = self._generator(fakez)
                    fakeact = self._apply_activate(fake)

                    real = torch.from_numpy(real.astype("float32")).to(self._device)

                    if c1 is not None:
                        fake_cat = torch.cat([fakeact, c1], dim=1)
                        real_cat = torch.cat([real, c2], dim=1)
                    else:
                        real_cat = real
                        fake_cat = fakeact

                    y_fake = discriminator(fake_cat)
                    y_real = discriminator(real_cat)

                    pen = discriminator.calc_gradient_penalty(
                        real_cat, fake_cat, self._device, self.pac
                    )
                    loss_d = -(torch.mean(y_real) - torch.mean(y_fake))

                    optimizerD.zero_grad(set_to_none=False)
                    pen.backward(retain_graph=True)
                    loss_d.backward()
                    optimizerD.step()

                fakez = torch.normal(mean=mean, std=std)
                condvec = self._data_sampler.sample_condvec(self._batch_size)

                if condvec is None:
                    c1, m1, col, opt = None, None, None, None
                else:
                    c1, m1, col, opt = condvec
                    c1 = torch.from_numpy(c1).to(self._device)
                    m1 = torch.from_numpy(m1).to(self._device)
                    fakez = torch.cat([fakez, c1], dim=1)

                fake = self._generator(fakez)
                fakeact = self._apply_activate(fake)

                if c1 is not None:
                    y_fake = discriminator(torch.cat([fakeact, c1], dim=1))
                else:
                    y_fake = discriminator(fakeact)

                if condvec is None:
                    cross_entropy = 0
                else:
                    cross_entropy = self._cond_loss(fake, c1, m1)

                loss_g = -torch.mean(y_fake) + cross_entropy

                optimizerG.zero_grad(set_to_none=False)
                loss_g.backward()
                optimizerG.step()

            generator_loss = loss_g.detach().cpu().item()
            discriminator_loss = loss_d.detach().cpu().item()

            epoch_loss_df = pd.DataFrame(
                {
                    "Epoch": [i],
                    "Generator Loss": [generator_loss],
                    "Discriminator Loss": [discriminator_loss],
                }
            )
            if not self.loss_values.empty:
                self.loss_values = pd.concat([self.loss_values, epoch_loss_df]).reset_index(
                    drop=True
                )
            else:
                self.loss_values = epoch_loss_df

            if self._verbose:
                epoch_iterator.set_description(
                    description.format(gen=generator_loss, dis=discriminator_loss)
                )

    @random_state
    def sample(self, n, condition_column=None, condition_value=None):
        """Sample data similar to the training data.

        Choosing a condition_column and condition_value will increase the probability of the
        discrete condition_value happening in the condition_column.

        Args:
            n (int):
                Number of rows to sample.
            condition_column (string):
                Name of a discrete column.
            condition_value (string):
                Name of the category in the condition_column which we wish to increase the
                probability of happening.

        Returns:
            numpy.ndarray or pandas.DataFrame
        """
        if condition_column is not None and condition_value is not None:
            condition_info = self._transformer.convert_column_name_value_to_id(
                condition_column, condition_value
            )
            global_condition_vec = self._data_sampler.generate_cond_from_condition_column_info(
                condition_info, self._batch_size
            )
        else:
            global_condition_vec = None

        steps = n // self._batch_size + 1
        data = []
        for i in range(steps):
            mean = torch.zeros(self._batch_size, self._embedding_dim)
            std = mean + 1
            fakez = torch.normal(mean=mean, std=std).to(self._device)

            if global_condition_vec is not None:
                condvec = global_condition_vec.copy()
            else:
                condvec = self._data_sampler.sample_original_condvec(self._batch_size)

            if condvec is None:
                pass
            else:
                c1 = condvec
                c1 = torch.from_numpy(c1).to(self._device)
                fakez = torch.cat([fakez, c1], dim=1)

            fake = self._generator(fakez)
            fakeact = self._apply_activate(fake)
            data.append(fakeact.detach().cpu().numpy())

        data = np.concatenate(data, axis=0)
        data = data[:n]

        return self._transformer.inverse_transform(data)

    def set_device(self, device):
        """Set the `device` to be used ('GPU' or 'CPU)."""
        self._device = device
        if self._generator is not None:
            self._generator.to(self._device)
