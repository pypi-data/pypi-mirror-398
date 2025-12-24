"""Gaussian Copula model wrapper."""

from typing import Optional

import pandas as pd
from sdv.metadata import SingleTableMetadata
from sdv.single_table import GaussianCopulaSynthesizer

from .base_generator import BaseGenerator


class GaussianCopulaGenerator(BaseGenerator):
    """
    Gaussian Copula generator from SDV.

    Fast parametric model that models correlations between variables.
    Good baseline for comparison with deep learning methods.
    """

    def __init__(self, default_distribution: str = "beta", random_state: int = 42):
        """
        Initialize Gaussian Copula.

        Parameters
        ----------
        default_distribution : str
            Default distribution for numerical columns
            Options: 'beta', 'gaussian', 'gamma', 'uniform'
        random_state : int
            Random seed
        """
        super().__init__(name="GaussianCopula", random_state=random_state)

        self.default_distribution = default_distribution
        self.model: GaussianCopulaSynthesizer
        self.metadata: SingleTableMetadata

    def fit(self, data: pd.DataFrame, metadata: Optional[dict] = None):
        """
        Fit Gaussian Copula to data.

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        metadata : dict, optional
            Dictionary with 'discrete_columns' key (ignored for GaussianCopula)
        """
        # Always create fresh metadata from data
        # GaussianCopula needs SingleTableMetadata object, not dict
        self.metadata = SingleTableMetadata()
        self.metadata.detect_from_dataframe(data)

        # Initialize and fit model
        self.model = GaussianCopulaSynthesizer(
            metadata=self.metadata, default_distribution=self.default_distribution
        )

        self.model.fit(data)
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

        return self.model.sample(num_rows=n_samples)
