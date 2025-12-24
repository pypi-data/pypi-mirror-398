"""Tests for evaluation modules."""

import numpy as np
import pandas as pd
import pytest

from evaluation.ml_utility import MLUtilityEvaluator
from evaluation.privacy_metrics import PrivacyEvaluator
from evaluation.sdmetrics_evaluation import SDMetricsEvaluator


@pytest.fixture
def sample_data():
    """Create sample tabular data for testing."""
    np.random.seed(42)
    n_samples = 100

    # Create mixed data types
    data = {
        "num1": np.random.normal(0, 1, n_samples),
        "num2": np.random.normal(5, 2, n_samples),
        "cat1": np.random.choice(["A", "B", "C"], n_samples),
        "cat2": np.random.choice([0, 1], n_samples),
        "target": np.random.choice([0, 1], n_samples),
    }

    return pd.DataFrame(data)


@pytest.fixture
def synthetic_data(sample_data):
    """Create synthetic data similar to sample data."""
    np.random.seed(123)
    n_samples = 75

    data = {
        "num1": np.random.normal(0.1, 1.1, n_samples),
        "num2": np.random.normal(4.8, 2.1, n_samples),
        "cat1": np.random.choice(["A", "B", "C"], n_samples),
        "cat2": np.random.choice([0, 1], n_samples),
        "target": np.random.choice([0, 1], n_samples),
    }

    return pd.DataFrame(data)


class TestSDMetricsEvaluator:
    """Test SDMetrics evaluator."""

    def test_initialization(self):
        """Test SDMetrics evaluator initialization."""
        evaluator = SDMetricsEvaluator()
        assert evaluator is not None

    def test_evaluate_all(self, sample_data, synthetic_data):
        """Test full evaluation."""
        evaluator = SDMetricsEvaluator()
        results = evaluator.evaluate_all(sample_data, synthetic_data)

        assert isinstance(results, dict)
        # Check that we get various metrics
        assert len(results) > 0
        assert any("score" in key.lower() for key in results.keys())


class TestPrivacyEvaluator:
    """Test Privacy evaluator."""

    def test_initialization(self):
        """Test Privacy evaluator initialization."""
        evaluator = PrivacyEvaluator()
        assert evaluator is not None
        assert evaluator.max_samples == 5000

    def test_evaluate_privacy(self, sample_data, synthetic_data):
        """Test privacy evaluation."""
        evaluator = PrivacyEvaluator()
        results = evaluator.evaluate(sample_data, synthetic_data)

        assert isinstance(results, dict)
        assert "dcr" in results
        assert "nndr" in results


class TestMLUtilityEvaluator:
    """Test ML Utility evaluator."""

    def test_initialization(self):
        """Test ML Utility evaluator initialization."""
        evaluator = MLUtilityEvaluator()
        assert evaluator is not None
        assert evaluator.task_type == "classification"
        assert evaluator.random_state == 42

    def test_evaluate_utility(self, sample_data, synthetic_data):
        """Test utility evaluation."""
        evaluator = MLUtilityEvaluator()
        # Split real data for testing
        real_train = sample_data.iloc[:70]
        real_test = sample_data.iloc[70:]

        results = evaluator.evaluate(real_train, real_test, synthetic_data, "target")

        assert isinstance(results, dict)
        assert "trtr" in results
        assert "tstr" in results
        assert "utility_ratio" in results


class TestEvaluatorIntegration:
    """Integration tests for evaluators."""

    def test_all_evaluators_have_evaluate_method(self, sample_data, synthetic_data):
        """Test that all evaluators have evaluate method."""
        evaluators = [SDMetricsEvaluator(), PrivacyEvaluator(), MLUtilityEvaluator()]

        for evaluator in evaluators:
            # SDMetrics has evaluate_all, others have evaluate
            has_method = hasattr(evaluator, "evaluate") or hasattr(evaluator, "evaluate_all")
            assert has_method
