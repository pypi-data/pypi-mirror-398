"""Evaluation package for synthetic data quality assessment."""

__version__ = "0.1.0"

from .metric_stability import MetricStabilityAnalyzer

# Core modules (always available, lightweight)
from .progressive_sampler import ProgressiveSampler
from .tstr_correlation import TSTRCorrelationAnalyzer


# Heavy dependencies - lazy import to support lightweight CI
# These require sdmetrics, torch, etc.
def _get_sdmetrics_evaluator():
    """Lazy load SDMetricsEvaluator to avoid import errors when sdmetrics not installed."""
    from .sdmetrics_evaluation import SDMetricsEvaluator

    return SDMetricsEvaluator


def _get_ml_utility_evaluator():
    """Lazy load MLUtilityEvaluator."""
    from .ml_utility import MLUtilityEvaluator

    return MLUtilityEvaluator


def _get_privacy_evaluator():
    """Lazy load PrivacyEvaluator."""
    from .privacy_metrics import PrivacyEvaluator

    return PrivacyEvaluator


__all__ = [
    "ProgressiveSampler",
    "MetricStabilityAnalyzer",
    "TSTRCorrelationAnalyzer",
    # Lazy-loaded evaluators (call the getter functions)
    "_get_sdmetrics_evaluator",
    "_get_ml_utility_evaluator",
    "_get_privacy_evaluator",
]
