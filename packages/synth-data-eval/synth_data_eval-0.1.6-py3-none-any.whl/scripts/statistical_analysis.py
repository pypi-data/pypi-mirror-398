"""Statistical analysis of benchmark results."""

import glob
import warnings
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import scipy.stats as stats

warnings.filterwarnings("ignore")


class StatisticalAnalyzer:
    """Perform statistical analysis on benchmark results."""

    def __init__(self, results_dir: str = "results/raw"):
        """
        Initialize statistical analyzer.

        Parameters
        ----------
        results_dir : str
            Directory containing results CSV files
        """
        self.results_dir = Path(results_dir)
        self.all_results_df = self._load_all_results()
        self.analysis_results: Dict[str, Any] = {}

    def _load_all_results(self) -> pd.DataFrame:
        """Load and combine all results files."""
        all_files = glob.glob(str(self.results_dir / "results_*.csv"))

        if not all_files:
            raise FileNotFoundError(f"No results files found in {self.results_dir}")

        dfs = []
        for file in all_files:
            try:
                df = pd.read_csv(file)
                dfs.append(df)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")

        if not dfs:
            raise ValueError("No valid results files could be loaded")

        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"Loaded {len(combined_df)} total runs from {len(dfs)} files")
        return combined_df

    def perform_statistical_tests(self) -> Dict:
        """Perform comprehensive statistical analysis."""
        print("Performing statistical analysis...")

        results = {
            "summary_stats": self._compute_summary_statistics(),
            "significance_tests": self._perform_significance_tests(),
            "confidence_intervals": self._compute_confidence_intervals(),
            "effect_sizes": self._compute_effect_sizes(),
        }

        self.analysis_results = results
        return results

    def _compute_summary_statistics(self) -> Dict:
        """Compute summary statistics for each metric by dataset and generator."""
        summary_stats: Dict[str, Any] = {}

        # Key metrics to analyze
        key_metrics = [
            "sdm_ks_complement_mean",
            "sdm_correlation_similarity",
            "ml_utility_ratio",
            "training_time",
            "privacy_dcr",
        ]

        for dataset in self.all_results_df["dataset"].unique():
            dataset_data = self.all_results_df[self.all_results_df["dataset"] == dataset]
            summary_stats[dataset] = {}

            for metric in key_metrics:
                if metric in dataset_data.columns:
                    metric_data = (
                        dataset_data.groupby("generator")[metric]
                        .agg(["count", "mean", "std", "min", "max", "median"])
                        .round(4)
                    )
                    summary_stats[dataset][metric] = metric_data

        return summary_stats

    def _perform_significance_tests(self) -> Dict:
        """Perform statistical significance tests between generators."""
        significance_results: Dict[str, Any] = {}

        # Key metrics for testing
        test_metrics = [
            "sdm_ks_complement_mean",
            "sdm_correlation_similarity",
            "ml_utility_ratio",
            "training_time",
        ]

        generators = self.all_results_df["generator"].unique()

        for dataset in self.all_results_df["dataset"].unique():
            dataset_data = self.all_results_df[self.all_results_df["dataset"] == dataset]
            significance_results[dataset] = {}

            for metric in test_metrics:
                if metric in dataset_data.columns and len(dataset_data[metric].dropna()) > 0:
                    significance_results[dataset][metric] = {}

                    # Perform pairwise t-tests
                    for i, gen1 in enumerate(generators):
                        for j, gen2 in enumerate(generators):
                            if i < j:  # Avoid duplicate comparisons
                                data1 = dataset_data[dataset_data["generator"] == gen1][
                                    metric
                                ].dropna()
                                data2 = dataset_data[dataset_data["generator"] == gen2][
                                    metric
                                ].dropna()

                                if len(data1) >= 2 and len(data2) >= 2:
                                    # Perform t-test
                                    ttest_result = stats.ttest_ind(data1, data2, equal_var=False)
                                    t_stat, p_value = ttest_result

                                    # Effect size (Cohen's d)
                                    mean_diff = data1.mean() - data2.mean()
                                    pooled_std = np.sqrt((data1.std() ** 2 + data2.std() ** 2) / 2)
                                    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

                                    significance_results[dataset][metric][f"{gen1}_vs_{gen2}"] = {
                                        "t_statistic": round(t_stat, 4),
                                        "p_value": round(p_value, 4),
                                        "significant": p_value < 0.05,
                                        "cohens_d": round(cohens_d, 4),
                                        "mean_diff": round(mean_diff, 4),
                                    }

        return significance_results

    def _compute_confidence_intervals(self, confidence: float = 0.95) -> Dict:
        """Compute confidence intervals for key metrics."""
        ci_results: Dict[str, Any] = {}

        key_metrics = [
            "sdm_ks_complement_mean",
            "sdm_correlation_similarity",
            "ml_utility_ratio",
            "training_time",
        ]

        for dataset in self.all_results_df["dataset"].unique():
            dataset_data = self.all_results_df[self.all_results_df["dataset"] == dataset]
            ci_results[dataset] = {}

            for metric in key_metrics:
                if metric in dataset_data.columns:
                    ci_results[dataset][metric] = {}

                    for generator in dataset_data["generator"].unique():
                        gen_data = dataset_data[dataset_data["generator"] == generator][
                            metric
                        ].dropna()

                        if len(gen_data) >= 2:
                            mean_val = gen_data.mean()
                            sem = stats.sem(gen_data)  # Standard error of the mean
                            ci_lower, ci_upper = stats.t.interval(
                                confidence, len(gen_data) - 1, loc=mean_val, scale=sem
                            )

                            ci_results[dataset][metric][generator] = {
                                "mean": round(mean_val, 4),
                                "ci_lower": round(ci_lower, 4),
                                "ci_upper": round(ci_upper, 4),
                                "ci_width": round(ci_upper - ci_lower, 4),
                                "n_samples": len(gen_data),
                            }

        return ci_results

    def _compute_effect_sizes(self) -> Dict:
        """Compute effect sizes between generators."""
        effect_sizes: Dict[str, Any] = {}

        key_metrics = [
            "sdm_ks_complement_mean",
            "sdm_correlation_similarity",
            "ml_utility_ratio",
            "training_time",
        ]

        for dataset in self.all_results_df["dataset"].unique():
            dataset_data = self.all_results_df[self.all_results_df["dataset"] == dataset]
            effect_sizes[dataset] = {}

            generators = dataset_data["generator"].unique()
            if len(generators) == 0:
                continue

            for metric in key_metrics:
                if metric in dataset_data.columns:
                    effect_sizes[dataset][metric] = {}

                    generators = dataset_data["generator"].unique()
                    baseline_gen = generators[0]  # Use first generator as baseline

                    baseline_data = dataset_data[dataset_data["generator"] == baseline_gen][
                        metric
                    ].dropna()

                    if len(baseline_data) > 0:
                        baseline_mean = baseline_data.mean()

                        for generator in generators[1:]:
                            gen_data = dataset_data[dataset_data["generator"] == generator][
                                metric
                            ].dropna()

                            if len(gen_data) > 0:
                                gen_mean = gen_data.mean()
                                relative_improvement = (
                                    (gen_mean - baseline_mean) / baseline_mean
                                ) * 100

                                effect_sizes[dataset][metric][f"{generator}_vs_{baseline_gen}"] = {
                                    "relative_improvement_pct": round(relative_improvement, 2),
                                    "absolute_difference": round(gen_mean - baseline_mean, 4),
                                }

        return effect_sizes

    def generate_latex_tables(self, output_dir: str = "results/tables") -> None:
        """Generate LaTeX tables for paper inclusion."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        # Generate summary statistics table
        self._generate_summary_table(output_path)

        # Generate significance test table
        self._generate_significance_table(output_path)

        print(f"LaTeX tables saved to {output_path}")

    def _generate_summary_table(self, output_path: Path) -> None:
        """Generate summary statistics LaTeX table."""
        if not self.analysis_results:
            self.perform_statistical_tests()

        summary_stats = self.analysis_results["summary_stats"]

        latex_content = """\\begin{table}[H]
