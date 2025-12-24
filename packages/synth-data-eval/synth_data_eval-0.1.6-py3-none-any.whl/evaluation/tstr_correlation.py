"""TSTR correlation analysis module.

Analyzes how well quality metrics predict downstream ML utility (TSTR).
This identifies which metrics are "trustworthy proxies" for real utility.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class TSTRCorrelationAnalyzer:
    """
    Correlate quality metrics with TSTR performance.

    Key research question: Which metrics actually predict
    downstream task performance?
    """

    def __init__(self, correlation_method: str = "spearman"):
        """
        Initialize TSTR correlation analyzer.

        Parameters
        ----------
        correlation_method : str
            Correlation method: 'spearman' (default) or 'pearson'
            Spearman is preferred as it captures monotonic relationships
            even with non-linear scales
        """
        self.correlation_method = correlation_method

    def compute_metric_utility_correlation(
        self,
        metric_scores: pd.DataFrame,
        tstr_scores: pd.Series,
        min_samples: int = 5,
    ) -> pd.DataFrame:
        """
        Compute correlation between each metric and TSTR performance.

        Parameters
        ----------
        metric_scores : pd.DataFrame
            DataFrame where columns are different metrics
            (e.g., 'sdm_quality_score', 'privacy_dcr', etc.)
        tstr_scores : pd.Series
            TSTR utility scores (ground truth performance)
        min_samples : int
            Minimum number of samples required for correlation

        Returns
        -------
        pd.DataFrame
            Correlation results with columns:
            - metric: metric name
            - correlation: correlation coefficient
            - p_value: statistical significance
            - is_significant: whether p < 0.05
            - n_samples: number of valid data points
        """
        if len(metric_scores) != len(tstr_scores):
            raise ValueError(
                f"Metric scores ({len(metric_scores)}) and TSTR scores "
                f"({len(tstr_scores)}) must have same length"
            )

        logger.info(f"Computing {self.correlation_method} correlations with TSTR")
        logger.info(f"Number of experiments: {len(tstr_scores)}")

        results = []

        for metric_name in metric_scores.columns:
            try:
                # Extract valid data points (non-null, non-inf)
                valid_idx = (
                    ~metric_scores[metric_name].isna()
                    & ~tstr_scores.isna()
                    & np.isfinite(metric_scores[metric_name])
                    & np.isfinite(tstr_scores)
                )

                metric_vals = metric_scores.loc[valid_idx, metric_name]
                tstr_vals = tstr_scores.loc[valid_idx]

                if len(metric_vals) < min_samples:
                    logger.warning(
                        f"Metric '{metric_name}' has only {len(metric_vals)} valid samples "
                        f"(min: {min_samples}). Skipping."
                    )
                    continue

                # Compute correlation
                if self.correlation_method == "spearman":
                    corr, p_value = stats.spearmanr(metric_vals, tstr_vals)
                elif self.correlation_method == "pearson":
                    corr, p_value = stats.pearsonr(metric_vals, tstr_vals)
                else:
                    raise ValueError(f"Unknown method: {self.correlation_method}")

                results.append(
                    {
                        "metric": metric_name,
                        "correlation": float(corr) if not np.isnan(corr) else 0.0,
                        "p_value": float(p_value) if not np.isnan(p_value) else 1.0,
                        "is_significant": p_value < 0.05 if not np.isnan(p_value) else False,
                        "n_samples": len(metric_vals),
                    }
                )

            except Exception as e:
                logger.error(f"Failed to compute correlation for '{metric_name}': {e}")
                continue

        results_df = pd.DataFrame(results)

        # Sort by absolute correlation (strongest predictors first)
        if not results_df.empty:
            results_df["abs_correlation"] = results_df["correlation"].abs()
            results_df = results_df.sort_values("abs_correlation", ascending=False)
            results_df = results_df.drop(columns=["abs_correlation"])

        logger.info(f"Computed correlations for {len(results_df)} metrics")

        return results_df

    def rank_metrics_by_predictive_power(
        self, correlations_by_size: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Rank metrics by how well they predict TSTR across sample sizes.

        Parameters
        ----------
        correlations_by_size : dict
            Mapping of sample_size -> correlation DataFrame
            (output from compute_metric_utility_correlation)

        Returns
        -------
        pd.DataFrame
            Ranked metrics with columns:
            - metric: metric name
            - mean_abs_correlation: average absolute correlation across sizes
            - std_correlation: stability of correlation across sizes
            - n_significant: number of sample sizes where correlation is significant
            - sample_sizes: list of sizes where tested
        """
        logger.info("Ranking metrics by predictive power across sample sizes")

        # Collect correlations for each metric across all sizes
        metric_data: Dict[str, Dict[str, List]] = {}

        for sample_size, corr_df in correlations_by_size.items():
            for _, row in corr_df.iterrows():
                metric = row["metric"]

                if metric not in metric_data:
                    metric_data[metric] = {
                        "correlations": [],
                        "p_values": [],
                        "sample_sizes": [],
                    }

                metric_data[metric]["correlations"].append(row["correlation"])
                metric_data[metric]["p_values"].append(row["p_value"])
                metric_data[metric]["sample_sizes"].append(sample_size)

        # Compute ranking statistics
        ranking_data = []

        for metric, data in metric_data.items():
            correlations = np.array(data["correlations"])
            p_values = np.array(data["p_values"])

            ranking_data.append(
                {
                    "metric": metric,
                    "mean_abs_correlation": float(np.mean(np.abs(correlations))),
                    "std_correlation": float(np.std(correlations)),
                    "median_correlation": float(np.median(correlations)),
                    "n_significant": int(np.sum(np.array(p_values) < 0.05)),
                    "n_sample_sizes": len(data["sample_sizes"]),
                    "sample_sizes": data["sample_sizes"],
                }
            )

        ranking_df = pd.DataFrame(ranking_data)

        # Sort by mean absolute correlation (stronger predictors first)
        if not ranking_df.empty:
            ranking_df = ranking_df.sort_values("mean_abs_correlation", ascending=False)

        logger.info(f"Ranked {len(ranking_df)} metrics by predictive power")

        return ranking_df

    def identify_unreliable_metrics(
        self,
        correlations_by_size: Dict[int, pd.DataFrame],
        min_correlation: float = 0.3,
        max_variance: float = 0.5,
    ) -> List[str]:
        """
        Identify metrics that fail to predict TSTR or are unstable.

        A metric is unreliable if:
        1. Weak correlation with TSTR (abs(rho) < min_correlation)
        2. High variance in correlation across sample sizes

        Parameters
        ----------
        correlations_by_size : dict
            Mapping of sample_size -> correlation DataFrame
        min_correlation : float
            Minimum acceptable correlation magnitude
        max_variance : float
            Maximum acceptable variance in correlation

        Returns
        -------
        list of str
            Names of unreliable metrics
        """
        ranking = self.rank_metrics_by_predictive_power(correlations_by_size)

        unreliable = ranking[
            (ranking["mean_abs_correlation"] < min_correlation)
            | (ranking["std_correlation"] > max_variance)
        ]

        unreliable_list = unreliable["metric"].tolist()

        logger.info(f"Identified {len(unreliable_list)} unreliable metrics")
        for metric in unreliable_list:
            row = unreliable[unreliable["metric"] == metric].iloc[0]
            logger.info(
                f"  - {metric}: "
                f"mean_corr={row['mean_abs_correlation']:.3f}, "
                f"std={row['std_correlation']:.3f}"
            )

        return list(unreliable_list)

    def analyze_correlation_breakdown(
        self, correlations_by_size: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Identify metrics whose predictive power breaks down at small sample sizes.

        This is a core research finding: showing which metrics
        become unreliable in low-resource regimes.

        Parameters
        ----------
        correlations_by_size : dict
            Mapping of sample_size -> correlation DataFrame

        Returns
        -------
        pd.DataFrame
            Analysis showing:
            - metric: metric name
            - correlation_at_smallest: correlation at smallest sample size
            - correlation_at_largest: correlation at largest sample size
            - correlation_degradation: difference (smaller - larger)
            - breaks_down: True if correlation degrades by >0.3
        """
        sample_sizes = sorted(correlations_by_size.keys())
        smallest_size = sample_sizes[0]
        largest_size = sample_sizes[-1]

        logger.info(
            f"Analyzing correlation breakdown from {largest_size} to {smallest_size} samples"
        )

        # Get correlations at smallest and largest sizes
        small_df = correlations_by_size[smallest_size].set_index("metric")
        large_df = correlations_by_size[largest_size].set_index("metric")

        # Find common metrics
        common_metrics = small_df.index.intersection(large_df.index)

        breakdown_data = []

        for metric in common_metrics:
            corr_small = small_df.loc[metric, "correlation"]
            corr_large = large_df.loc[metric, "correlation"]

            degradation = abs(corr_small) - abs(corr_large)

            breakdown_data.append(
                {
                    "metric": metric,
                    "correlation_at_smallest": float(corr_small),
                    "correlation_at_largest": float(corr_large),
                    "abs_correlation_at_smallest": float(abs(corr_small)),
                    "abs_correlation_at_largest": float(abs(corr_large)),
                    "correlation_degradation": float(degradation),
                    "breaks_down": degradation < -0.3,  # Significant degradation
                }
            )

        breakdown_df = pd.DataFrame(breakdown_data)

        # Sort by degradation (worst degradation first)
        if not breakdown_df.empty:
            breakdown_df = breakdown_df.sort_values("correlation_degradation")

        # Log findings
        broken_metrics = breakdown_df[breakdown_df["breaks_down"]]
        if not broken_metrics.empty:
            logger.warning(f"Found {len(broken_metrics)} metrics with correlation breakdown:")
            for _, row in broken_metrics.iterrows():
                logger.warning(
                    f"  - {row['metric']}: "
                    f"{row['abs_correlation_at_largest']:.3f} → "
                    f"{row['abs_correlation_at_smallest']:.3f} "
                    f"(Δ = {row['correlation_degradation']:.3f})"
                )

        return breakdown_df

    def create_correlation_heatmap_data(
        self, correlations_by_size: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Create pivot table for heatmap visualization.

        Parameters
        ----------
        correlations_by_size : dict
            Mapping of sample_size -> correlation DataFrame

        Returns
        -------
        pd.DataFrame
            Pivot table with:
            - Rows: metrics
            - Columns: sample sizes
            - Values: correlations with TSTR
        """
        data_for_pivot = []

        for sample_size, corr_df in correlations_by_size.items():
            for _, row in corr_df.iterrows():
                data_for_pivot.append(
                    {
                        "metric": row["metric"],
                        "sample_size": sample_size,
                        "correlation": row["correlation"],
                    }
                )

        pivot_df = pd.DataFrame(data_for_pivot)
        heatmap_data = pivot_df.pivot(index="metric", columns="sample_size", values="correlation")

        # Sort by mean absolute correlation
        heatmap_data["mean_abs_corr"] = heatmap_data.abs().mean(axis=1)
        heatmap_data = heatmap_data.sort_values("mean_abs_corr", ascending=False)
        heatmap_data = heatmap_data.drop(columns=["mean_abs_corr"])

        return heatmap_data
