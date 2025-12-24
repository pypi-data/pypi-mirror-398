"""TVAE model wrapper."""

from typing import List, Optional

import pandas as pd
from ctgan import TVAE as _TVAE

from .base_generator import BaseGenerator


class TVAEGenerator(BaseGenerator):
    """
    TVAE (Tabular Variational AutoEncoder) generator.

    Uses variational autoencoder architecture for tabular data synthesis.
    Generally faster than CTGAN but may produce lower quality samples.
    """

    def __init__(
        self,
        epochs: int = 300,
        batch_size: int = 500,
        compress_dims: tuple = (128, 128),
        decompress_dims: tuple = (128, 128),
        random_state: int = 42,
        verbose: bool = False,
    ):
        """
        Initialize TVAE.

        Parameters
        ----------
        epochs : int
            Number of training epochs
        batch_size : int
            Batch size for training
        compress_dims : tuple
            Encoder network dimensions
        decompress_dims : tuple
            Decoder network dimensions
        random_state : int
            Random seed
        verbose : bool
            Print training progress
        """
        super().__init__(name="TVAE", random_state=random_state)

        self.epochs = epochs
        self.batch_size = batch_size
        self.verbose = verbose

        self.model = _TVAE(
            epochs=epochs,
            batch_size=batch_size,
            compress_dims=compress_dims,
            decompress_dims=decompress_dims,
            verbose=verbose,
        )

        self.discrete_columns: List[str] = []

    def fit(self, data: pd.DataFrame, metadata: Optional[dict] = None):
        """
        Fit TVAE to data.

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        metadata : dict, optional
            Must contain 'discrete_columns' key with list of
            categorical column names
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
