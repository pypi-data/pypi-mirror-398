"""KAN-CTGAN model wrapper."""

from typing import List, Optional

import pandas as pd

from .base_generator import BaseGenerator
from .KAN_CTGAN import KAN_CTGAN


class KAN_CTGAN_Generator(BaseGenerator):
    """
    KAN-CTGAN (Kolmogorov-Arnold Networks Conditional Tabular GAN) generator.

    Modified CTGAN where generator and discriminator use KAN layers
    instead of traditional MLPs for better expressiveness.

    Reference:
    Based on CTGAN (Xu et al., NeurIPS 2019) with KAN modifications.
    """

    def __init__(
        self,
        epochs: int = 300,
        batch_size: int = 500,
        embedding_dim: int = 128,
        generator_dim: tuple = (256, 256),
        discriminator_dim: tuple = (256, 256),
        generator_lr: float = 2e-4,
        generator_decay: float = 1e-6,
        discriminator_lr: float = 2e-4,
        discriminator_decay: float = 1e-6,
        discriminator_steps: int = 1,
        log_frequency: bool = True,
        pac: int = 10,
        grid_size_gen: int = 5,
        spline_order_gen: int = 3,
        grid_size_desc: int = 5,
        spline_order_desc: int = 3,
        random_state: int = 42,
        verbose: bool = False,
    ):
        """
        Initialize KAN-CTGAN.

        Parameters
        ----------
        epochs : int
            Number of training epochs
        batch_size : int
            Batch size for training
        embedding_dim : int
            Dimension of noise vector
        generator_dim : tuple
            Generator hidden layer dimensions
        discriminator_dim : tuple
            Discriminator hidden layer dimensions
        generator_lr : float
            Generator learning rate
        generator_decay : float
            Generator weight decay
        discriminator_lr : float
            Discriminator learning rate
        discriminator_decay : float
            Discriminator weight decay
        discriminator_steps : int
            Discriminator updates per generator update
        log_frequency : bool
            Use log frequency for conditional sampling
        pac : int
            PACGAN grouping size
        grid_size_gen : int
            Grid size for KAN generator layers
        spline_order_gen : int
            Spline order for KAN generator layers
        grid_size_desc : int
            Grid size for KAN discriminator layers
        spline_order_desc : int
            Spline order for KAN discriminator layers
        random_state : int
            Random seed
        verbose : bool
            Print training progress
        """
        super().__init__(name="KAN-CTGAN", random_state=random_state)

        self.epochs = epochs
        self.batch_size = batch_size
        self.verbose = verbose

        self.model = KAN_CTGAN(
            epochs=epochs,
            batch_size=batch_size,
            embedding_dim=embedding_dim,
            generator_dim=generator_dim,
            discriminator_dim=discriminator_dim,
            generator_lr=generator_lr,
            generator_decay=generator_decay,
            discriminator_lr=discriminator_lr,
            discriminator_decay=discriminator_decay,
            discriminator_steps=discriminator_steps,
            log_frequency=log_frequency,
            verbose=verbose,
            pac=pac,
            grid_size_gen=grid_size_gen,
            spline_order_gen=spline_order_gen,
            grid_size_desc=grid_size_desc,
            spline_order_desc=spline_order_desc,
        )

        self.discrete_columns: List[str] = []

    def fit(self, data: pd.DataFrame, metadata: Optional[dict] = None):
        """
        Fit KAN-CTGAN to data.

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        metadata : dict, optional
            Must contain 'discrete_columns' key with list of categorical
            column names
        """
        # Identify discrete columns
        if metadata and "discrete_columns" in metadata:
            self.discrete_columns = metadata["discrete_columns"]
        else:
            # Auto-detect categorical columns
            self.discrete_columns = [
                col
                for col in data.columns
                if data[col].dtype == "object" or data[col].nunique() < 20
            ]

        self.model.fit(data, discrete_columns=self.discrete_columns)
        self.is_fitted = True

    def generate(self, n_samples: int) -> pd.DataFrame:
        """
        Generate synthetic samples.

        Parameters
        ----------
        n_samples : int
            Number of samples to generate

        Returns
        -------
        pd.DataFrame
            Synthetic data
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before generating")

        return self.model.sample(n_samples)
