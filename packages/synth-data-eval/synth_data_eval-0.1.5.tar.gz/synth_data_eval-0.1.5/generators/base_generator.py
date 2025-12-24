"""Base class for all synthetic data generators."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """Abstract base class for synthetic data generators."""

    def __init__(self, name: str, random_state: int = 42):
        """
        Initialize generator.

        Parameters
        ----------
        name : str
            Generator name for identification
        random_state : int
            Random seed for reproducibility
        """
        self.name = name
        self.random_state = random_state
        self.is_fitted = False
        self.training_time: Optional[float] = None
        self.generation_time: Optional[float] = None

    @abstractmethod
    def fit(self, data: pd.DataFrame, metadata: Optional[dict] = None):
        """
        Fit the generator to training data.

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        metadata : dict, optional
            Column metadata (types, constraints)
        """
        pass

    @abstractmethod
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
        pass

    def fit_generate(
        self, data: pd.DataFrame, n_samples: int, metadata: Optional[dict] = None
    ) -> pd.DataFrame:
        """
        Fit and generate in one call.

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        n_samples : int
            Number of synthetic samples
        metadata : dict, optional
            Column metadata

        Returns
        -------
        pd.DataFrame
            Synthetic data
        """
        start_time = time.time()
        self.fit(data, metadata)
        self.training_time = time.time() - start_time

        start_time = time.time()
        synthetic = self.generate(n_samples)
        self.generation_time = time.time() - start_time

        logger.info(
            f"{self.name} - Training: {self.training_time:.2f}s, "
            f"Generation: {self.generation_time:.2f}s"
        )

        return synthetic

    def get_metadata(self) -> dict:
        """Get generator metadata and performance stats."""
        return {
            "name": self.name,
            "training_time": self.training_time,
            "generation_time": self.generation_time,
            "is_fitted": self.is_fitted,
        }
