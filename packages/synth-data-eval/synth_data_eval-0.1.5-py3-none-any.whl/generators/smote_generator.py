"""SMOTE-based synthetic data generator.

Simple statistical baseline for comparison with complex GAN models.
Tests whether "simpler is better" for small datasets.
"""

import logging
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SMOTEGenerator:
    """
    SMOTE (Synthetic Minority Oversampling Technique) generator.

    This serves as a simple statistical baseline to contrast with
    complex deep learning generators (CTGAN, TVAE).

    Note: SMOTE is designed for classification tasks with class imbalance.
    For regression or balanced datasets, it may not be appropriate.
    """

    def __init__(
        self,
        k_neighbors: int = 5,
        sampling_strategy: str = "auto",
        random_state: int = 42,
    ):
        """
        Initialize SMOTE generator.

        Parameters
        ----------
        k_neighbors : int
            Number of nearest neighbors for SMOTE
        sampling_strategy : str
            Sampling strategy: 'auto', 'minority', 'not majority', 'all'
        random_state : int
            Random seed
        """
        self.k_neighbors = k_neighbors
        self.sampling_strategy = sampling_strategy
        self.random_state = random_state
        self.training_time = 0.0
        self.generation_time = 0.0
        self._fitted = False
        self._target_col: Optional[str] = None
        self._feature_cols: Optional[List[str]] = None
        self._smote_model = None

    def fit_generate(
        self,
        data: pd.DataFrame,
        n_samples: int,
        metadata: Optional[Dict] = None,
    ) -> pd.DataFrame:
        """
        Fit SMOTE and generate synthetic data.

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        n_samples : int
            Number of synthetic samples to generate
        metadata : dict, optional
            Metadata including 'discrete_columns' and 'target_column'

        Returns
        -------
        pd.DataFrame
            Synthetic data
        """
        logger.info("SMOTE Generator: Starting fit and generation")
        start_time = time.time()

        # Lazy import to avoid dependency issues
        try:
            from imblearn.over_sampling import SMOTE
        except ImportError:
            raise ImportError(
                "imbalanced-learn is required for SMOTE. "
                "Install with: pip install imbalanced-learn"
            )

        # Determine target column
        if metadata and "target_column" in metadata:
            target_col = metadata["target_column"]
        else:
            # Assume last column is target (common convention)
            target_col = data.columns[-1]
            logger.warning(f"No target column specified. Assuming last column: {target_col}")

        self._target_col = target_col
        self._feature_cols = [col for col in data.columns if col != target_col]

        # Prepare data
        X = data[self._feature_cols].copy()
        y = data[target_col].copy()

        # Handle categorical features (SMOTE requires numerical input)
        from sklearn.preprocessing import LabelEncoder

        encoders = {}
        categorical_cols: List[str] = []  # Initialize as typed list
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                encoders[col] = LabelEncoder()
                X[col] = encoders[col].fit_transform(X[col].astype(str))
                categorical_cols.append(col)  # Track categorical columns

        # Encode target - but remember the original dtype
        original_target_dtype = y.dtype
        target_encoder = LabelEncoder()
        y_encoded = target_encoder.fit_transform(y.astype(str))

        # Calculate sampling strategy to reach desired n_samples
        class_counts = pd.Series(y_encoded).value_counts()
        max_class_count = class_counts.max()

        # Determine how many samples per class to reach n_samples
        n_classes = len(class_counts)
        target_per_class = n_samples // n_classes

        if target_per_class < max_class_count:
            logger.warning(
                f"Requested {n_samples} samples, but majority class has "
                f"{max_class_count} samples. SMOTE will not undersample. "
                "Generating samples to match majority class."
            )
            sampling_dict = {cls: max_class_count for cls in class_counts.index}
        else:
            sampling_dict = {cls: target_per_class for cls in class_counts.index}

        # Adjust k_neighbors if needed
        min_class_count = class_counts.min()
        k_neighbors = min(self.k_neighbors, min_class_count - 1)
        if k_neighbors < 1:
            logger.error(
                f"Smallest class has only {min_class_count} samples. "
                "Cannot run SMOTE (need at least 2)."
            )
            # Return original data
            self.training_time = time.time() - start_time
            self.generation_time = 0.0
            return data.copy()

        fit_start = time.time()

        # Apply SMOTE
        try:
            smote = SMOTE(
                sampling_strategy=sampling_dict,
                k_neighbors=k_neighbors,
                random_state=self.random_state,
            )
            X_resampled, y_resampled = smote.fit_resample(X, y_encoded)
        except Exception as e:
            logger.error(f"SMOTE failed: {e}")
            logger.info("Returning original data as fallback")
            self.training_time = time.time() - start_time
            self.generation_time = 0.0
            return data.copy()

        self.training_time = time.time() - fit_start

        gen_start = time.time()

        # Decode categorical features
        X_decoded = pd.DataFrame(X_resampled, columns=self._feature_cols)
        for col, encoder in encoders.items():
            # Clip to valid range
            X_decoded[col] = X_decoded[col].round().astype(int)
            X_decoded[col] = X_decoded[col].clip(0, len(encoder.classes_) - 1)
            X_decoded[col] = encoder.inverse_transform(X_decoded[col])

        # Decode target and preserve original dtype
        y_decoded = target_encoder.inverse_transform(y_resampled)

        # Convert back to original dtype (critical for ML evaluation!)
        if pd.api.types.is_numeric_dtype(original_target_dtype):
            # Convert string back to numeric
            y_decoded = pd.to_numeric(y_decoded)
            # Preserve exact original dtype (int32, int64, float64, etc.)
            y_decoded = y_decoded.astype(original_target_dtype)

        # Combine into DataFrame
        synthetic_df = X_decoded.copy()
        synthetic_df[target_col] = y_decoded

        # Sample to exact size if needed
        if len(synthetic_df) > n_samples:
            synthetic_df = synthetic_df.sample(n=n_samples, random_state=self.random_state)
        elif len(synthetic_df) < n_samples:
            # Oversample if not enough
            additional_samples = n_samples - len(synthetic_df)
            extra = synthetic_df.sample(
                n=additional_samples, replace=True, random_state=self.random_state
            )
            synthetic_df = pd.concat([synthetic_df, extra], ignore_index=True)

        self.generation_time = time.time() - gen_start
        total_time = time.time() - start_time

        logger.info(
            f"SMOTE completed: {len(synthetic_df)} samples in {total_time:.2f}s "
            f"(fit: {self.training_time:.2f}s, gen: {self.generation_time:.2f}s)"
        )

        self._fitted = True
        return synthetic_df

    def fit(self, data: pd.DataFrame, metadata: Optional[Dict] = None):
        """
        Fit the generator (SMOTE doesn't have separate fit/generate).

        Parameters
        ----------
        data : pd.DataFrame
            Training data
        metadata : dict, optional
            Metadata
        """
        logger.warning("SMOTE does not have separate fit/generate. Use fit_generate().")
        self._fitted = True

    def generate(self, n_samples: int) -> pd.DataFrame:
        """
        Generate synthetic data (SMOTE doesn't support separate generation).

        Parameters
        ----------
        n_samples : int
            Number of samples

        Returns
        -------
        pd.DataFrame
            Placeholder (use fit_generate instead)
        """
        logger.error("SMOTE does not support separate generation. Use fit_generate().")
        raise NotImplementedError("SMOTE requires fit_generate(), not separate generate()")
