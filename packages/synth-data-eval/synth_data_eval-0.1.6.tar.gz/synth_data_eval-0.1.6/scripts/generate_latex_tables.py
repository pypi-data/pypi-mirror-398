"""Generate LaTeX tables from meta-evaluation results.

Creates publication-ready tables for:
- Metric stability summary
- TSTR correlation rankings
- Most unstable metrics per sample size
- Generator comparison
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaTeXTableGenerator:
    """Generate LaTeX tables from meta-evaluation results."""

    def __init__(self, results_dir: str = "results", output_dir: str = "results/tables"):
        """
        Initialize table generator.

        Parameters
        ----------
        results_dir : str
            Directory containing result CSV files
        output_dir : str
            Directory to save LaTeX tables
        """
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def generate_stability_summary_table(
        self,
        stability_df: pd.DataFrame,
        sample_size: int = 100,
        top_n: int = 10,
    ) -> str:
        """
        Generate LaTeX table summarizing most unstable metrics.

        Parameters
        ----------
        stability_df : pd.DataFrame
            Stability analysis results
        sample_size : int
            Sample size to focus on
        top_n : int
            Number of metrics to include

        Returns
        -------
        str
            LaTeX table code
        """
        logger.info(f"Generating stability summary table for n={sample_size}...")

        # Filter and sort
        filtered = stability_df[stability_df["sample_size"] == sample_size]
        top_unstable = filtered.nlargest(top_n, "cv")[
            ["metric", "mean", "std", "cv", "ci_lower", "ci_upper"]
        ]

        # Clean metric names
        top_unstable["metric"] = (
            top_unstable["metric"]
            .str.replace("sdm_", "")
            .str.replace("ml_", "")
            .str.replace("_", " ")
        )

        # Create LaTeX table
        latex = "\\begin{table}[h]\n"
        latex += "\\centering\n"
        latex += f"\\caption{{Top {top_n} Most Unstable Metrics at n={sample_size}}}\n"
        latex += "\\label{tab:stability_" + str(sample_size) + "}\n"
        latex += "\\begin{tabular}{lcccccc}\n"
        latex += "\\hline\n"
        latex += "\\textbf{Metric} & \\textbf{Mean} & \\textbf{Std} & \\textbf{CV} & \\textbf{CI Lower} & \\textbf{CI Upper} \\\\\n"
        latex += "\\hline\n"

        for _, row in top_unstable.iterrows():
            latex += f"{row['metric']} & "
            latex += f"{row['mean']:.3f} & "
            latex += f"{row['std']:.3f} & "
            latex += f"\\textbf{{{row['cv']:.3f}}} & "
            latex += f"{row['ci_lower']:.3f} & "
            latex += f"{row['ci_upper']:.3f} \\\\\n"

        latex += "\\hline\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"

        return latex

    def generate_tstr_correlation_table(
        self,
        correlations_df: pd.DataFrame,
        top_n: int = 10,
    ) -> str:
        """
        Generate LaTeX table of top TSTR-correlated metrics.

        Parameters
        ----------
        correlations_df : pd.DataFrame
            TSTR correlation results
        top_n : int
            Number of metrics to include

        Returns
        -------
        str
            LaTeX table code
        """
        logger.info("Generating TSTR correlation table...")

        # Sort by absolute correlation
        correlations_df["abs_corr"] = correlations_df["correlation"].abs()
        top_corr = correlations_df.nlargest(top_n, "abs_corr")[
            ["metric", "correlation", "p_value", "is_significant", "n_samples"]
        ]

        # Clean metric names
        top_corr["metric"] = (
            top_corr["metric"].str.replace("sdm_", "").str.replace("ml_", "").str.replace("_", " ")
        )

        # Create LaTeX table
        latex = "\\begin{table}[h]\n"
        latex += "\\centering\n"
        latex += f"\\caption{{Top {top_n} Metrics by TSTR Correlation}}\n"
        latex += "\\label{tab:tstr_correlation}\n"
        latex += "\\begin{tabular}{lcccc}\n"
        latex += "\\hline\n"
        latex += "\\textbf{Metric} & \\textbf{$\\rho$} & \\textbf{p-value} & \\textbf{Significant} & \\textbf{N} \\\\\n"
        latex += "\\hline\n"

        for _, row in top_corr.iterrows():
            sig_marker = "\\checkmark" if row["is_significant"] else ""
            latex += f"{row['metric']} & "
            latex += f"{row['correlation']:.3f} & "
            latex += f"{row['p_value']:.4f} & "
            latex += f"{sig_marker} & "
            latex += f"{int(row['n_samples'])} \\\\\n"

        latex += "\\hline\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"

        return latex

    def generate_cv_vs_samplesize_table(
        self,
        stability_df: pd.DataFrame,
        metric_name: str,
    ) -> str:
        """
        Generate table showing CV decrease across sample sizes for a metric.

        Parameters
        ----------
        stability_df : pd.DataFrame
            Stability analysis results
        metric_name : str
            Metric to analyze

        Returns
        -------
        str
            LaTeX table code
        """
        logger.info(f"Generating CV vs sample size table for {metric_name}...")

        metric_data = stability_df[stability_df["metric"] == metric_name].sort_values(
            "sample_size"
        )[["sample_size", "mean", "cv", "n_samples"]]

        if metric_data.empty:
            logger.warning(f"No data for metric: {metric_name}")
            return ""

        clean_name = metric_name.replace("sdm_", "").replace("ml_", "").replace("_", " ")

        latex = "\\begin{table}[h]\n"
        latex += "\\centering\n"
        latex += f"\\caption{{Stability of {clean_name} Across Sample Sizes}}\n"
        latex += "\\label{tab:cv_trend_" + metric_name.replace("_", "") + "}\n"
        latex += "\\begin{tabular}{cccc}\n"
        latex += "\\hline\n"
        latex += "\\textbf{Sample Size} & \\textbf{Mean} & \\textbf{CV} & \\textbf{N Runs} \\\\\n"
        latex += "\\hline\n"

        for _, row in metric_data.iterrows():
            latex += f"{int(row['sample_size'])} & "
            latex += f"{row['mean']:.3f} & "
            latex += f"{row['cv']:.3f} & "
            latex += f"{int(row['n_samples'])} \\\\\n"

        latex += "\\hline\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"

        return latex

    def generate_all_tables(self, timestamp: Optional[str] = None):
        """
        Generate all LaTeX tables from saved results.

        Parameters
        ----------
        timestamp : str, optional
            Timestamp of results to use (None = most recent)
        """
        logger.info("=" * 80)
        logger.info("GENERATING LATEX TABLES")
        logger.info("=" * 80)

        # Load stability results
        stability_files = list((self.results_dir / "stability").glob("stability_analysis_*.csv"))
        if not stability_files:
            logger.error("No stability analysis files found!")
            return

        if timestamp:
            stability_file = self.results_dir / "stability" / f"stability_analysis_{timestamp}.csv"
        else:
            stability_file = max(stability_files, key=lambda p: p.stat().st_mtime)

        logger.info(f"Loading stability results from: {stability_file}")
        stability_df = pd.read_csv(stability_file)

        all_latex = ""

        # 1. Stability summary for small n
        table1 = self.generate_stability_summary_table(stability_df, sample_size=100, top_n=10)
        all_latex += table1 + "\n\n"

        # 2. Load and generate TSTR correlation table
        corr_files = list((self.results_dir / "correlations").glob("correlations_*.csv"))
        if corr_files:
            # Use first file (or specify differently)
            corr_file = max(corr_files, key=lambda p: p.stat().st_mtime)
            correlations_df = pd.read_csv(corr_file)
            table2 = self.generate_tstr_correlation_table(correlations_df, top_n=10)
            all_latex += table2 + "\n\n"

        # 3. CV trend for most unstable metric
        most_unstable = stability_df.loc[stability_df["cv"].idxmax()]["metric"]
        table3 = self.generate_cv_vs_samplesize_table(stability_df, most_unstable)
        all_latex += table3 + "\n\n"

        # Save all tables
        output_file = self.output_dir / "latex_tables.tex"
        with open(output_file, "w") as f:
            f.write(all_latex)

        logger.info(f"\nAll LaTeX tables saved to: {output_file}")
        logger.info("=" * 80)

        # Also print to console
        print("\n" + "=" * 80)
        print("LATEX TABLES (copy to your paper)")
        print("=" * 80)
        print(all_latex)
        print("=" * 80)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate LaTeX tables")
    parser.add_argument("--results-dir", default="results", help="Directory containing results")
    parser.add_argument("--output-dir", default="results/tables", help="Directory to save tables")
    parser.add_argument("--timestamp", default=None, help="Specific result timestamp to use")

    args = parser.parse_args()

    generator = LaTeXTableGenerator(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
    )

    generator.generate_all_tables(timestamp=args.timestamp)


if __name__ == "__main__":
    main()
