"""Integration tests for the full synthetic data evaluation pipeline."""

import numpy as np
import pandas as pd
import pytest

from evaluation.ml_utility import MLUtilityEvaluator
from evaluation.privacy_metrics import PrivacyEvaluator
from evaluation.sdmetrics_evaluation import SDMetricsEvaluator
from generators.ctgan_model import CTGANGenerator
from generators.gaussian_copula import GaussianCopulaGenerator
from generators.tvae_model import TVAEGenerator


@pytest.fixture
def sample_data():
    """Create sample tabular data for testing."""
    np.random.seed(42)
    n_samples = 200

    # Create mixed data types
    data = {
        "num1": np.random.normal(0, 1, n_samples),
        "num2": np.random.normal(5, 2, n_samples),
        "cat1": np.random.choice(["A", "B", "C"], n_samples),
        "cat2": np.random.choice([0, 1], n_samples),
        "target": np.random.choice([0, 1], n_samples),
    }

    return pd.DataFrame(data)


class TestFullPipeline:
    """Test the complete synthetic data generation and evaluation pipeline."""

    def test_ctgan_pipeline(self, sample_data):
        """Test full pipeline with CTGAN generator."""
        # Generate synthetic data
        generator = CTGANGenerator(epochs=1, verbose=False)
        synthetic_data = generator.fit_generate(sample_data, n_samples=100)

        assert isinstance(synthetic_data, pd.DataFrame)
        assert len(synthetic_data) == 100
        assert list(synthetic_data.columns) == list(sample_data.columns)

        # Evaluate with SDMetrics
        sd_evaluator = SDMetricsEvaluator()
        sd_results = sd_evaluator.evaluate_all(sample_data, synthetic_data)
        assert isinstance(sd_results, dict)
        assert len(sd_results) > 0

        # Evaluate privacy
        privacy_evaluator = PrivacyEvaluator()
        privacy_results = privacy_evaluator.evaluate(sample_data, synthetic_data)
        assert isinstance(privacy_results, dict)
        assert "dcr" in privacy_results

        # Evaluate ML utility
        ml_evaluator = MLUtilityEvaluator()
        real_train = sample_data.iloc[:140]
        real_test = sample_data.iloc[140:]

        ml_results = ml_evaluator.evaluate(real_train, real_test, synthetic_data, "target")
        assert isinstance(ml_results, dict)
        assert "utility_ratio" in ml_results

    def test_tvae_pipeline(self, sample_data):
        """Test full pipeline with TVAE generator."""
        # Generate synthetic data
        generator = TVAEGenerator(epochs=1, verbose=False)
        synthetic_data = generator.fit_generate(sample_data, n_samples=100)

        assert isinstance(synthetic_data, pd.DataFrame)
        assert len(synthetic_data) == 100

        # Evaluate with SDMetrics
        sd_evaluator = SDMetricsEvaluator()
        sd_results = sd_evaluator.evaluate_all(sample_data, synthetic_data)
        assert isinstance(sd_results, dict)

    def test_gaussian_copula_pipeline(self, sample_data):
        """Test full pipeline with Gaussian Copula generator."""
        # Generate synthetic data
        generator = GaussianCopulaGenerator(random_state=42)
        synthetic_data = generator.fit_generate(sample_data, n_samples=100)

        assert isinstance(synthetic_data, pd.DataFrame)
        assert len(synthetic_data) == 100

        # Evaluate with SDMetrics
        sd_evaluator = SDMetricsEvaluator()
        sd_results = sd_evaluator.evaluate_all(sample_data, synthetic_data)
        assert isinstance(sd_results, dict)

    def test_multiple_generators_comparison(self, sample_data):
        """Test comparing multiple generators on same data."""
        generators = [
            CTGANGenerator(epochs=1, verbose=False),
            TVAEGenerator(epochs=1, verbose=False),
            GaussianCopulaGenerator(random_state=42),
        ]

        results = {}
        for generator in generators:
            synthetic_data = generator.fit_generate(sample_data, n_samples=50)
            evaluator = SDMetricsEvaluator()
            results[generator.__class__.__name__] = evaluator.evaluate_all(
                sample_data, synthetic_data
            )

        # All generators should produce results
        assert len(results) == 3
        for gen_name, gen_results in results.items():
            assert isinstance(gen_results, dict)
            assert len(gen_results) > 0

    def test_pipeline_with_different_data_sizes(self):
        """Test pipeline robustness with different data sizes."""
        sizes = [50, 100, 200]

        for size in sizes:
            # Create data of different sizes
            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "num": np.random.normal(0, 1, size),
                    "cat": np.random.choice(["A", "B"], size),
                    "target": np.random.choice([0, 1], size),
                }
            )

            # Generate and evaluate
            generator = GaussianCopulaGenerator(random_state=42)
            synthetic = generator.fit_generate(data, n_samples=min(50, size // 2))

            evaluator = SDMetricsEvaluator()
            results = evaluator.evaluate_all(data, synthetic)

            assert isinstance(results, dict)
            assert len(results) > 0

    def test_pipeline_error_handling(self, sample_data):
        """Test pipeline handles errors gracefully."""
        # Test with mismatched column data
        bad_synthetic = sample_data.copy()
        bad_synthetic["num1"] = bad_synthetic["num1"].astype(str)

        evaluator = SDMetricsEvaluator()

        # Should handle gracefully or raise informative error
        try:
            results = evaluator.evaluate_all(sample_data, bad_synthetic)
            assert isinstance(results, dict)
        except Exception as e:
            # Should be informative error
            assert len(str(e)) > 0


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_generation_evaluation_cycle(self, sample_data):
        """Test a complete generate-evaluate cycle."""
        # Step 1: Generate
        generator = CTGANGenerator(epochs=2, verbose=False)
        synthetic = generator.fit_generate(sample_data, n_samples=80)

        # Step 2: Evaluate quality
        quality_evaluator = SDMetricsEvaluator()
        quality_results = quality_evaluator.evaluate_all(sample_data, synthetic)

        # Step 3: Evaluate privacy
        privacy_evaluator = PrivacyEvaluator()
        privacy_results = privacy_evaluator.evaluate(sample_data, synthetic)

        # Step 4: Evaluate utility
        utility_evaluator = MLUtilityEvaluator()
        train_data = sample_data.iloc[:160]
        test_data = sample_data.iloc[160:]

        utility_results = utility_evaluator.evaluate(train_data, test_data, synthetic, "target")

        # All evaluations should complete successfully
        assert isinstance(quality_results, dict)
        assert isinstance(privacy_results, dict)
        assert isinstance(utility_results, dict)

        # Results should contain expected metrics
        assert len(quality_results) > 0
        assert "dcr" in privacy_results
        assert "utility_ratio" in utility_results
