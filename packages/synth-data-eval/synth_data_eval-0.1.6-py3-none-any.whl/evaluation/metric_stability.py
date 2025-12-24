"""Metric stability analysis module.

Core contribution: Measure the reliability of evaluation metrics themselves
across different data scarcity regimes.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class MetricStabilityAnalyzer:
    """
    Analyze stability and reliability of evaluation metrics.

    This is the core novelty of the meta-evaluation framework:
    instead of just measuring synthetic data quality, we measure
    the *reliability* of the quality metrics themselves.
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize stability analyzer.

        Parameters
        ----------
        confidence_level : float
            Confidence level for intervals (default 95%)
        """
        self.confidence_level = confidence_level

    def compute_stability_metrics(
        self, metric_values: List[float], metric_name: str
    ) -> Dict[str, float]:
        """
        Compute stability statistics for a single metric.

        Parameters
        ----------
        metric_values : list of float
            Values of a metric across multiple runs
        metric_name : str
            Name of the metric

        Returns
        -------
        dict
            Stability statistics including:
            - mean, std, cv (coefficient of variation)
            - 95% confidence interval
            - inter-quartile range (IQR)
            - min, max
        """
        if not metric_values or len(metric_values) < 2:
            logger.warning(f"Insufficient data for {metric_name}: {len(metric_values)} values")
            return self._get_default_stability_metrics()

        values = np.array(metric_values)
        values = values[~np.isnan(values)]  # Remove NaNs

        if len(values) < 2:
            logger.warning(f"Insufficient valid data for {metric_name} after removing NaNs")
            return self._get_default_stability_metrics()

        mean = np.mean(values)
        std = np.std(values, ddof=1)

        # Coefficient of variation (relative variability)
        # High CV = unstable metric
        if abs(mean) > 1e-8:
            cv = std / abs(mean)
        else:
            cv = float("inf") if std > 0 else 0.0

        # Confidence interval
        sem = stats.sem(values)
        ci_margin = sem * stats.t.ppf((1 + self.confidence_level) / 2, len(values) - 1)

        # Inter-quartile range
        q25, q75 = np.percentile(values, [25, 75])
        iqr = q75 - q25

        return {
            "mean": float(mean),
            "std": float(std),
            "cv": float(cv),
            "sem": float(sem),
            "ci_lower": float(mean - ci_margin),
            "ci_upper": float(mean + ci_margin),
            "ci_margin": float(ci_margin),
            "iqr": float(iqr),
            "q25": float(q25),
            "q75": float(q75),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "n_samples": len(values),
        }

    def compare_sample_sizes(
        self, results_by_size: Dict[int, List[Dict[str, float]]], metric_name: str
    ) -> pd.DataFrame:
        """
        Compare metric variance across sample sizes.

        Statistical test: Does metric variance differ significantly
        across data scarcity regimes?

        Parameters
        ----------
        results_by_size : dict
            Mapping of sample_size -> [results_run1, results_run2, ...]
        metric_name : str
            Name of metric to analyze

        Returns
        -------
        pd.DataFrame
            Statistical comparison including:
            - Stability metrics per sample size
            - Levene's test for variance homogeneity
            - ANOVA for mean differences
        """
        logger.info(f"Comparing metric '{metric_name}' across sample sizes")

        comparison_data = []
        values_by_size = {}

        # Extract metric values per sample size
        for sample_size, runs in results_by_size.items():
            values = []
            for run_result in runs:
                if metric_name in run_result and run_result[metric_name] is not None:
                    values.append(run_result[metric_name])

            if values:
                values_by_size[sample_size] = values
                stability = self.compute_stability_metrics(values, metric_name)
                stability["sample_size"] = sample_size
                comparison_data.append(stability)

        comparison_df = pd.DataFrame(comparison_data)

        # Run statistical tests if we have multiple sample sizes
        if len(values_by_size) >= 2:
            # Levene's test for homogeneity of variances
            groups = list(values_by_size.values())
            try:
                levene_stat, levene_p = stats.levene(*groups)
                logger.info(
                    f"Levene's test for {metric_name}: "
                    f"statistic={levene_stat:.4f}, p={levene_p:.4f}"
                )
                comparison_df.attrs["levene_statistic"] = levene_stat
                comparison_df.attrs["levene_p_value"] = levene_p
            except Exception as e:
                logger.warning(f"Levene's test failed: {e}")

            # ANOVA for mean differences
            try:
                f_stat, anova_p = stats.f_oneway(*groups)
                logger.info(f"ANOVA for {metric_name}: " f"F={f_stat:.4f}, p={anova_p:.4f}")
                comparison_df.attrs["anova_f_statistic"] = f_stat
                comparison_df.attrs["anova_p_value"] = anova_p
            except Exception as e:
                logger.warning(f"ANOVA failed: {e}")

        return comparison_df

    def bootstrap_metric_distribution(
        self,
        metric_values: List[float],
        n_bootstrap: int = 1000,
        statistic: str = "mean",
    ) -> Dict[str, float]:
        """
        Bootstrap resampling to estimate metric reliability.

        Parameters
        ----------
        metric_values : list of float
            Observed metric values
        n_bootstrap : int
            Number of bootstrap iterations
        statistic : str
            Statistic to bootstrap ('mean', 'std', 'median')

        Returns
        -------
        dict
            Bootstrap confidence intervals and distribution stats
        """
        if not metric_values or len(metric_values) < 2:
            return self._get_default_bootstrap_results()

        values = np.array(metric_values)
        values = values[~np.isnan(values)]

        if len(values) < 2:
            return self._get_default_bootstrap_results()

        # Select statistic function
        if statistic == "mean":
            stat_func = np.mean
        elif statistic == "std":
            stat_func = lambda x: np.std(x, ddof=1)
        elif statistic == "median":
            stat_func = np.median
        else:
            raise ValueError(f"Unknown statistic: {statistic}")

        # Bootstrap resampling
        bootstrap_stats = []
        rng = np.random.RandomState(42)

        for _ in range(n_bootstrap):
            sample = rng.choice(values, size=len(values), replace=True)
            bootstrap_stats.append(stat_func(sample))

        bootstrap_stats = np.array(bootstrap_stats)

        # Compute confidence intervals
        alpha = 1 - self.confidence_level
        ci_lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
        ci_upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

        return {
            "bootstrap_mean": float(np.mean(bootstrap_stats)),
            "bootstrap_std": float(np.std(bootstrap_stats)),
            "bootstrap_ci_lower": float(ci_lower),
            "bootstrap_ci_upper": float(ci_upper),
            "original_statistic": float(stat_func(values)),
            "n_bootstrap": n_bootstrap,
        }

    def identify_unstable_metrics(
        self,
        stability_results: pd.DataFrame,
        cv_threshold: float = 0.3,
        ci_width_threshold: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Identify metrics that are unstable (high variance).

        Parameters
        ----------
        stability_results : pd.DataFrame
            Output from compare_sample_sizes()
        cv_threshold : float
            Coefficient of variation threshold (default 0.3 = 30% relative std)
        ci_width_threshold : float, optional
            Confidence interval width threshold

        Returns
        -------
        pd.DataFrame
            Filtered DataFrame of unstable metrics
        """
        unstable = stability_results[stability_results["cv"] > cv_threshold].copy()

        if ci_width_threshold is not None:
            unstable["ci_width"] = unstable["ci_upper"] - unstable["ci_lower"]
            unstable = unstable[unstable["ci_width"] > ci_width_threshold]

        logger.info(f"Found {len(unstable)} unstable metric-size combinations")
        return unstable

    def analyze_variance_trend(self, stability_by_size: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze how metric variance changes with sample size.

        Expected: Variance should decrease as O(1/√n) with sample size.

        Parameters
        ----------
        stability_by_size : pd.DataFrame
            Stability results indexed by sample size

        Returns
        -------
        dict
            Trend analysis including:
            - Pearson correlation between sample_size and variance
            - Power law fit parameters
        """
        if len(stability_by_size) < 3:
            logger.warning("Need at least 3 sample sizes for trend analysis")
            return {}

        sample_sizes = stability_by_size["sample_size"].values
        variances = stability_by_size["std"].values ** 2  # Variance = std²

        # Remove invalid values
        valid_idx = ~(np.isnan(variances) | np.isinf(variances))
        sample_sizes = sample_sizes[valid_idx]
        variances = variances[valid_idx]

        if len(sample_sizes) < 3:
            return {}

        # Correlation with sample size (expect negative correlation)
        corr, p_value = stats.pearsonr(sample_sizes, variances)

        # Log-log regression for power law: variance ~ n^α
        # Expected: α ≈ -1 (variance ∝ 1/n)
        log_n = np.log(sample_sizes)
        log_var = np.log(variances + 1e-10)  # Add small constant to avoid log(0)

        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(log_n, log_var)

        return {
            "size_variance_correlation": float(corr),
            "size_variance_p_value": float(p_value),
            "power_law_exponent": float(slope),
            "power_law_r_squared": float(r_value**2),
            "power_law_p_value": float(p_value_reg),
        }

    def _get_default_stability_metrics(self) -> Dict[str, float]:
        """Return default stability metrics when computation fails."""
        return {
            "mean": 0.0,
            "std": 0.0,
            "cv": float("inf"),
            "sem": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "ci_margin": 0.0,
            "iqr": 0.0,
            "q25": 0.0,
            "q75": 0.0,
            "min": 0.0,
            "max": 0.0,
            "n_samples": 0,
        }

    def _get_default_bootstrap_results(self) -> Dict[str, float]:
        """Return default bootstrap results when computation fails."""
        return {
            "bootstrap_mean": 0.0,
            "bootstrap_std": 0.0,
            "bootstrap_ci_lower": 0.0,
            "bootstrap_ci_upper": 0.0,
            "original_statistic": 0.0,
            "n_bootstrap": 0,
        }
