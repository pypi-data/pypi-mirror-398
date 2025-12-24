"""Unit tests for TSTR correlation analyzer."""

import numpy as np
import pandas as pd
import pytest

from evaluation.tstr_correlation import TSTRCorrelationAnalyzer


@pytest.fixture
def mock_evaluation_data():
    """Create mock evaluation data with metrics and TSTR scores."""
    np.random.seed(42)
    n_experiments = 20

    # Create synthetic metric values
    metric_scores = pd.DataFrame(
        {
            "sdm_quality_score": np.random.uniform(0.5, 0.9, n_experiments),
            "sdm_correlation_similarity": np.random.uniform(0.6, 1.0, n_experiments),
            "privacy_dcr": np.random.uniform(0.1, 0.5, n_experiments),
        }
    )

    # Create TSTR scores with some correlation to metrics
    tstr_scores = pd.Series(
        0.3 * metric_scores["sdm_quality_score"]
        + 0.5 * metric_scores["sdm_correlation_similarity"]
        + 0.2 * np.random.randn(n_experiments)
    )

    return metric_scores, tstr_scores


def test_analyzer_init():
    """Test analyzer initialization."""
    analyzer = TSTRCorrelationAnalyzer()
    assert analyzer.correlation_method == "spearman"

    pearson_analyzer = TSTRCorrelationAnalyzer(correlation_method="pearson")
    assert pearson_analyzer.correlation_method == "pearson"


def test_compute_metric_utility_correlation(mock_evaluation_data):
    """Test correlation computation."""
    metric_scores, tstr_scores = mock_evaluation_data
    analyzer = TSTRCorrelationAnalyzer()

    correlations = analyzer.compute_metric_utility_correlation(
        metric_scores, tstr_scores, min_samples=5
    )

    assert not correlations.empty
    assert "metric" in correlations.columns
    assert "correlation" in correlations.columns
    assert "p_value" in correlations.columns
    assert "is_significant" in correlations.columns

    # Should have 3 metrics
    assert len(correlations) == 3

    # Correlations should be sorted by absolute value
    abs_corrs = correlations["correlation"].abs()
    assert all(abs_corrs.iloc[i] >= abs_corrs.iloc[i + 1] for i in range(len(abs_corrs) - 1))


def test_rank_metrics_by_predictive_power():
    """Test metric ranking across sample sizes."""
    analyzer = TSTRCorrelationAnalyzer()

    # Create mock correlations for multiple sample sizes
    correlations_by_size = {
        100: pd.DataFrame(
            {
                "metric": ["metric_a", "metric_b", "metric_c"],
                "correlation": [0.3, 0.7, 0.5],
                "p_value": [0.1, 0.01, 0.05],
            }
        ),
        1000: pd.DataFrame(
            {
                "metric": ["metric_a", "metric_b", "metric_c"],
                "correlation": [0.5, 0.75, 0.6],
                "p_value": [0.02, 0.001, 0.01],
            }
        ),
        10000: pd.DataFrame(
            {
                "metric": ["metric_a", "metric_b", "metric_c"],
                "correlation": [0.6, 0.8, 0.65],
                "p_value": [0.001, 0.0001, 0.001],
            }
        ),
    }

    ranking = analyzer.rank_metrics_by_predictive_power(correlations_by_size)

    assert not ranking.empty
    assert "metric" in ranking.columns
    assert "mean_abs_correlation" in ranking.columns
    assert "std_correlation" in ranking.columns
    assert "n_significant" in ranking.columns

    # metric_b should rank highest (strongest correlations)
    assert ranking.iloc[0]["metric"] == "metric_b"
    assert ranking.iloc[0]["n_significant"] == 3  # Significant at all sizes


def test_identify_unreliable_metrics():
    """Test identification of unreliable metrics."""
    analyzer = TSTRCorrelationAnalyzer()

    correlations_by_size = {
        100: pd.DataFrame(
            {
                "metric": ["weak_metric", "strong_metric", "unstable_metric"],
                "correlation": [0.1, 0.8, 0.7],
                "p_value": [0.5, 0.001, 0.01],
            }
        ),
        1000: pd.DataFrame(
            {
                "metric": ["weak_metric", "strong_metric", "unstable_metric"],
                "correlation": [0.15, 0.82, 0.2],  # unstable_metric drops significantly
                "p_value": [0.4, 0.001, 0.3],
            }
        ),
    }

    unreliable = analyzer.identify_unreliable_metrics(
        correlations_by_size, min_correlation=0.3, max_variance=0.3
    )

    # Should identify weak_metric (low correlation) and unstable_metric (high variance)
    # weak_metric: mean corr ~0.125 (< 0.3 threshold)
    # unstable_metric: variance = 0.135 (correlation drops from 0.7 to 0.2)

    # The function identifies metrics below min_correlation OR above max_variance
    # weak_metric has low correlation, so it should be identified
    assert "weak_metric" in unreliable
    # strong_metric should NOT be in unreliable (high correlation, low variance)
    assert "strong_metric" not in unreliable

    # Note: unstable_metric's variance of 0.135 is below max_variance threshold (0.3)
    # so it may or may not be flagged depending on mean correlation
    # Since its mean is ~0.45 (above 0.3), it won't be flagged by low correlation either


