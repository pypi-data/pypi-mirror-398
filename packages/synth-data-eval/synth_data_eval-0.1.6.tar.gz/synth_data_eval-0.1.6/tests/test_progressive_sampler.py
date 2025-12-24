"""Unit tests for progressive sampler."""

import numpy as np
import pandas as pd
import pytest

from evaluation.progressive_sampler import ProgressiveSampler


@pytest.fixture
def sample_data():
    """Create sample dataset for testing."""
    np.random.seed(42)
    n_samples = 1000

    data = pd.DataFrame(
        {
            "feature1": np.random.randn(n_samples),
            "feature2": np.random.randn(n_samples),
            "feature3": np.random.randint(0, 5, n_samples),
            "target": np.random.randint(0, 2, n_samples),
        }
    )

    return data


def test_progressive_sampler_init():
    """Test sampler initialization."""
    sampler = ProgressiveSampler()
    assert sampler.sample_sizes == [100, 500, 1000, 5000, 10000, 50000]

    custom_sampler = ProgressiveSampler(sample_sizes=[10, 50, 100])
    assert custom_sampler.sample_sizes == [10, 50, 100]


def test_create_samples_basic(sample_data):
    """Test basic sample creation."""
    sampler = ProgressiveSampler(sample_sizes=[100, 500])

    samples = sampler.create_samples(
        data=sample_data,
        target_col="target",
        n_repeats=3,
        stratify=True,
        task_type="classification",
    )

    assert len(samples) == 2  # Two sample sizes
    assert 100 in samples
    assert 500 in samples

    assert len(samples[100]) == 3  # Three repeats
    assert len(samples[500]) == 3


def test_stratified_sampling(sample_data):
    """Test stratified sampling preserves class ratios."""
    sampler = ProgressiveSampler(sample_sizes=[200])

    samples = sampler.create_samples(
        data=sample_data,
        target_col="target",
        n_repeats=5,
        stratify=True,
        task_type="classification",
    )

    original_ratio = sample_data["target"].value_counts(normalize=True)

    for sample_df in samples[200]:
        sample_ratio = sample_df["target"].value_counts(normalize=True)
        # Check class ratios are similar (within 10%)
        for cls in original_ratio.index:
            assert abs(sample_ratio[cls] - original_ratio[cls]) < 0.1


def test_sample_size_validation(sample_data):
    """Test handling of samples larger than dataset."""
    sampler = ProgressiveSampler(sample_sizes=[100, 5000])  # 5000 > 1000

    samples = sampler.create_samples(
        data=sample_data, target_col="target", n_repeats=2, task_type="classification"
    )

    # Should skip 5000 as it exceeds dataset size
    assert 100 in samples
    assert 5000 not in samples


def test_train_test_split(sample_data):
    """Test train/test split functionality."""
    sampler = ProgressiveSampler(sample_sizes=[100, 200])

    splits = sampler.create_train_test_split(
        data=sample_data, target_col="target", test_size=0.2, task_type="classification"
    )

    assert len(splits) == 2

    for sample_size, split_list in splits.items():
        for train_df, test_df in split_list:
            # Check sizes
            total = len(train_df) + len(test_df)
            assert abs(total - sample_size) <= 1  # Allow ±1 for rounding

            # Check test size ratio
            test_ratio = len(test_df) / total
            assert abs(test_ratio - 0.2) < 0.05


def test_summary_statistics(sample_data):
    """Test summary statistics generation."""
    sampler = ProgressiveSampler(sample_sizes=[100, 200])

    samples = sampler.create_samples(
        data=sample_data, target_col="target", n_repeats=2, task_type="classification"
    )

    summary = sampler.get_summary_statistics(samples, target_col="target")

    assert not summary.empty
    assert "sample_size" in summary.columns
    assert "n_rows" in summary.columns
    assert "n_classes" in summary.columns
    assert len(summary) == 4  # 2 sizes × 2 repeats


def test_regression_task(sample_data):
    """Test sampling for regression tasks."""
    sample_data["regression_target"] = np.random.randn(len(sample_data))

    sampler = ProgressiveSampler(sample_sizes=[100])

    samples = sampler.create_samples(
        data=sample_data,
        target_col="regression_target",
        n_repeats=2,
        stratify=False,  # No stratification for regression
        task_type="regression",
    )

    assert len(samples[100]) == 2
    assert len(samples[100][0]) == 100