\\centering
\\caption{Summary Statistics by Dataset and Generator}
\\label{tab:summary_stats}
\\begin{tabular}{@{}llcccccc@{}}
\\toprule
Dataset & Generator & Metric & Mean & Std & Min & Max & N \\\\
\\midrule
"""

        for dataset, dataset_stats in summary_stats.items():
            for metric, metric_stats in dataset_stats.items():
                metric_name = self._format_metric_name(metric)

                for generator in metric_stats.index:
                    stats_row = metric_stats.loc[generator]
                    generator_escaped = generator.replace("_", "\\_")
                    latex_content += f"{dataset} & {generator_escaped} & {metric_name} & {stats_row['mean']:.3f} & {stats_row['std']:.3f} & {stats_row['min']:.3f} & {stats_row['max']:.3f} & {int(stats_row['count'])} \\\\\n"  # noqa: E501

        latex_content += """\\bottomrule
\\end{tabular}
\\end{table}"""

        with open(output_path / "summary_statistics.tex", "w") as f:
            f.write(latex_content)

    def _generate_significance_table(self, output_path: Path) -> None:
        """Generate statistical significance LaTeX table."""
        if not self.analysis_results:
            self.perform_statistical_tests()

        sig_tests = self.analysis_results["significance_tests"]

        latex_content = """\\begin{table}[H]
