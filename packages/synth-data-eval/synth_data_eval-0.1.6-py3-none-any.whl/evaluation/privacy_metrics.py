"""Privacy evaluation metrics - Memory optimized."""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class PrivacyEvaluator:
    """
    Evaluate privacy risks in synthetic data - Memory optimized.

    Implements:
    - Distance to Closest Record (DCR)
    - Nearest Neighbor Distance Ratio (NNDR)
    - Attribute Disclosure
    """

    def __init__(self, max_samples: int = 5000):
        """
        Initialize evaluator.

        Parameters
        ----------
        max_samples : int
            Maximum samples to use for distance computations (memory limit)
        """
        self.max_samples = max_samples
        self.results: Dict[str, float] = {}

    def evaluate(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        sensitive_columns: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Run privacy evaluation.

        Parameters
        ----------
        real_data : pd.DataFrame
            Real training data
        synthetic_data : pd.DataFrame
            Generated synthetic data
        sensitive_columns : list, optional
            List of sensitive attribute columns

        Returns
        -------
        dict
            Dictionary of privacy metrics
        """
        logger.info("Running Privacy evaluation...")

        # Sample data if too large
        if len(real_data) > self.max_samples:
            logger.info(f"Sampling real data: {len(real_data)} -> {self.max_samples}")
            real_data = real_data.sample(n=self.max_samples, random_state=42)

        if len(synthetic_data) > self.max_samples:
            logger.info(f"Sampling synthetic data: {len(synthetic_data)} -> {self.max_samples}")
            synthetic_data = synthetic_data.sample(n=self.max_samples, random_state=42)

        # Prepare numerical data
        real_num, synth_num = self._prepare_numerical_data(real_data, synthetic_data)

        results = {}

        # Distance to Closest Record (DCR)
        results["dcr"] = self._compute_dcr(real_num, synth_num)

        # Nearest Neighbor Distance Ratio (NNDR)
        results["nndr"] = self._compute_nndr(real_num, synth_num)

        # Privacy Loss Score (5th percentile of DCR)
        results["privacy_loss"] = self._compute_privacy_loss(real_num, synth_num)

        # Attribute Disclosure (if sensitive columns specified)
        if sensitive_columns:
            results["attribute_disclosure"] = self._compute_attribute_disclosure(
                real_data, synthetic_data, sensitive_columns
            )

        self.results = results
        return results

    def _prepare_numerical_data(
        self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert to numerical arrays and normalize."""
        # Select numerical columns
        numerical_cols = real_data.select_dtypes(include=[np.number]).columns

        if len(numerical_cols) == 0:
            raise ValueError("No numerical columns found for privacy evaluation")

        real_num = real_data[numerical_cols].values
        synth_num = synthetic_data[numerical_cols].values

        # Normalize
        scaler = StandardScaler()
        real_num = scaler.fit_transform(real_num)
        synth_num = scaler.transform(synth_num)

        return real_num, synth_num

    def _compute_dcr(self, real_data: np.ndarray, synthetic_data: np.ndarray) -> float:
        """
        Compute Distance to Closest Record (batched for memory efficiency).

        Measures minimum distance from each synthetic record to real records.
        Higher is better (more privacy).
        """
        batch_size = 1000
        min_distances: List[float] = []

        # Process in batches to avoid memory issues
        for i in range(0, len(synthetic_data), batch_size):
            batch = synthetic_data[i : i + batch_size]
            distances = cdist(batch, real_data, metric="euclidean")
            min_distances.extend(distances.min(axis=1))

        min_distances_array = np.array(min_distances)
        dcr = float(np.mean(min_distances_array))

        logger.info(f"DCR: {dcr:.4f} (mean), {np.median(min_distances_array):.4f} (median)")

        return dcr

    def _compute_nndr(self, real_data: np.ndarray, synthetic_data: np.ndarray) -> float:
        """
        Compute Nearest Neighbor Distance Ratio (batched).

        Ratio of distances: synthetic-to-real vs real-to-real.
        Value close to 1 indicates similar privacy as original data.
        """
        batch_size = 1000

        # Synthetic to nearest real (batched)
        min_dists_synth = []
        for i in range(0, len(synthetic_data), batch_size):
            batch = synthetic_data[i : i + batch_size]
            distances = cdist(batch, real_data, metric="euclidean")
            min_dists_synth.extend(distances.min(axis=1))

        min_dist_synth = np.mean(min_dists_synth)

        # Real to nearest other real
        nn = NearestNeighbors(n_neighbors=2)
        nn.fit(real_data)
        distances_real, _ = nn.kneighbors(real_data)
        min_dist_real = distances_real[:, 1].mean()

        nndr = min_dist_synth / (min_dist_real + 1e-8)

        logger.info(f"NNDR: {nndr:.4f}")

        return float(nndr)

    def _compute_privacy_loss(
        self, real_data: np.ndarray, synthetic_data: np.ndarray, percentile: int = 5
    ) -> float:
        """
        Compute privacy loss score (batched).

        5th percentile of DCR - identifies worst-case privacy violations.
        Lower values indicate higher privacy risk.
        """
        batch_size = 1000
        min_distances: List[float] = []

        for i in range(0, len(synthetic_data), batch_size):
            batch = synthetic_data[i : i + batch_size]
            distances = cdist(batch, real_data, metric="euclidean")
            min_distances.extend(distances.min(axis=1))

        min_distances_array = np.array(min_distances)
        privacy_loss = float(np.percentile(min_distances_array, percentile))

        logger.info(f"Privacy Loss ({percentile}th percentile): {privacy_loss:.4f}")

        return privacy_loss

    def _compute_attribute_disclosure(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        sensitive_columns: list,
        sample_size: int = 1000,
    ) -> float:
        """
        Compute attribute disclosure risk (sampled for efficiency).

        Measures how often sensitive attributes can be correctly inferred
        from synthetic data by matching to real data.
        """
        # Sample for efficiency
        if len(synthetic_data) > sample_size:
            synthetic_sample = synthetic_data.sample(n=sample_size, random_state=42)
        else:
            synthetic_sample = synthetic_data

        # Find nearest real record for each synthetic record
        real_num, synth_num = self._prepare_numerical_data(real_data, synthetic_sample)

        distances = cdist(synth_num, real_num, metric="euclidean")
        nearest_indices = distances.argmin(axis=1)

        # Check if sensitive attributes match
        disclosure_count = 0
        total_count = 0

        for i, nearest_idx in enumerate(nearest_indices):
            for col in sensitive_columns:
                if col in real_data.columns and col in synthetic_sample.columns:
                    real_val = real_data.iloc[nearest_idx][col]
                    synth_val = synthetic_sample.iloc[i][col]
                    if pd.notna(real_val) and pd.notna(synth_val) and real_val == synth_val:
                        disclosure_count += 1
                    total_count += 1

        disclosure_rate = disclosure_count / (total_count + 1e-8)

        logger.info(f"Attribute Disclosure Rate: {disclosure_rate:.4f}")

        return float(disclosure_rate)

    def get_summary(self) -> pd.DataFrame:
        """Get summary of privacy metrics."""
        if not self.results:
            return pd.DataFrame()

        return pd.DataFrame([self.results]).T.rename(columns={0: "Score"})
