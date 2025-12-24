"""Progressive sampling module for meta-evaluation experiments.

This module creates stratified samples at multiple scales (logarithmic)
to enable analysis of metric stability across data scarcity regimes.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class ProgressiveSampler:
    """
    Generate multiple sample sizes from a dataset for meta-evaluation.

    This class enables systematic testing of synthetic data generators
    and metrics across data scarcity regimes (100 to 50k samples).
    """

    def __init__(
        self,
        sample_sizes: Optional[List[int]] = None,
        random_state: int = 42,
    ):
        """
        Initialize progressive sampler.

        Parameters
        ----------
        sample_sizes : list of int, optional
            Sample sizes to generate. Defaults to logarithmic scale:
            [100, 500, 1000, 5000, 10000, 50000]
        random_state : int
            Random seed for reproducibility
        """
        self.sample_sizes = sample_sizes or [100, 500, 1000, 5000, 10000, 50000]
        self.random_state = random_state

    def create_samples(
        self,
        data: pd.DataFrame,
        target_col: str,
        n_repeats: int = 5,
        stratify: bool = True,
        task_type: str = "classification",
    ) -> Dict[int, List[pd.DataFrame]]:
        """
        Create multiple samples at different sizes.

        Parameters
        ----------
        data : pd.DataFrame
            Full dataset to sample from
        target_col : str
            Name of target column for stratification
        n_repeats : int
            Number of independent samples per size (for variance estimation)
        stratify : bool
            Whether to use stratified sampling (preserves class distribution)
        task_type : str
            'classification' or 'regression'

        Returns
        -------
        dict
            Mapping of sample_size -> [df_run1, df_run2, ...]

        Example
        -------
        >>> sampler = ProgressiveSampler(sample_sizes=[100, 500])
        >>> samples = sampler.create_samples(df, target_col='label', n_repeats=3)
        >>> samples[100]  # List of 3 DataFrames, each with 100 rows
        """
        logger.info(f"Creating progressive samples from dataset with {len(data)} rows")
        logger.info(f"Sample sizes: {self.sample_sizes}")
        logger.info(f"Repeats per size: {n_repeats}")

        results = {}

        # Validate sample sizes
        valid_sizes = [size for size in self.sample_sizes if size <= len(data)]
        if len(valid_sizes) < len(self.sample_sizes):
            skipped = set(self.sample_sizes) - set(valid_sizes)
            logger.warning(f"Skipping sample sizes {skipped} (exceed dataset size {len(data)})")
        self.sample_sizes = valid_sizes

        # Generate samples
        for sample_size in self.sample_sizes:
            logger.info(f"Generating {n_repeats} samples of size {sample_size}")
            samples = []

            for repeat_id in range(n_repeats):
                try:
                    sample_df = self._create_single_sample(
                        data=data,
                        target_col=target_col,
                        sample_size=sample_size,
                        stratify=stratify and task_type == "classification",
                        seed=self.random_state + repeat_id,
                    )
                    samples.append(sample_df)
                except Exception as e:
                    logger.error(
                        f"Failed to create sample (size={sample_size}, " f"repeat={repeat_id}): {e}"
                    )
                    continue

            if samples:
                results[sample_size] = samples
                logger.info(f"Created {len(samples)} samples of size {sample_size}")
            else:
                logger.warning(f"No valid samples created for size {sample_size}")

        return results

    def _create_single_sample(
        self,
        data: pd.DataFrame,
        target_col: str,
        sample_size: int,
        stratify: bool,
        seed: int,
    ) -> pd.DataFrame:
        """
        Create a single stratified sample.

        Parameters
        ----------
        data : pd.DataFrame
            Full dataset
        target_col : str
            Target column name
        sample_size : int
            Number of samples to draw
        stratify : bool
            Whether to stratify by target
        seed : int
            Random seed

        Returns
        -------
        pd.DataFrame
            Sampled dataset
        """
        if sample_size >= len(data):
            logger.warning(
                f"Sample size {sample_size} >= data size {len(data)}. " "Returning full dataset."
            )
            return data.copy()

        # Check if stratification is feasible
        if stratify:
            class_counts = data[target_col].value_counts()
            min_class_count = class_counts.min()

            # Need at least 2 samples per class for meaningful stratification
            if min_class_count < 2:
                logger.warning(
                    f"Minimum class count ({min_class_count}) too small. "
                    "Falling back to random sampling."
                )
                stratify = False
            elif sample_size / len(class_counts) < 2:
                logger.warning(
                    f"Sample size {sample_size} too small for {len(class_counts)} classes. "
                    "Falling back to random sampling."
                )
                stratify = False

        # Perform sampling
        if stratify:
            try:
                sample_df = data.groupby(target_col, group_keys=False).apply(
                    lambda x: x.sample(
                        frac=sample_size / len(data),
                        random_state=seed,
                        replace=False,
                    )
                )
                # Ensure exact sample size
                if len(sample_df) != sample_size:
                    sample_df = sample_df.sample(n=sample_size, random_state=seed, replace=False)
            except Exception as e:
                logger.warning(f"Stratified sampling failed: {e}. Using random sampling.")
                sample_df = data.sample(n=sample_size, random_state=seed, replace=False)
        else:
            sample_df = data.sample(n=sample_size, random_state=seed, replace=False)

        # Validate class representation for classification
        if stratify:
            original_classes = set(data[target_col].unique())
            sample_classes = set(sample_df[target_col].unique())
            if sample_classes != original_classes:
                logger.warning(f"Sample is missing classes: {original_classes - sample_classes}")

        return sample_df.reset_index(drop=True)

    def create_train_test_split(
        self,
        data: pd.DataFrame,
        target_col: str,
        test_size: float = 0.2,
        task_type: str = "classification",
    ) -> Dict[int, List[Tuple[pd.DataFrame, pd.DataFrame]]]:
        """
        Create progressive samples with train/test splits.

        Parameters
        ----------
        data : pd.DataFrame
            Full dataset
        target_col : str
            Target column name
        test_size : float
            Fraction for test set
        task_type : str
            'classification' or 'regression'

        Returns
        -------
        dict
            Mapping of sample_size -> [(train1, test1), (train2, test2), ...]
        """
        logger.info("Creating progressive samples with train/test splits")

        # First create full samples
        samples_by_size = self.create_samples(
            data=data,
            target_col=target_col,
            stratify=task_type == "classification",
            task_type=task_type,
        )

        # Then split each sample
        results = {}
        for sample_size, samples in samples_by_size.items():
            splits = []
            for idx, sample_df in enumerate(samples):
                try:
                    if task_type == "classification":
                        stratify_col = sample_df[target_col]
                    else:
                        stratify_col = None

                    train_df, test_df = train_test_split(
                        sample_df,
                        test_size=test_size,
                        random_state=self.random_state + idx,
                        stratify=stratify_col,
                    )
                    splits.append((train_df, test_df))
                except Exception as e:
                    logger.error(f"Failed to split sample (size={sample_size}, idx={idx}): {e}")
                    continue

            results[sample_size] = splits

        return results

    def get_summary_statistics(
        self, samples_by_size: Dict[int, List[pd.DataFrame]], target_col: str
    ) -> pd.DataFrame:
        """
        Get summary statistics for generated samples.

        Parameters
        ----------
        samples_by_size : dict
            Output from create_samples()
        target_col : str
            Target column name

        Returns
        -------
        pd.DataFrame
            Summary statistics per sample size
        """
        summary_data = []

        for sample_size, samples in samples_by_size.items():
            for idx, sample_df in enumerate(samples):
                stats = {
                    "sample_size": sample_size,
                    "repeat_id": idx,
                    "n_rows": len(sample_df),
                    "n_cols": len(sample_df.columns),
                    "n_classes": sample_df[target_col].nunique(),
                }

                # Class distribution
                class_counts = sample_df[target_col].value_counts()
                stats["min_class_count"] = class_counts.min()
                stats["max_class_count"] = class_counts.max()
                stats["class_imbalance_ratio"] = class_counts.max() / class_counts.min()

                summary_data.append(stats)

        return pd.DataFrame(summary_data)
