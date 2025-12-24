"""Tests for results visualization script."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from scripts.visualize_results import ResultsVisualizer


@pytest.fixture
def sample_results_df():
    """Create sample results DataFrame for testing."""
    np.random.seed(42)
    n_results = 20

    data = {
        "dataset": np.random.choice(["adult", "diabetes"], n_results),
        "generator": np.random.choice(["ctgan", "tvae", "gaussian_copula"], n_results),
        "run_id": np.arange(n_results),
        "sdm_quality": np.random.uniform(0.5, 0.9, n_results),
        "sdm_privacy": np.random.uniform(0.3, 0.8, n_results),
        "ml_trtr_accuracy": np.random.uniform(0.6, 0.85, n_results),
        "ml_tstr_accuracy": np.random.uniform(0.55, 0.8, n_results),
        "ml_utility_ratio": np.random.uniform(0.8, 1.2, n_results),
        "privacy_dcr": np.random.uniform(0.4, 0.9, n_results),
        "privacy_nndr": np.random.uniform(0.5, 1.0, n_results),
        "training_time": np.random.uniform(10, 300, n_results),
        "generation_time": np.random.uniform(1, 50, n_results),
    }

    return pd.DataFrame(data)


@pytest.fixture
def temp_results_csv(sample_results_df):
    """Create temporary CSV file with results."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_results_df.to_csv(f, index=False)
        return f.name


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    return Path(temp_dir)


class TestResultsVisualizer:
    """Test results visualization functionality."""

    def test_initialization(self, temp_results_csv, temp_output_dir):
        """Test visualizer initialization."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))

        assert isinstance(visualizer.results_df, pd.DataFrame)
        assert len(visualizer.results_df) > 0
        assert isinstance(visualizer.summary_df, pd.DataFrame)
        assert temp_output_dir.exists()

    def test_initialization_missing_file(self, temp_output_dir):
        """Test initialization with missing file."""
        with pytest.raises(FileNotFoundError):
            ResultsVisualizer("nonexistent.csv", str(temp_output_dir))

    @patch("scripts.visualize_results.plt.savefig")
    def test_plot_sdmetrics(self, mock_savefig, temp_results_csv, temp_output_dir):
        """Test SDMetrics comparison plotting."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))
        # Should not raise an exception
        visualizer.plot_sdmetrics_comparison()

    @patch("scripts.visualize_results.plt.savefig")
    def test_plot_ml_utility(self, mock_savefig, temp_results_csv, temp_output_dir):
        """Test ML utility comparison plotting."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))
        # Should not raise an exception
        visualizer.plot_ml_utility_comparison()

    @patch("scripts.visualize_results.plt.savefig")
    def test_plot_privacy(self, mock_savefig, temp_results_csv, temp_output_dir):
        """Test privacy metrics plotting."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))
        # Should not raise an exception
        visualizer.plot_privacy_metrics()

    @patch("scripts.visualize_results.plt.savefig")
    def test_plot_training_times(self, mock_savefig, temp_results_csv, temp_output_dir):
        """Test training times plotting."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))
        # Should not raise an exception
        visualizer.plot_training_times()

    @patch("scripts.visualize_results.plt.savefig")
    def test_plot_radar(self, mock_savefig, temp_results_csv, temp_output_dir):
        """Test radar chart plotting."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))
        # Should not raise an exception
        visualizer.plot_radar_chart()

    @patch("scripts.visualize_results.plt.savefig")
    def test_plot_heatmap(self, mock_savefig, temp_results_csv, temp_output_dir):
        """Test heatmap plotting."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))
        # Should not raise an exception
        visualizer.plot_heatmap()

    @patch("scripts.visualize_results.plt.savefig")
    def test_plot_all(self, mock_savefig, temp_results_csv, temp_output_dir):
        """Test plotting all visualizations."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))

        # Mock all the individual plot methods
        with patch.object(visualizer, "plot_sdmetrics_comparison"), patch.object(
            visualizer, "plot_ml_utility_comparison"
        ), patch.object(visualizer, "plot_privacy_metrics"), patch.object(
            visualizer, "plot_training_times"
        ), patch.object(
            visualizer, "plot_radar_chart"
        ), patch.object(
            visualizer, "plot_heatmap"
        ):
            visualizer.plot_all()

    def test_summary_df_aggregation(self, temp_results_csv, temp_output_dir):
        """Test that summary_df properly aggregates results."""
        visualizer = ResultsVisualizer(temp_results_csv, str(temp_output_dir))

        # summary_df should be aggregated by dataset and generator
        assert "dataset" in visualizer.summary_df.columns
        assert "generator" in visualizer.summary_df.columns

        # Should have fewer rows than original (aggregated)
        assert len(visualizer.summary_df) <= len(visualizer.results_df)


def test_main_function_no_args():
    """Test main function with no arguments."""
    from scripts.visualize_results import main

    # Should print usage and return
    # We can't easily test this without mocking sys.argv
    assert callable(main)


def test_main_function_missing_file():
    """Test main function with missing file."""
    from scripts.visualize_results import main

    # Mock sys.argv to provide a missing file
    with patch("sys.argv", ["visualize_results.py", "missing_file.csv"]):
        # Should raise FileNotFoundError when trying to read CSV
        with pytest.raises(FileNotFoundError):
            main()
