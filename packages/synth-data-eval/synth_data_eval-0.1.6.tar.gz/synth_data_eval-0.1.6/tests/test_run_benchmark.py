"""Tests for benchmark runner script."""

import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yaml

from scripts.run_benchmark import BenchmarkRunner


@pytest.fixture
def temp_config():
    """Create temporary config for testing."""
    config = {
        "datasets": {
            "test_dataset": {
                "file": "datasets/adult.csv",  # Use existing dataset
                "target": "income",
                "task": "classification",
                "test_size": 0.2,
                "discrete_columns": ["workclass", "education"],
                "sensitive_columns": ["race", "sex"],
            }
        },
        "generators": {
            "test_ctgan": {
                "class": "CTGANGenerator",
                "params": {"epochs": 1, "batch_size": 50, "verbose": False},
            }
        },
        "evaluation": {
            "random_seed": 42,
            "n_runs": 1,
            "n_synthetic_samples": 100,
            "metrics": ["sdmetrics", "ml_utility", "privacy"],
        },
        "output": {"results_dir": "results"},
    }
    return config


@pytest.fixture
def temp_config_file(temp_config):
    """Create temporary config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(temp_config, f)
        return f.name


class TestBenchmarkRunner:
    """Test benchmark runner functionality."""

    def test_initialization(self, temp_config_file):
        """Test benchmark runner initialization."""
        runner = BenchmarkRunner(temp_config_file)
        assert runner.config is not None
        assert "datasets" in runner.config
        assert "generators" in runner.config

    def test_load_dataset(self, temp_config_file):
        """Test dataset loading and splitting."""
        runner = BenchmarkRunner(temp_config_file)

        dataset_config = runner.config["datasets"]["test_dataset"]

        # This will fail if adult.csv doesn't exist, but that's expected
        # in a real test environment
        try:
            train_df, test_df = runner.load_dataset(dataset_config)
            assert isinstance(train_df, pd.DataFrame)
            assert isinstance(test_df, pd.DataFrame)
            assert len(train_df) > len(test_df)  # Train should be larger
            assert "income" in train_df.columns
            assert "income" in test_df.columns
        except FileNotFoundError:
            # Expected if dataset doesn't exist
            pytest.skip("Dataset file not found")

    def test_get_generator(self, temp_config_file):
        """Test generator instantiation."""
        runner = BenchmarkRunner(temp_config_file)

        generator_config = runner.config["generators"]["test_ctgan"]

        generator = runner.get_generator("test_ctgan", generator_config)
        assert generator is not None
        assert hasattr(generator, "fit_generate")

    def test_get_generator_unknown(self, temp_config_file):
        """Test unknown generator raises error."""
        runner = BenchmarkRunner(temp_config_file)

        generator_config = {"class": "UnknownGenerator", "params": {}}

        with pytest.raises(ValueError, match="Unknown generator"):
            runner.get_generator("unknown", generator_config)

    @patch("scripts.run_benchmark.BenchmarkRunner.load_dataset")
    @patch("scripts.run_benchmark.BenchmarkRunner.get_generator")
    @patch("scripts.run_benchmark.SDMetricsEvaluator")
    @patch("scripts.run_benchmark.MLUtilityEvaluator")
    @patch("scripts.run_benchmark.PrivacyEvaluator")
    def test_run_single_experiment(
        self, mock_privacy, mock_ml, mock_sdm, mock_get_gen, mock_load_dataset, temp_config_file
    ):
        """Test single experiment execution."""
        # Setup mocks
        mock_train = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"], "target": [0, 1, 0]})
        mock_test = pd.DataFrame({"A": [4, 5], "B": ["w", "v"], "target": [1, 0]})
        mock_load_dataset.return_value = (mock_train, mock_test)

        mock_generator = MagicMock()
        mock_generator.fit_generate.return_value = pd.DataFrame(
            {"A": [1.1, 2.1, 3.1], "B": ["x", "y", "z"], "target": [0, 1, 0]}
        )
        mock_get_gen.return_value = mock_generator

        mock_sdm_instance = MagicMock()
        mock_sdm_instance.evaluate_all.return_value = {"quality": 0.8, "privacy": 0.7}
        mock_sdm.return_value = mock_sdm_instance

        mock_ml_instance = MagicMock()
        mock_ml_instance.evaluate.return_value = {"utility": 0.9}
        mock_ml.return_value = mock_ml_instance

        mock_privacy_instance = MagicMock()
        mock_privacy_instance.evaluate.return_value = {"privacy_score": 0.6}
        mock_privacy.return_value = mock_privacy_instance

        runner = BenchmarkRunner(temp_config_file)

        results = runner.run_single_experiment(
            "test_dataset",
            runner.config["datasets"]["test_dataset"],
            "test_ctgan",
            runner.config["generators"]["test_ctgan"],
            0,  # run_id
        )

        assert isinstance(results, dict)
        assert "dataset" in results
        assert "generator" in results
        assert results["dataset"] == "test_dataset"
        assert results["generator"] == "test_ctgan"

    def test_run_all_experiments_empty_config(self, temp_config_file):
        """Test running all experiments with empty config."""
        # Modify config to have empty datasets
        runner = BenchmarkRunner(temp_config_file)
        runner.config["datasets"] = {}
        runner.config["generators"] = {}

        results = runner.run_all_experiments()
        assert results == []

    @patch("scripts.run_benchmark.BenchmarkRunner.run_single_experiment")
    def test_run_all_experiments(self, mock_run_single, temp_config_file):
        """Test running all experiments."""
        mock_run_single.return_value = {"test": "result"}

        runner = BenchmarkRunner(temp_config_file)
        results = runner.run_all_experiments()

        # Should call run_single_experiment for each
        # dataset-generator combination
        expected_calls = len(runner.config["datasets"]) * len(runner.config["generators"])
        assert mock_run_single.call_count == expected_calls
        assert len(results) == expected_calls


def test_main_function():
    """Test main function doesn't crash."""
    # This is a basic smoke test - main() should not crash on import
    # In a real scenario, we'd mock the dependencies
    from scripts.run_benchmark import main

    # Just test that the function exists and can be called
    # (it will fail due to missing config, but shouldn't crash on import)
    assert callable(main)
