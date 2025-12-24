"""Main benchmark execution script."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/benchmark.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# AGGRESSIVE RELOAD - Remove cached module first
if "evaluation.sdmetrics_evaluation" in sys.modules:
    del sys.modules["evaluation.sdmetrics_evaluation"]
    logger.info("Removed cached sdmetrics_evaluation module")

from evaluation.ml_utility import MLUtilityEvaluator  # noqa: E402
from evaluation.privacy_metrics import PrivacyEvaluator  # noqa: E402

# Now import fresh
from evaluation.sdmetrics_evaluation import SDMetricsEvaluator  # noqa: E402
from generators.ctgan_model import CTGANGenerator  # noqa: E402
from generators.gaussian_copula import GaussianCopulaGenerator  # noqa: E402
from generators.kan_ctgan_model import KAN_CTGAN_Generator  # noqa: E402
from generators.kan_tvae_model import KAN_TVAE_Generator  # noqa: E402
from generators.tvae_model import TVAEGenerator  # noqa: E402


class BenchmarkRunner:
    """Run comprehensive benchmark experiments."""

    def __init__(self, config_path: str = "scripts/config.yaml"):
        """Initialize benchmark runner."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.results_dir = Path(self.config["output"]["results_dir"])
        self.results_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.results_dir / "figures").mkdir(exist_ok=True)
        (self.results_dir / "tables").mkdir(exist_ok=True)
        (self.results_dir / "raw").mkdir(exist_ok=True)

        Path("logs").mkdir(exist_ok=True)

        self.all_results: List[Dict] = []

    def load_dataset(self, dataset_config: Dict) -> tuple:
        """Load and split dataset."""
        logger.info(f"Loading dataset: {dataset_config['file']}")

        df = pd.read_csv(dataset_config["file"])

        # Split train/test
        from sklearn.model_selection import train_test_split

        target = dataset_config["target"]
        test_size = dataset_config["test_size"]

        if dataset_config["task"] == "classification":
            stratify = df[target]
        else:
            stratify = None

        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=self.config["evaluation"]["random_seed"],
            stratify=stratify,
        )

        logger.info(f"Train: {train_df.shape}, Test: {test_df.shape}")

        return train_df, test_df

    def get_generator(self, generator_name: str, generator_config: Dict):
        """Instantiate generator."""
        class_name = generator_config["class"]
        params = generator_config["params"]

        if class_name == "CTGANGenerator":
            return CTGANGenerator(**params)
        elif class_name == "TVAEGenerator":
            return TVAEGenerator(**params)
        elif class_name == "KAN_CTGAN_Generator":
            return KAN_CTGAN_Generator(**params)
        elif class_name == "KAN_TVAE_Generator":
            return KAN_TVAE_Generator(**params)
        elif class_name == "GaussianCopulaGenerator":
            return GaussianCopulaGenerator(**params)
        else:
            raise ValueError(f"Unknown generator: {class_name}")

    def run_single_experiment(
        self,
        dataset_name: str,
        dataset_config: Dict,
        generator_name: str,
        generator_config: Dict,
        run_id: int,
    ) -> Dict:
        """Run single experiment."""
        logger.info(f"\n{'='*60}")
        logger.info(
            (f"Dataset: {dataset_name} | " f"Generator: {generator_name} | " f"Run: {run_id}")
        )
        logger.info(f"{'='*60}")

        # Load data
        train_df, test_df = self.load_dataset(dataset_config)

        # Initialize generator
        generator = self.get_generator(generator_name, generator_config)

        # Prepare metadata
        metadata = {"discrete_columns": dataset_config.get("discrete_columns", [])}

        # Generate synthetic data
        n_samples = self.config["evaluation"]["n_synthetic_samples"]
        if n_samples is None:
            n_samples = len(train_df)

        logger.info(f"Generating {n_samples} synthetic samples...")
        synthetic_df = generator.fit_generate(train_df, n_samples=n_samples, metadata=metadata)
        logger.info(f"Synthetic data shape: {synthetic_df.shape}")

        # Collect results
        results = {
            "dataset": dataset_name,
            "generator": generator_name,
            "run_id": run_id,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "synthetic_size": len(synthetic_df),
            "training_time": generator.training_time,
            "generation_time": generator.generation_time,
        }

        # Run evaluations
        if "sdmetrics" in self.config["evaluation"]["metrics"]:
            logger.info("Running SDMetrics evaluation...")
            sdm_eval = SDMetricsEvaluator()
            sdm_results = sdm_eval.evaluate_all(train_df, synthetic_df, metadata)
            results.update({f"sdm_{k}": v for k, v in sdm_results.items()})

        if "ml_utility" in self.config["evaluation"]["metrics"]:
            logger.info("Running ML Utility evaluation...")
            ml_eval = MLUtilityEvaluator(
                task_type=dataset_config["task"],
                random_state=self.config["evaluation"]["random_seed"],
            )
            ml_results = ml_eval.evaluate(
                train_df, test_df, synthetic_df, target_col=dataset_config["target"]
            )
            # Flatten nested results
            for key, value in ml_results.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        results[f"ml_{key}_{subkey}"] = subvalue
                else:
                    results[f"ml_{key}"] = value

        if "privacy" in self.config["evaluation"]["metrics"]:
            logger.info("Running Privacy evaluation...")
            privacy_eval = PrivacyEvaluator()
            privacy_results = privacy_eval.evaluate(
                train_df,
                synthetic_df,
                sensitive_columns=dataset_config.get("sensitive_columns", []),
            )
            results.update({f"privacy_{k}": v for k, v in privacy_results.items()})

        logger.info("Experiment completed successfully!")

        return results

    def run_all_experiments(self):
        """Run all experiments defined in config."""
        logger.info("Starting benchmark experiments...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Iterate over all combinations
        for dataset_name, dataset_config in self.config["datasets"].items():
            for generator_name, generator_config in self.config["generators"].items():
                for run_id in range(self.config["evaluation"]["n_runs"]):
                    try:
                        result = self.run_single_experiment(
                            dataset_name, dataset_config, generator_name, generator_config, run_id
                        )
                        self.all_results.append(result)

                        # Save intermediate results
                        self.save_results(timestamp)

                    except Exception as e:
                        logger.error(f"Experiment failed: {e}", exc_info=True)
                        continue

        logger.info("\n" + "=" * 60)
        logger.info("All experiments completed!")
        logger.info("=" * 60)

        return self.all_results

    def save_results(self, timestamp: str):
        """Save results to files."""
        if not self.all_results:
            return

        # Convert to DataFrame
        results_df = pd.DataFrame(self.all_results)

        # Save raw results
        results_df.to_csv(self.results_dir / "raw" / f"results_{timestamp}.csv", index=False)

        # Save summary statistics
        summary = self.create_summary(results_df)
        summary.to_csv(self.results_dir / "tables" / f"summary_{timestamp}.csv")

        logger.info(f"Results saved to {self.results_dir}")

    def create_summary(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """Create summary statistics."""
        # Group by dataset and generator
        grouped = results_df.groupby(["dataset", "generator"])

        # Aggregate key metrics
        agg_dict = {}
        for col in results_df.columns:
            if col not in ["dataset", "generator", "run_id"]:
                if pd.api.types.is_numeric_dtype(results_df[col]):
                    agg_dict[col] = ["mean", "std"]

        summary = grouped.agg(agg_dict)

        return summary


def main():
    """Main execution function."""
    runner = BenchmarkRunner()
    results = runner.run_all_experiments()

    logger.info(f"\nTotal experiments completed: {len(results)}")


if __name__ == "__main__":
    main()
