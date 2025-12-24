"""KAN-TVAE model wrapper."""

from typing import List, Optional

import pandas as pd

from .base_generator import BaseGenerator
from .KAN_TVAE import KAN_TVAE


class KAN_TVAE_Generator(BaseGenerator):
    """
    KAN-TVAE (Kolmogorov-Arnold Networks Tabular VAE) generator.

    Modified TVAE where the encoder and decoder use KAN layers
    instead of traditional MLPs for better expressiveness.

    Reference:
    Based on TVAE (Xu et al., NeurIPS 2019) with KAN modifications.
    """

    def __init__(
        self,
        epochs: int = 300,
        batch_size: int = 500,
        embedding_dim: int = 128,
        compress_dims: tuple = (128, 128),
        decompress_dims: tuple = (128, 128),
        l2scale: float = 1e-5,
        loss_factor: int = 2,
        grid_size_enc: int = 5,
        spline_order_enc: int = 3,
        grid_size_dec: int = 5,
        spline_order_dec: int = 3,
        random_state: int = 42,
        verbose: bool = False,
    ):
        """
        Initialize KAN-TVAE.

        Parameters
        ----------
        epochs : int
            Number of training epochs
        batch_size : int
            Batch size for training
        embedding_dim : int
            Dimension of latent space
        compress_dims : tuple
            Encoder hidden layer dimensions
        decompress_dims : tuple
            Decoder hidden layer dimensions
        l2scale : float
            L2 regularization scale
        loss_factor : float
            Loss scaling factor
        grid_size_enc : int
            Grid size for KAN encoder layers
        spline_order_enc : int
            Spline order for KAN encoder layers
        grid_size_dec : int
            Grid size for KAN decoder layers
        spline_order_dec : int
            Spline order for KAN decoder layers
        random_state : int
            Random seed
        verbose : bool
            Print training progress
        """
        super().__init__(name="KAN-TVAE", random_state=random_state)

        self.epochs = epochs
        self.batch_size = batch_size
        self.verbose = verbose

        self.model = KAN_TVAE(
            epochs=epochs,
            batch_size=batch_size,
            embedding_dim=embedding_dim,
            compress_dims=compress_dims,
            decompress_dims=decompress_dims,
            l2scale=l2scale,
            loss_factor=loss_factor,
            grid_size_enc=grid_size_enc,
            spline_order_enc=spline_order_enc,
            grid_size_dec=grid_size_dec,
            spline_order_dec=spline_order_dec,
        )

        self.discrete_columns: List[str] = []

    def fit(self, data: pd.DataFrame, metadata: Optional[dict] = None):
        """
        Fit KAN-TVAE to data.

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