\\centering
\\caption{Statistical Significance Tests (p-values)}
\\label{tab:significance_tests}
\\begin{tabular}{@{}llccc@{}}
\\toprule
Dataset & Metric & Comparison & p-value & Significant \\\\
\\midrule
"""

        for dataset, dataset_tests in sig_tests.items():
            for metric, metric_tests in dataset_tests.items():
                metric_name = self._format_metric_name(metric)

                for comparison, results in metric_tests.items():
                    gen1, gen2 = comparison.split("_vs_")
                    sig_symbol = "***" if results["significant"] else ""

                    gen1_escaped = gen1.replace("_", "\\_")
                    gen2_escaped = gen2.replace("_", "\\_")
                    latex_content += f"{dataset} & {metric_name} & {gen1_escaped} vs {gen2_escaped} & {results['p_value']:.3f}{sig_symbol} & {str(results['significant'])} \\\\\n"  # noqa: E501

        latex_content += """\\bottomrule
\\multicolumn{5}{l}{$^{***}p < 0.001, ^{**}p < 0.01, ^{*}p < 0.05$}
\\end{tabular}
\\end{table}"""

        with open(output_path / "significance_tests.tex", "w") as f:
            f.write(latex_content)

    def _format_metric_name(self, metric: str) -> str:
        """Format metric names for display."""
        name_map = {
            "sdm_ks_complement_mean": "KS Complement",
            "sdm_correlation_similarity": "Correlation Similarity",
            "ml_utility_ratio": "ML Utility Ratio",
            "training_time": "Training Time (s)",
            "privacy_dcr": "Privacy DCR",
        }
        return name_map.get(metric, metric.replace("_", " ").title())

    def save_results(self, output_path: str = "results/statistical_analysis.json") -> None:
        """Save analysis results to JSON file."""
        import json

        # Convert numpy types to native Python types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj

        serializable_results = convert_to_serializable(self.analysis_results)

        with open(output_path, "w") as f:
            json.dump(serializable_results, f, indent=2)

        print(f"Statistical analysis results saved to {output_path}")


def main():
    """Main execution function."""
    analyzer = StatisticalAnalyzer()

    # Perform analysis
    results = analyzer.perform_statistical_tests()

    # Generate LaTeX tables
    analyzer.generate_latex_tables()

    # Save results (skip DataFrames which aren't JSON serializable)
    # analyzer.save_results()

    # Print key findings
    print("\n=== Key Statistical Findings ===")

    sig_tests = results["significance_tests"]
    for dataset, dataset_tests in sig_tests.items():
        print(f"\n{str(dataset).upper()}:")
        for metric, metric_tests in dataset_tests.items():
            significant_comparisons = [
                comp for comp, res in metric_tests.items() if res["significant"]
            ]
            if significant_comparisons:
                metric_name = analyzer._format_metric_name(metric)
                print(f"  {metric_name}: {len(significant_comparisons)} significant differences")


if __name__ == "__main__":
    main()
