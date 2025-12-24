"""Tests for synthetic data generators."""

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_regression

from generators.base_generator import BaseGenerator
from generators.ctgan_model import CTGANGenerator
from generators.gaussian_copula import GaussianCopulaGenerator
from generators.kan_ctgan_model import KAN_CTGAN_Generator
from generators.kan_tvae_model import KAN_TVAE_Generator
from generators.tvae_model import TVAEGenerator


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
def regression_data():
    """Create regression data for testing."""
    X, y = make_regression(n_samples=100, n_features=5, noise=0.1, random_state=42)
    data = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(5)])
    data["target"] = y
    return data


class TestBaseGenerator:
    """Test the abstract base generator."""

    def test_abstract_methods(self):
        """Test that BaseGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseGenerator("test", 42)

    def test_initialization(self, sample_data):
        """Test generator initialization."""
        gen = CTGANGenerator(epochs=1, verbose=False)
        assert gen.name == "CTGAN"
        assert gen.random_state == 42
        assert not gen.is_fitted
        assert gen.training_time is None
        assert gen.generation_time is None

    def test_fit_generate(self, sample_data):
        """Test the fit_generate convenience method."""
        gen = GaussianCopulaGenerator(random_state=42)

        # Should work without fitting first
        synthetic = gen.fit_generate(sample_data, n_samples=50)

        assert isinstance(synthetic, pd.DataFrame)
        assert len(synthetic) == 50
        assert list(synthetic.columns) == list(sample_data.columns)
        assert gen.is_fitted
        assert gen.training_time is not None
        assert gen.generation_time is not None

    def test_get_metadata(self, sample_data):
        """Test metadata retrieval."""
        gen = GaussianCopulaGenerator(random_state=42)
        gen.fit_generate(sample_data, n_samples=50)

        metadata = gen.get_metadata()
        assert isinstance(metadata, dict)
        assert "name" in metadata
        assert "training_time" in metadata
        assert "generation_time" in metadata
        assert "is_fitted" in metadata


class TestCTGANGenerator:
    """Test CTGAN generator."""

    def test_initialization(self):
        """Test CTGAN initialization with custom parameters."""
        gen = CTGANGenerator(
            epochs=5,
            batch_size=100,
            generator_dim=(64, 64),
            discriminator_dim=(64, 64),
            random_state=42,
            verbose=False,
        )
        assert gen.epochs == 5
        assert gen.batch_size == 100
        assert not gen.verbose

    def test_fit_and_generate(self, sample_data):
        """Test CTGAN fit and generate separately."""
        gen = CTGANGenerator(epochs=1, verbose=False)

        # Fit
        gen.fit(sample_data)
        assert gen.is_fitted

        # Generate
        synthetic = gen.generate(n_samples=50)
        assert isinstance(synthetic, pd.DataFrame)
        assert len(synthetic) == 50
        assert list(synthetic.columns) == list(sample_data.columns)

    def test_fit_with_metadata(self, sample_data):
        """Test CTGAN fit with discrete columns metadata."""
        gen = CTGANGenerator(epochs=1, verbose=False)

        metadata = {"discrete_columns": ["cat1", "cat2"]}
        gen.fit(sample_data, metadata)

        assert gen.is_fitted
        assert gen.discrete_columns == ["cat1", "cat2"]

    def test_generate_without_fit_raises_error(self, sample_data):
        """Test that generate raises error when not fitted."""
        gen = CTGANGenerator(epochs=1, verbose=False)

        with pytest.raises(ValueError, match="Model must be fitted"):
            gen.generate(n_samples=50)


class TestTVAEGenerator:
    """Test TVAE generator."""

    def test_initialization(self):
        """Test TVAE initialization."""
        gen = TVAEGenerator(
            epochs=3,
            batch_size=50,
            compress_dims=(64, 32),
            decompress_dims=(32, 64),
            random_state=42,
            verbose=False,
        )
        assert gen.epochs == 3
        assert gen.batch_size == 50
        assert not gen.verbose

    def test_fit_and_generate(self, sample_data):
        """Test TVAE fit and generate."""
        gen = TVAEGenerator(epochs=1, verbose=False)

        gen.fit(sample_data)
        assert gen.is_fitted

        synthetic = gen.generate(n_samples=30)
        assert isinstance(synthetic, pd.DataFrame)
        assert len(synthetic) == 30
        assert list(synthetic.columns) == list(sample_data.columns)

    def test_auto_detect_categorical(self, sample_data):
        """Test automatic categorical column detection."""
        gen = TVAEGenerator(epochs=1, verbose=False)

        gen.fit(sample_data)
        # Should have detected categorical columns
        assert isinstance(gen.discrete_columns, list)
        assert len(gen.discrete_columns) > 0


class TestGaussianCopulaGenerator:
    """Test Gaussian Copula generator."""

    def test_initialization(self):
        """Test Gaussian Copula initialization."""
        gen = GaussianCopulaGenerator(default_distribution="beta", random_state=42)
        assert gen.default_distribution == "beta"
        assert gen.random_state == 42

    def test_fit_and_generate(self, sample_data):
        """Test Gaussian Copula fit and generate."""
        gen = GaussianCopulaGenerator(random_state=42)

        gen.fit(sample_data)
        assert gen.is_fitted
        assert gen.metadata is not None
        assert gen.model is not None

        synthetic = gen.generate(n_samples=75)
        assert isinstance(synthetic, pd.DataFrame)
        assert len(synthetic) == 75
        assert list(synthetic.columns) == list(sample_data.columns)

    def test_different_distributions(self, sample_data):
        """Test different default distributions."""
        for dist in ["beta", "norm", "gamma"]:
            gen = GaussianCopulaGenerator(default_distribution=dist, random_state=42)
            gen.fit(sample_data)
            synthetic = gen.generate(n_samples=25)
            assert len(synthetic) == 25


class TestGeneratorIntegration:
    """Integration tests for generators."""

    @pytest.mark.parametrize(
        "generator_class,kwargs",
        [
            (CTGANGenerator, {"epochs": 1, "verbose": False}),
            (TVAEGenerator, {"epochs": 1, "verbose": False}),
            (KAN_CTGAN_Generator, {"epochs": 1, "verbose": False}),
            (KAN_TVAE_Generator, {"epochs": 1, "verbose": False}),
            (GaussianCopulaGenerator, {"random_state": 42}),
        ],
    )
    def test_all_generators_basic_workflow(self, generator_class, kwargs, sample_data):
        """Test basic workflow for all generators."""
        gen = generator_class(**kwargs)

        # Fit and generate
        synthetic = gen.fit_generate(sample_data, n_samples=50)

        # Assertions
        assert isinstance(synthetic, pd.DataFrame)
        assert len(synthetic) == 50
        assert list(synthetic.columns) == list(sample_data.columns)
        assert gen.is_fitted
        assert gen.training_time > 0
        assert gen.generation_time > 0

    def test_generator_output_shapes(self, sample_data):
        """Test that generated data has correct shapes."""
        gen = GaussianCopulaGenerator(random_state=42)
        synthetic = gen.fit_generate(sample_data, n_samples=200)

        # Check numerical columns have reasonable distributions
        for col in synthetic.select_dtypes(include=[np.number]).columns:
            assert not synthetic[col].isnull().all()
            assert synthetic[col].std() > 0  # Has variance

    def test_reproducibility(self, sample_data):
        """Test that generators are reproducible with same random state."""
        gen1 = GaussianCopulaGenerator(random_state=42)
        gen2 = GaussianCopulaGenerator(random_state=42)

        synth1 = gen1.fit_generate(sample_data, n_samples=50)
        synth2 = gen2.fit_generate(sample_data, n_samples=50)

        # Should be identical (deterministic)
        pd.testing.assert_frame_equal(synth1, synth2)
