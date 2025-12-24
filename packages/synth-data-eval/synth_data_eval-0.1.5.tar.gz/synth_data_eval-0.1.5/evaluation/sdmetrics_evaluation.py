"""SDMetrics-based evaluation."""

import logging
from typing import Dict, Optional, Union

import numpy as np
import pandas as pd
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.single_table import (
    ContingencySimilarity,
    CorrelationSimilarity,
    KSComplement,
    TVComplement,
)
from sdv.metadata import SingleTableMetadata

logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("SDMETRICS_EVALUATION.PY VERSION 8 LOADED - FORCED UPDATE!!!")
logger.info("=" * 80)


class SDMetricsEvaluator:
    """Comprehensive evaluation using SDMetrics library."""

    def __init__(self, metadata: Optional[Union[dict, SingleTableMetadata]] = None):
        """
        Initialize evaluator.

        Parameters
        ----------
        metadata : dict or SingleTableMetadata, optional
            SDV metadata for the dataset
        """
        self.metadata = metadata
        self.results: Dict[str, float] = {}

    def evaluate_all(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        metadata: Optional[Union[dict, SingleTableMetadata]] = None,
    ) -> Dict[str, float]:
        """
        Run comprehensive evaluation.

        Parameters
        ----------
        real_data : pd.DataFrame
            Real training data
        synthetic_data : pd.DataFrame
            Generated synthetic data
        metadata : dict, optional
            Override metadata

        Returns
        -------
        dict
            Dictionary of metric scores
        """
        logger.info("Running SDMetrics evaluation...")
        logger.info("\n" + "#" * 80)
        logger.info("# SDMetricsEvaluator.evaluate_all() CALLED")
        logger.info("#" * 80)
        logger.info(f"# real_data shape: {real_data.shape}")
        logger.info(f"# synthetic_data shape: {synthetic_data.shape}")
        logger.info(f"# metadata type: {type(metadata)}")
        logger.info(f"# metadata value: {metadata}")
        logger.info("#" * 80 + "\n")

        results = {}

        # Overall Quality Report
        logger.info("# Calling _quality_report...")
        results.update(self._quality_report(real_data, synthetic_data, metadata))
        logger.info(f"# _quality_report returned: {len(results)} results")

        # Statistical Fidelity
        logger.info("# Calling _statistical_metrics...")
        results.update(self._statistical_metrics(real_data, synthetic_data))

        # Column-wise metrics
        logger.info("# Calling _column_metrics...")
        results.update(self._column_metrics(real_data, synthetic_data))

        self.results = results
        logger.info(f"# evaluate_all complete. Total results: {len(results)}")
        return results

    def _build_metadata_dict(
        self, real_data: pd.DataFrame, metadata: Optional[Union[dict, SingleTableMetadata]] = None
    ) -> dict:
        """
        Build metadata dict in the exact format SDMetrics expects.

        SDMetrics requires:
        {
            "columns": {
                "col1": {"sdtype": "numerical"},
                "col2": {"sdtype": "categorical"},
                ...
            }
        }
        """
        logger.info("DEBUG: _build_metadata_dict called")
        logger.info(f"DEBUG: metadata type: {type(metadata)}")
        logger.info(f"DEBUG: metadata value: {metadata}")

        # Start with empty columns dict
        columns = {}

        # Case 1: metadata is None or has 'discrete_columns' key
        if metadata is None or (isinstance(metadata, dict) and "discrete_columns" in metadata):
            discrete_cols = set()
            if isinstance(metadata, dict):
                discrete_cols = set(metadata.get("discrete_columns", []))

            logger.info(
                "DEBUG: Using discrete_columns approach. " f"discrete_cols: {discrete_cols}"
            )

            # Auto-detect column types
            for col in real_data.columns:
                if col in discrete_cols:
                    columns[col] = {"sdtype": "categorical"}
                elif pd.api.types.is_numeric_dtype(real_data[col]):
                    columns[col] = {"sdtype": "numerical"}
                else:
                    columns[col] = {"sdtype": "categorical"}

        # Case 2: metadata is SingleTableMetadata
        elif isinstance(metadata, SingleTableMetadata):
            logger.info("DEBUG: metadata is SingleTableMetadata")
            full_dict = metadata.to_dict()
            columns = full_dict.get("columns", {})

        # Case 3: metadata already has 'columns' key
        elif isinstance(metadata, dict) and "columns" in metadata:
            logger.info("DEBUG: metadata already has 'columns' key")
            columns = metadata["columns"]

        # Case 4: fallback - auto-detect
        else:
            logger.info("DEBUG: Using fallback auto-detect")
            for col in real_data.columns:
                if pd.api.types.is_numeric_dtype(real_data[col]):
                    columns[col] = {"sdtype": "numerical"}
                else:
                    columns[col] = {"sdtype": "categorical"}

        # Build the final metadata dict with explicit keys
        result = {"columns": columns}

        logger.info(f"DEBUG: Built metadata with {len(columns)} columns")
        logger.info(f"DEBUG: First 3 columns: {list(columns.keys())[:3]}")

        return result

    def _quality_report(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        metadata: Optional[Union[dict, SingleTableMetadata]] = None,
    ) -> Dict[str, float]:
        """Generate overall quality report."""
        logger.info("\n" + "=" * 80)
        logger.info("DEBUG: _quality_report STARTED")
        logger.info("=" * 80)

        try:
            meta_input = metadata or self.metadata
            logger.info(f"DEBUG: meta_input type: {type(meta_input)}")

            # Build metadata dict
            logger.info("DEBUG: About to call _build_metadata_dict...")
            sdmetrics_metadata = self._build_metadata_dict(real_data, meta_input)
            logger.info("DEBUG: Metadata built successfully")

            # Verify format
            if not isinstance(sdmetrics_metadata, dict):
                raise ValueError(f"Metadata must be dict, got {type(sdmetrics_metadata)}")

            if "columns" not in sdmetrics_metadata:
                raise ValueError(
                    "Metadata missing 'columns' key. "
                    f"Got keys: {list(sdmetrics_metadata.keys())}"
                )

            logger.info("DEBUG: Metadata has " f"{len(sdmetrics_metadata['columns'])} columns")
            logger.info(
                "DEBUG: Sample columns: " f"{list(sdmetrics_metadata['columns'].keys())[:3]}"
            )

            # Generate report
            logger.info("DEBUG: Creating QualityReport instance...")
            report = QualityReport()
            logger.info("DEBUG: Calling report.generate()...")
            report.generate(real_data, synthetic_data, sdmetrics_metadata)
            logger.info("DEBUG: report.generate() completed successfully!")

            properties_df = report.get_properties()
            properties_scores = properties_df.set_index("Property")["Score"]

            return {
                "quality_score": float(report.get_score() or 0.0),
                "column_shapes_score": properties_scores["Column Shapes"],
                "column_pair_trends_score": (properties_scores["Column Pair Trends"]),
            }
        except Exception as e:
            logger.warning(f"Quality report failed: {e}")
            import traceback

            logger.debug("\nFULL TRACEBACK:")
            logger.debug(traceback.format_exc())
            return {}

    def _statistical_metrics(
        self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Compute statistical similarity metrics."""
        results = {}

        # Kolmogorov-Smirnov Complement
        try:
            ks_scores = []
            for col in real_data.select_dtypes(include=[np.number]).columns:
                score = KSComplement.compute(
                    real_data=real_data[[col]],
                    synthetic_data=synthetic_data[[col]],
                )
                ks_scores.append(score)

            if ks_scores:
                results["ks_complement_mean"] = np.mean(ks_scores)
                results["ks_complement_std"] = np.std(ks_scores)
        except Exception as e:
            logger.warning(f"KS test failed: {e}")

        # Total Variation Distance
        try:
            tv_scores = []
            for col in real_data.select_dtypes(include=["object", "category"]).columns:
                score = TVComplement.compute(
                    real_data=real_data[[col]],
                    synthetic_data=synthetic_data[[col]],
                )
                tv_scores.append(score)

            if tv_scores:
                results["tv_complement_mean"] = np.mean(tv_scores)
        except Exception as e:
            logger.warning(f"TV distance failed: {e}")

        # Correlation Similarity
        try:
            # Filter out columns with constant values in real or synthetic data
            numeric_cols = real_data.select_dtypes(include=[np.number]).columns
            valid_cols = []

            for col in numeric_cols:
                real_unique = real_data[col].nunique()
                synth_unique = synthetic_data[col].nunique()

                if real_unique > 1 and synth_unique > 1:
                    valid_cols.append(col)
                else:
                    logger.debug(
                        "Skipping '%s' for correlation: " "real=%d, synth=%d",
                        col,
                        real_unique,
                        synth_unique,
                    )

            if len(valid_cols) >= 2:
                # Compute correlation on valid columns only
                real_filtered = real_data[valid_cols]
                synth_filtered = synthetic_data[valid_cols]

                corr_score = CorrelationSimilarity.compute(
                    real_data=real_filtered, synthetic_data=synth_filtered
                )
                results["correlation_similarity"] = corr_score
                logger.info("Correlation computed on %d columns", len(valid_cols))
            else:
                logger.warning(
                    "Correlation skipped: only %d valid columns " "(need ≥2)", len(valid_cols)
                )
        except Exception as e:
            logger.warning(f"Correlation similarity failed: {e}")

        # Contingency Similarity (for categorical pairs)
        try:
            cat_cols = real_data.select_dtypes(include=["object", "category"]).columns.tolist()
            if len(cat_cols) >= 2:
                cont_score = ContingencySimilarity.compute(
                    real_data=real_data, synthetic_data=synthetic_data
                )
                results["contingency_similarity"] = cont_score
        except Exception as e:
            logger.warning(f"Contingency similarity failed: {e}")

        return results

    def _column_metrics(
        self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Compute per-column quality metrics."""
        results = {}

        # Basic statistics comparison
        for col in real_data.columns:
            try:
                if pd.api.types.is_numeric_dtype(real_data[col]):
                    real_mean = real_data[col].mean()
                    synth_mean = synthetic_data[col].mean()
                    real_std = real_data[col].std()
                    synth_std = synthetic_data[col].std()

                    results[f"{col}_mean_diff"] = abs(real_mean - synth_mean) / (real_std + 1e-8)
                    results[f"{col}_std_ratio"] = synth_std / (real_std + 1e-8)
            except Exception as e:
                logger.warning(f"Column metric failed for {col}: {e}")

        return results

    def get_summary(self) -> pd.DataFrame:
        """Get summary of key metrics as DataFrame."""
        if not self.results:
            return pd.DataFrame()

        summary_metrics = {
            k: v
            for k, v in self.results.items()
            if not k.startswith("_") and isinstance(v, (int, float))
        }

        return pd.DataFrame([summary_metrics]).T.rename(columns={0: "Score"})
