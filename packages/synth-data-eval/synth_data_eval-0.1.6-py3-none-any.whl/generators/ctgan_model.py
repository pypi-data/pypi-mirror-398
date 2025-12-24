"""CTGAN model wrapper."""

from typing import List, Optional

import pandas as pd
from ctgan import CTGAN as _CTGAN

from .base_generator import BaseGenerator


class CTGANGenerator(BaseGenerator):
    """
    CTGAN (Conditional Tabular GAN) generator.

    Reference:
    Xu et al. "Modeling Tabular data using Conditional GAN" (NeurIPS 2019)
    """

    def __init__(
        self,
        epochs: int = 300,
        batch_size: int = 500,
        generator_dim: tuple = (256, 256),
        discriminator_dim: tuple = (256, 256),
        random_state: int = 42,
        verbose: bool = False,
    ):
        """
        Initialize CTGAN.

        Parameters
        ----------
        epochs : int
            Number of training epochs
        batch_size : int
            Batch size for training
        generator_dim : tuple
            Generator network dimensions
        discriminator_dim : tuple
            Discriminator network dimensions
        random_state : int
            Random seed
        verbose : bool
            Print training progress
        """
        super().__init__(name="CTGAN", random_state=random_state)

        self.epochs = epochs
        self.batch_size = batch_size
        self.verbose = verbose

        self.model = _CTGAN(
            epochs=epochs,
            batch_size=batch_size,
            generator_dim=generator_dim,
            discriminator_dim=discriminator_dim,
            verbose=verbose,
        )

        self.discrete_columns: List[str] = []

    def fit(self, data: pd.DataFrame, metadata: Optional[dict] = None):
        """
        Fit CTGAN to data.

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        metadata : dict, optional
            Must contain 'discrete_columns' key with list of categorical column names
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