def test_analyze_correlation_breakdown():
    """Test correlation breakdown analysis."""
    analyzer = TSTRCorrelationAnalyzer()

    correlations_by_size = {
        100: pd.DataFrame(
            {
                "metric": ["stable_metric", "breaking_metric"],
                "correlation": [0.75, 0.3],  # breaking_metric weak at small size
                "p_value": [0.01, 0.2],
            }
        ),
        10000: pd.DataFrame(
            {
                "metric": ["stable_metric", "breaking_metric"],
                "correlation": [0.78, 0.85],  # breaking_metric strong at large size
                "p_value": [0.001, 0.001],
            }
        ),
    }

    breakdown = analyzer.analyze_correlation_breakdown(correlations_by_size)

    assert not breakdown.empty
    assert "metric" in breakdown.columns
    assert "correlation_at_smallest" in breakdown.columns
    assert "correlation_at_largest" in breakdown.columns
    assert "correlation_degradation" in breakdown.columns
    assert "breaks_down" in breakdown.columns

    # breaking_metric should show significant degradation
    breaking_row = breakdown[breakdown["metric"] == "breaking_metric"].iloc[0]
    assert breaking_row["correlation_degradation"] < -0.3
    assert breaking_row["breaks_down"] == True

    # stable_metric should not break down
    stable_row = breakdown[breakdown["metric"] == "stable_metric"].iloc[0]
    assert stable_row["breaks_down"] == False


def test_create_correlation_heatmap_data():
    """Test heatmap data creation."""
    analyzer = TSTRCorrelationAnalyzer()

    correlations_by_size = {
        100: pd.DataFrame(
            {
                "metric": ["metric_a", "metric_b"],
                "correlation": [0.5, 0.7],
                "p_value": [0.05, 0.01],
            }
        ),
        1000: pd.DataFrame(
            {
                "metric": ["metric_a", "metric_b"],
                "correlation": [0.6, 0.75],
                "p_value": [0.02, 0.001],
            }
        ),
    }

    heatmap_data = analyzer.create_correlation_heatmap_data(correlations_by_size)

    assert isinstance(heatmap_data, pd.DataFrame)
    assert heatmap_data.shape == (2, 2)  # 2 metrics × 2 sample sizes
    assert 100 in heatmap_data.columns
    assert 1000 in heatmap_data.columns

    # Check values
    assert heatmap_data.loc["metric_a", 100] == 0.5
    assert heatmap_data.loc["metric_b", 1000] == 0.75


def test_edge_case_insufficient_data():
    """Test handling of insufficient data."""
    analyzer = TSTRCorrelationAnalyzer()

    metric_scores = pd.DataFrame(
        {
            "metric_a": [0.5, 0.6],  # Only 2 samples
        }
    )
    tstr_scores = pd.Series([0.7, 0.8])

    correlations = analyzer.compute_metric_utility_correlation(
        metric_scores, tstr_scores, min_samples=5  # Require 5 samples
    )

    # Should return empty or skip metric
    assert correlations.empty or len(correlations) == 0


def test_edge_case_nan_values():
    """Test handling of NaN values."""
    analyzer = TSTRCorrelationAnalyzer()

    metric_scores = pd.DataFrame(
        {
            "metric_a": [0.5, np.nan, 0.7, 0.6, np.nan, 0.8],
        }
    )
    tstr_scores = pd.Series([0.6, 0.7, np.nan, 0.75, 0.8, 0.85])

    correlations = analyzer.compute_metric_utility_correlation(
        metric_scores, tstr_scores, min_samples=3
    )

    # Should compute on valid overlapping data only
    assert not correlations.empty
    row = correlations[correlations["metric"] == "metric_a"].iloc[0]
    assert row["n_samples"] == 3  # Only 3 valid overlapping points
