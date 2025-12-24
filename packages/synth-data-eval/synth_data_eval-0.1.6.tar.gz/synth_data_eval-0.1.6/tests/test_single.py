import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd  # noqa: E402

from evaluation.sdmetrics_evaluation import SDMetricsEvaluator  # noqa: E402
from generators.ctgan_model import CTGANGenerator  # noqa: E402


@pytest.mark.skipif(not Path("datasets/diabetes.csv").exists(), reason="Dataset not available")
def test_single_generator_workflow():
    """Test a single generator workflow with diabetes dataset."""
    # Load small dataset
    df = pd.read_csv("datasets/diabetes.csv")
    train_df = df.iloc[:300]  # Use smaller subset for quick testing
    test_df = df.iloc[300:400]

    print(f"Train: {train_df.shape}, Test: {test_df.shape}")

    # Generate with CTGAN (quick test with few epochs)
    gen = CTGANGenerator(epochs=5, verbose=False)  # Even fewer epochs for CI
    synthetic = gen.fit_generate(train_df, n_samples=100)

    # Basic validation
    assert synthetic.shape[0] == 100
    assert synthetic.shape[1] == train_df.shape[1]
    assert gen.is_fitted
    assert gen.training_time is not None
    assert gen.generation_time is not None

    # Evaluate synthetic data
    evaluator = SDMetricsEvaluator()
    results = evaluator.evaluate_all(train_df, synthetic)

    assert "quality_score" in results
    assert "column_shapes_score" in results
    assert "column_pair_trends_score" in results
    # Check that we have some statistical metrics
    assert len(results) > 10  # Should have quality scores + statistical + column metrics
