"""Meta-evaluation experiment runner.

Orchestrates progressive experiments across sample sizes to analyze
metric stability and TSTR correlations.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/meta_evaluation.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

from evaluation.metric_stability import MetricStabilityAnalyzer  # noqa: E402
from evaluation.ml_utility import MLUtilityEvaluator  # noqa: E402
from evaluation.privacy_metrics import PrivacyEvaluator  # noqa: E402
from evaluation.progressive_sampler import ProgressiveSampler  # noqa: E402
from evaluation.sdmetrics_evaluation import SDMetricsEvaluator  # noqa: E402
from evaluation.tstr_correlation import TSTRCorrelationAnalyzer  # noqa: E402
from generators.ctgan_model import CTGANGenerator  # noqa: E402
from generators.gaussian_copula import GaussianCopulaGenerator  # noqa: E402
from generators.smote_generator import SMOTEGenerator  # noqa: E402
from generators.tvae_model import TVAEGenerator  # noqa: E402


class MetaEvaluationRunner:
    """
    Run meta-evaluation experiments across sample sizes.

    This is the main orchestrator for the research framework.
    """

    def __init__(self, config_path: str = "scripts/config.yaml"):
        """
        Initialize meta-evaluation runner.

        Parameters
        ----------
        config_path : str
            Path to configuration file
        """
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.results_dir = Path(self.config["output"]["results_dir"])
        self.results_dir.mkdir(exist_ok=True, parents=True)

        # Create subdirectories for meta-evaluation
        (self.results_dir / "progressive").mkdir(exist_ok=True)
        (self.results_dir / "stability").mkdir(exist_ok=True)
        (self.results_dir / "correlations").mkdir(exist_ok=True)

        self.all_results: List[Dict] = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_progressive_experiments(
        self, dataset_names: Optional[List[str]] = None, generator_names: Optional[List[str]] = None
    ):
        """
        Run experiments across progressive sample sizes.

        Parameters
        ----------
        dataset_names : list of str, optional
            Specific datasets to run (None = all)
        generator_names : list of str, optional
            Specific generators to run (None = all)
        """
        logger.info("=" * 80)
        logger.info("STARTING META-EVALUATION EXPERIMENTS")
        logger.info("=" * 80)

        # Filter datasets and generators if specified
        datasets = self.config["datasets"]
        if dataset_names:
            datasets = {k: v for k, v in datasets.items() if k in dataset_names}

        generators = self.config["generators"]
        if generator_names:
            generators = {k: v for k, v in generators.items() if k in generator_names}

        logger.info(f"Datasets: {list(datasets.keys())}")
        logger.info(f"Generators: {list(generators.keys())}")

        # Get progressive sampling config
        prog_config = self.config.get("progressive_sampling", {})
        sample_sizes = prog_config.get("sample_sizes", [100, 500, 1000, 5000, 10000, 50000])
        n_repeats = prog_config.get("n_repeats_per_size", 10)

        logger.info(f"Sample sizes: {sample_sizes}")
        logger.info(f"Repeats per size: {n_repeats}")

        # Run experiments
        for dataset_name, dataset_config in datasets.items():
            logger.info(f"\n{'='*80}")
            logger.info(f"DATASET: {dataset_name}")
            logger.info(f"{'='*80}")

            try:
                self._run_dataset_progressive_experiments(
                    dataset_name=dataset_name,
                    dataset_config=dataset_config,
                    generators=generators,
                    sample_sizes=sample_sizes,
                    n_repeats=n_repeats,
                )
            except Exception as e:
                logger.error(f"Dataset {dataset_name} failed: {e}", exc_info=True)
                continue

        logger.info("\n" + "=" * 80)
        logger.info("ALL EXPERIMENTS COMPLETED")
        logger.info("=" * 80)

        # Save all results
        self._save_progressive_results()

        # Run meta-analyses
        self._analyze_metric_stability()
        self._analyze_tstr_correlations()

    def _run_dataset_progressive_experiments(
        self,
        dataset_name: str,
        dataset_config: Dict,
        generators: Dict,
        sample_sizes: List[int],
        n_repeats: int,
    ):
        """Run progressive experiments for a single dataset."""
        # Load full dataset
        logger.info(f"Loading dataset: {dataset_config['file']}")
        df = pd.read_csv(dataset_config["file"])
        logger.info(f"Full dataset size: {len(df)} samples")

        # Create progressive samples
        sampler = ProgressiveSampler(
            sample_sizes=sample_sizes,
            random_state=self.config["evaluation"]["random_seed"],
        )

        train_test_splits = sampler.create_train_test_split(
            data=df,
            target_col=dataset_config["target"],
            test_size=dataset_config["test_size"],
            task_type=dataset_config["task"],
        )

        logger.info(f"Created samples for {len(train_test_splits)} sizes")

        # Run experiments for each sample size
        for sample_size, splits in train_test_splits.items():
            logger.info(f"\n{'-'*60}")
            logger.info(f"Sample size: {sample_size}")
            logger.info(f"{'-'*60}")

            for repeat_id, (train_df, test_df) in enumerate(splits):
                logger.info(f"Repeat {repeat_id + 1}/{len(splits)}")

                # Run generators on this sample
                for gen_name, gen_config in generators.items():
                    try:
                        result = self._run_single_progressive_experiment(
                            dataset_name=dataset_name,
                            dataset_config=dataset_config,
                            generator_name=gen_name,
                            generator_config=gen_config,
                            train_df=train_df,
                            test_df=test_df,
                            sample_size=sample_size,
                            repeat_id=repeat_id,
                        )
                        self.all_results.append(result)

                        # Save intermediate results
                        if len(self.all_results) % 10 == 0:
                            self._save_progressive_results()

                    except Exception as e:
                        logger.error(
                            f"Experiment failed (gen={gen_name}, "
                            f"size={sample_size}, repeat={repeat_id}): {e}",
                            exc_info=True,
                        )
                        continue

    def _run_single_progressive_experiment(
        self,
        dataset_name: str,
        dataset_config: Dict,
        generator_name: str,
        generator_config: Dict,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        sample_size: int,
        repeat_id: int,
    ) -> Dict:
        """Run a single experiment."""
        logger.info(
            f"  Running: {generator_name} "
            f"(dataset={dataset_name}, size={sample_size}, repeat={repeat_id})"
        )

        # Initialize generator
        generator = self._get_generator(generator_name, generator_config)

        # Prepare metadata
        metadata = {"discrete_columns": dataset_config.get("discrete_columns", [])}

        # Add target column for SMOTE
        if generator_name == "smote":
            metadata["target_column"] = dataset_config["target"]

        # Generate synthetic data
        n_samples = len(train_df)
        logger.info(f"  Generating {n_samples} synthetic samples...")

        try:
            synthetic_df = generator.fit_generate(train_df, n_samples=n_samples, metadata=metadata)
        except Exception as e:
            logger.error(f"  Generation failed: {e}")
            # Return minimal results
            return {
                "dataset": dataset_name,
                "generator": generator_name,
                "sample_size": sample_size,
                "repeat_id": repeat_id,
                "generation_failed": True,
                "error": str(e),
            }

        logger.info(f"  Generated {len(synthetic_df)} samples")

        # Collect results
        results = {
            "dataset": dataset_name,
            "generator": generator_name,
            "sample_size": sample_size,
            "repeat_id": repeat_id,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "synthetic_size": len(synthetic_df),
            "training_time": generator.training_time,
            "generation_time": generator.generation_time,
            "generation_failed": False,
        }

        # Run evaluations
        try:
            # SDMetrics
            sdm_eval = SDMetricsEvaluator()
            sdm_results = sdm_eval.evaluate_all(train_df, synthetic_df, metadata)
            results.update({f"sdm_{k}": v for k, v in sdm_results.items()})
        except Exception as e:
            logger.warning(f"  SDMetrics evaluation failed: {e}")

        try:
            # ML Utility
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
        except Exception as e:
            logger.warning(f"  ML Utility evaluation failed: {e}")

        try:
            # Privacy
            privacy_eval = PrivacyEvaluator()
            privacy_results = privacy_eval.evaluate(
                train_df,
                synthetic_df,
                sensitive_columns=dataset_config.get("sensitive_columns", []),
            )
            results.update({f"privacy_{k}": v for k, v in privacy_results.items()})
        except Exception as e:
            logger.warning(f"  Privacy evaluation failed: {e}")

        logger.info("  Experiment completed successfully")
        return results

    def _get_generator(self, generator_name: str, generator_config: Dict):
        """Instantiate generator."""
        class_name = generator_config["class"]
        params = generator_config["params"]

        if class_name == "CTGANGenerator":
            return CTGANGenerator(**params)
        elif class_name == "TVAEGenerator":
            return TVAEGenerator(**params)
        elif class_name == "GaussianCopulaGenerator":
            return GaussianCopulaGenerator(**params)
        elif class_name == "SMOTEGenerator":
            return SMOTEGenerator(**params)
        else:
            raise ValueError(f"Unknown generator: {class_name}")

    def _save_progressive_results(self):
        """Save progressive experiment results."""
        if not self.all_results:
            return

        results_df = pd.DataFrame(self.all_results)
        output_path = self.results_dir / "progressive" / f"progressive_results_{self.timestamp}.csv"
        results_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(results_df)} results to {output_path}")

    def _analyze_metric_stability(self):
        """Analyze metric stability across sample sizes."""
        logger.info("\n" + "=" * 80)
        logger.info("ANALYZING METRIC STABILITY")
        logger.info("=" * 80)

        if not self.all_results:
            logger.warning("No results to analyze")
            return

        results_df = pd.DataFrame(self.all_results)

        # Filter out failed generations
        results_df = results_df[results_df["generation_failed"] == False]

        analyzer = MetricStabilityAnalyzer()

        # Group by dataset, generator, and sample size
        grouped = results_df.groupby(["dataset", "generator", "sample_size"])

        stability_results = []

        # Analyze each metric
        metric_cols = [
            col
            for col in results_df.columns
            if (col.startswith("sdm_") or col.startswith("ml_") or col.startswith("privacy_"))
            and col not in ["dataset", "generator", "sample_size", "repeat_id"]
        ]

        for (dataset, generator, sample_size), group in grouped:
            for metric_col in metric_cols:
                if metric_col in group.columns:
                    values = group[metric_col].dropna().tolist()
                    if values:
                        stability = analyzer.compute_stability_metrics(values, metric_col)
                        stability.update(
                            {
                                "dataset": dataset,
                                "generator": generator,
                                "sample_size": sample_size,
                                "metric": metric_col,
                            }
                        )
                        stability_results.append(stability)

        # Save stability results
        stability_df = pd.DataFrame(stability_results)
        output_path = self.results_dir / "stability" / f"stability_analysis_{self.timestamp}.csv"
        stability_df.to_csv(output_path, index=False)
        logger.info(f"Saved stability analysis to {output_path}")

        # Identify unstable metrics
        unstable = analyzer.identify_unstable_metrics(stability_df, cv_threshold=0.3)
        logger.info(f"\nFound {len(unstable)} unstable metric configurations:")
        logger.info(f"Top 10 most unstable (by CV):")
        top_unstable = unstable.nlargest(10, "cv")
        for _, row in top_unstable.iterrows():
            logger.info(
                f"  {row['metric']} @ {row['sample_size']} samples: "
                f"CV={row['cv']:.3f}, mean={row['mean']:.3f}"
            )

    def _analyze_tstr_correlations(self):
        """Analyze TSTR correlations."""
        logger.info("\n" + "=" * 80)
        logger.info("ANALYZING TSTR CORRELATIONS")
        logger.info("=" * 80)

        if not self.all_results:
            logger.warning("No results to analyze")
            return

        results_df = pd.DataFrame(self.all_results)
        results_df = results_df[results_df["generation_failed"] == False]

        analyzer = TSTRCorrelationAnalyzer(correlation_method="spearman")

        # Group by dataset and sample size
        grouped = results_df.groupby(["dataset", "sample_size"])

        correlation_results = {}

        for (dataset, sample_size), group in grouped:
            # Get TSTR scores
            tstr_col = "ml_utility_ratio"
            if tstr_col not in group.columns or group[tstr_col].isna().all():
                logger.warning(f"No TSTR scores for {dataset} @ {sample_size}. Skipping.")
                continue

            tstr_scores = group[tstr_col]

            # Get all metric columns
            metric_cols = [
                col
                for col in group.columns
                if (col.startswith("sdm_") or col.startswith("privacy_"))
                and not col.endswith("_mean_diff")
                and not col.endswith("_std_ratio")
            ]

            metric_scores = group[metric_cols]

            # Compute correlations
            correlations = analyzer.compute_metric_utility_correlation(
                metric_scores, tstr_scores, min_samples=3
            )

            key = (dataset, sample_size)
            correlation_results[key] = correlations

            logger.info(f"\n{dataset} @ {sample_size} samples: " f"Top 5 correlations with TSTR:")
            if not correlations.empty:
                for _, row in correlations.head(5).iterrows():
                    logger.info(
                        f"  {row['metric']}: ρ={row['correlation']:.3f} "
                        f"(p={row['p_value']:.4f})"
                    )

        # Save correlation results
        for (dataset, sample_size), corr_df in correlation_results.items():
            output_path = (
                self.results_dir
                / "correlations"
                / f"correlations_{dataset}_{sample_size}_{self.timestamp}.csv"
            )
            corr_df.to_csv(output_path, index=False)

        logger.info(f"\nSaved correlation analyses to {self.results_dir / 'correlations'}")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Run meta-evaluation experiments")
    parser.add_argument("--config", default="scripts/config.yaml", help="Path to config file")
    parser.add_argument("--datasets", nargs="+", help="Specific datasets to run (optional)")
    parser.add_argument("--generators", nargs="+", help="Specific generators to run (optional)")

    args = parser.parse_args()

    runner = MetaEvaluationRunner(config_path=args.config)
    runner.run_progressive_experiments(dataset_names=args.datasets, generator_names=args.generators)


if __name__ == "__main__":
    main()
