"""Tests for scripts."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from scripts.download_datasets import DatasetDownloader


class TestDatasetDownloader:
    """Test dataset downloader."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_initialization(self, temp_data_dir):
        """Test downloader initialization."""
        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        assert downloader.data_dir == temp_data_dir
        assert temp_data_dir.exists()

    @patch("sklearn.datasets.load_diabetes")
    def test_download_diabetes(self, mock_load_diabetes, temp_data_dir):
        """Test diabetes dataset download."""
        # Mock the sklearn dataset loading
        mock_df = pd.DataFrame({"feature1": [1, 2, 3], "target": [0.1, 0.2, 0.3]})
        mock_load_diabetes.return_value = MagicMock()
        mock_load_diabetes.return_value.frame = mock_df

        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        downloader.download_diabetes()

        output_path = temp_data_dir / "diabetes.csv"
        assert output_path.exists()

        # Check that file contains data
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert len(df.columns) == 2

    @patch("pandas.read_csv")
    def test_download_adult(self, mock_read_csv, temp_data_dir):
        """Test adult dataset download."""
        # Mock pandas read_csv to return sample data
        mock_df = pd.DataFrame(
            {
                "age": [25, 30, 35],
                "workclass": ["Private", "Self-emp", "Gov"],
                "income": ["<=50K", ">50K", "<=50K"],
            }
        )
        mock_read_csv.return_value = mock_df

        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        downloader.download_adult()

        output_path = temp_data_dir / "adult.csv"
        assert output_path.exists()

        # Check that file contains data (don't verify exact content)
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert "income" in df.columns
        # Just check that income column exists and has the right length
        assert len(df["income"]) == 3

    @patch("pandas.read_excel")
    def test_download_credit_handles_errors(self, mock_read_excel, temp_data_dir):
        """Test credit download handles network errors gracefully."""
        # Mock pandas read_excel to raise an exception
        mock_read_excel.side_effect = Exception("Network timeout")

        downloader = DatasetDownloader(data_dir=str(temp_data_dir))

        # download_credit should raise an exception when it fails
        with pytest.raises(Exception):
            downloader.download_credit()

    @patch("pandas.read_csv")
    @patch("pandas.read_excel")
    @patch("sklearn.datasets.load_diabetes")
    def test_download_all(self, mock_load_diabetes, mock_read_excel, mock_read_csv, temp_data_dir):
        """Test downloading all datasets."""
        # Mock the dataframes
        mock_adult_df = pd.DataFrame(
            {"age": [25, 30], "workclass": ["Private", "Gov"], "income": ["<=50K", ">50K"]}
        )
        mock_read_csv.return_value = mock_adult_df

        # Mock sklearn for diabetes
        mock_diabetes_df = pd.DataFrame({"feature1": [1, 2], "target": [0.1, 0.2]})
        mock_load_diabetes.return_value = MagicMock()
        mock_load_diabetes.return_value.frame = mock_diabetes_df

        # Mock credit to fail
        mock_read_excel.side_effect = Exception("Network error")

        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        # download_all should not raise exceptions even if individual downloads fail
        downloader.download_all()

        # Check that expected files exist (adult and diabetes should succeed, credit should fail)
        expected_files = ["adult.csv", "diabetes.csv"]
        for filename in expected_files:
            assert (temp_data_dir / filename).exists()
