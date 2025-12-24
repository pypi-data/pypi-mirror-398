"""Unit tests for metric stability analyzer."""

import numpy as np
import pandas as pd
import pytest

from evaluation.metric_stability import MetricStabilityAnalyzer


@pytest.fixture
def mock_metric_values():
    """Create mock metric values for testing."""
    np.random.seed(42)
    return {
        "stable": [0.8, 0.82, 0.81, 0.79, 0.80, 0.81],  # Low variance
        "unstable": [0.5, 0.9, 0.3, 0.7, 0.6, 0.2],  # High variance
        "perfect": [0.75] * 6,  # No variance
    }


def test_analyzer_init():
    """Test analyzer initialization."""
    analyzer = MetricStabilityAnalyzer()
    assert analyzer.confidence_level == 0.95

    custom_analyzer = MetricStabilityAnalyzer(confidence_level=0.99)
    assert custom_analyzer.confidence_level == 0.99


def test_compute_stability_metrics_stable(mock_metric_values):
    """Test stability computation for stable metric."""
    analyzer = MetricStabilityAnalyzer()

    stability = analyzer.compute_stability_metrics(mock_metric_values["stable"], "test_metric")

    assert "mean" in stability
    assert "std" in stability
    assert "cv" in stability

    # Stable metric should have low CV
    assert stability["cv"] < 0.1
    assert stability["mean"] == pytest.approx(0.805, abs=0.01)


def test_compute_stability_metrics_unstable(mock_metric_values):
    """Test stability computation for unstable metric."""
    analyzer = MetricStabilityAnalyzer()

    stability = analyzer.compute_stability_metrics(mock_metric_values["unstable"], "test_metric")

    # Unstable metric should have high CV
    assert stability["cv"] > 0.3
    assert stability["ci_margin"] > 0


def test_compute_stability_metrics_perfect(mock_metric_values):
    """Test stability computation for perfect metric."""
    analyzer = MetricStabilityAnalyzer()

    stability = analyzer.compute_stability_metrics(mock_metric_values["perfect"], "test_metric")

    # Perfect metric should have zero variance
    assert stability["std"] == 0.0
    assert stability["cv"] == 0.0
    assert stability["iqr"] == 0.0


def test_compare_sample_sizes():
    """Test variance comparison across sample sizes."""
    analyzer = MetricStabilityAnalyzer()

    # Create mock results with different variances at different sizes
    results_by_size = {
        100: [{"metric_a": 0.5}, {"metric_a": 0.9}, {"metric_a": 0.3}],  # High variance
        1000: [{"metric_a": 0.75}, {"metric_a": 0.77}, {"metric_a": 0.73}],  # Low variance
        10000: [{"metric_a": 0.8}, {"metric_a": 0.81}, {"metric_a": 0.79}],  # Very low variance
    }

    comparison = analyzer.compare_sample_sizes(results_by_size, "metric_a")

    assert len(comparison) == 3
    assert "sample_size" in comparison.columns
    assert "std" in comparison.columns
    assert "cv" in comparison.columns

    # Variance should decrease with sample size
    comparison_sorted = comparison.sort_values("sample_size")
    stds = comparison_sorted["std"].values
    # Check general trend (allowing some noise)
    assert stds[0] > stds[-1]  # First (smallest) > last (largest)


def test_bootstrap_metric_distribution():
    """Test bootstrap resampling."""
    analyzer = MetricStabilityAnalyzer()

    values = [0.7, 0.75, 0.72, 0.73, 0.74]

    bootstrap_results = analyzer.bootstrap_metric_distribution(
        values, n_bootstrap=100, statistic="mean"
    )

    assert "bootstrap_mean" in bootstrap_results
    assert "bootstrap_std" in bootstrap_results
    assert "bootstrap_ci_lower" in bootstrap_results
    assert "bootstrap_ci_upper" in bootstrap_results

    # Bootstrap mean should be close to actual mean
    assert bootstrap_results["bootstrap_mean"] == pytest.approx(np.mean(values), abs=0.05)


def test_identify_unstable_metrics():
    """Test identification of unstable metrics."""
    analyzer = MetricStabilityAnalyzer()

    stability_results = pd.DataFrame(
        [
            {"metric": "stable_metric", "cv": 0.1, "ci_lower": 0.7, "ci_upper": 0.8},
            {"metric": "unstable_metric", "cv": 0.5, "ci_lower": 0.3, "ci_upper": 0.9},
            {"metric": "moderate_metric", "cv": 0.25, "ci_lower": 0.5, "ci_upper": 0.7},
        ]
    )

    unstable = analyzer.identify_unstable_metrics(stability_results, cv_threshold=0.3)

    assert len(unstable) == 1
    assert unstable.iloc[0]["metric"] == "unstable_metric"


def test_analyze_variance_trend():
    """Test variance trend analysis."""
    analyzer = MetricStabilityAnalyzer()

    stability_by_size = pd.DataFrame(
        [
            {"sample_size": 100, "std": 0.3, "mean": 0.5},
            {"sample_size": 500, "std": 0.15, "mean": 0.52},
            {"sample_size": 1000, "std": 0.1, "mean": 0.53},
            {"sample_size": 5000, "std": 0.05, "mean": 0.54},
        ]
    )

    trend = analyzer.analyze_variance_trend(stability_by_size)

    # Should have negative correlation (variance decreases with size)
    assert "size_variance_correlation" in trend
    assert trend["size_variance_correlation"] < 0

    # Power law exponent should be negative (variance ~ 1/n)
    assert "power_law_exponent" in trend
    assert trend["power_law_exponent"] < 0


def test_edge_case_empty_values():
    """Test handling of empty metric values."""
    analyzer = MetricStabilityAnalyzer()

    stability = analyzer.compute_stability_metrics([], "empty_metric")

    # Should return default values without crashing
    assert stability["mean"] == 0.0
    assert stability["n_samples"] == 0


def test_edge_case_single_value():
    """Test handling of single metric value."""
    analyzer = MetricStabilityAnalyzer()

    stability = analyzer.compute_stability_metrics([0.8], "single_metric")

    # Should return defaults for single value
    assert stability["mean"] == 0.0
    assert stability["n_samples"] == 0


def test_edge_case_nan_values():
    """Test handling of NaN values."""
    analyzer = MetricStabilityAnalyzer()

    values_with_nan = [0.7, np.nan, 0.8, 0.75, np.nan, 0.77]

    stability = analyzer.compute_stability_metrics(values_with_nan, "nan_metric")

    # Should compute on valid values only
    assert stability["n_samples"] == 4
    assert not np.isnan(stability["mean"])
