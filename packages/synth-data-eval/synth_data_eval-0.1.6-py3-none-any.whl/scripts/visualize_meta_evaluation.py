"""Visualization scripts for meta-evaluation results.

Creates publication-ready plots:
- Metric stability vs sample size
- TSTR correlation heatmaps
- Confidence interval ribbons
- Domain-stratified analyses
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set publication-quality style
plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.size"] = 10
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["legend.fontsize"] = 9


class MetaEvaluationVisualizer:
    """Create publication-ready visualizations for meta-evaluation results."""

    def __init__(self, results_dir: str = "results", output_dir: str = "results/figures"):
        """
        Initialize visualizer.

        Parameters
        ----------
        results_dir : str
            Directory containing result CSV files
        output_dir : str
            Directory to save figures
        """
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def plot_metric_stability_trends(
        self,
        stability_df: pd.DataFrame,
        metrics_to_plot: Optional[List[str]] = None,
        dataset_filter: Optional[str] = None,
    ):
        """
        Plot metric stability (CV) vs sample size.

        Parameters
        ----------
        stability_df : pd.DataFrame
            Stability analysis results
        metrics_to_plot : list of str, optional
            Specific metrics to plot (None = all)
        dataset_filter : str, optional
            Filter to specific dataset
        """
        logger.info("Creating metric stability trends plot...")

        if dataset_filter:
            stability_df = stability_df[stability_df["dataset"] == dataset_filter]

        # Group by metric and sample size
        grouped = stability_df.groupby(["metric", "sample_size"])["cv"].mean().reset_index()

        # Select metrics to plot
        if metrics_to_plot is None:
            # Plot top 10 most unstable metrics
            avg_cv = grouped.groupby("metric")["cv"].mean().sort_values(ascending=False)
            metrics_to_plot = avg_cv.head(10).index.tolist()

        filtered = grouped[grouped["metric"].isin(metrics_to_plot)]

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        for metric in metrics_to_plot:
            metric_data = filtered[filtered["metric"] == metric]
            ax.plot(
                metric_data["sample_size"],
                metric_data["cv"],
                marker="o",
                label=metric.replace("sdm_", "").replace("ml_", "").replace("privacy_", ""),
                linewidth=2,
                markersize=6,
            )

        # Add stability threshold line
        ax.axhline(
            y=0.3, color="red", linestyle="--", linewidth=2, label="Instability Threshold (CV=0.3)"
        )

        ax.set_xlabel("Sample Size", fontweight="bold")
        ax.set_ylabel("Coefficient of Variation (CV)", fontweight="bold")
        ax.set_title("Metric Stability vs Sample Size", fontweight="bold", fontsize=14)
        ax.set_xscale("log")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", frameon=True)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        output_path = self.output_dir / "metric_stability_trends.png"
        plt.savefig(output_path, bbox_inches="tight")
        logger.info(f"Saved to {output_path}")
        plt.close()

    def plot_tstr_correlation_heatmap(
        self,
        correlations_by_size: Dict[int, pd.DataFrame],
        top_n_metrics: int = 15,
    ):
        """
        Create heatmap of metric-TSTR correlations across sample sizes.

        Parameters
        ----------
        correlations_by_size : dict
            Mapping of sample_size -> correlation DataFrame
        top_n_metrics : int
            Number of top metrics to display
        """
        logger.info("Creating TSTR correlation heatmap...")

        # Build pivot table
        data_for_pivot = []
        for sample_size, corr_df in correlations_by_size.items():
            for _, row in corr_df.iterrows():
                data_for_pivot.append(
                    {
                        "metric": row["metric"],
                        "sample_size": sample_size,
                        "correlation": row["correlation"],
                    }
                )

        pivot_df = pd.DataFrame(data_for_pivot)
        heatmap_data = pivot_df.pivot(index="metric", columns="sample_size", values="correlation")

        # Select top metrics by average absolute correlation
        heatmap_data["mean_abs_corr"] = heatmap_data.abs().mean(axis=1)
        heatmap_data = heatmap_data.sort_values("mean_abs_corr", ascending=False)
        heatmap_data = heatmap_data.drop(columns=["mean_abs_corr"]).head(top_n_metrics)

        # Clean metric names
        heatmap_data.index = (
            heatmap_data.index.str.replace("sdm_", "")
            .str.replace("ml_", "")
            .str.replace("privacy_", "")
        )

        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt=".2f",
            cmap="RdYlGn",
            center=0,
            vmin=-1,
            vmax=1,
            cbar_kws={"label": "Spearman Correlation (ρ)"},
            linewidths=0.5,
            ax=ax,
        )

        ax.set_xlabel("Sample Size", fontweight="bold")
        ax.set_ylabel("Quality Metric", fontweight="bold")
        ax.set_title("Metric-TSTR Correlation Across Sample Sizes", fontweight="bold", fontsize=14)

        plt.tight_layout()
        output_path = self.output_dir / "tstr_correlation_heatmap.png"
        plt.savefig(output_path, bbox_inches="tight")
        logger.info(f"Saved to {output_path}")
        plt.close()

    def plot_confidence_intervals(
        self,
        stability_df: pd.DataFrame,
        metric_name: str,
        dataset_filter: Optional[str] = None,
    ):
        """
        Plot metric values with confidence interval ribbons.

        Parameters
        ----------
        stability_df : pd.DataFrame
            Stability analysis results
        metric_name : str
            Metric to plot
        dataset_filter : str, optional
            Filter to specific dataset
        """
        logger.info(f"Creating confidence interval plot for {metric_name}...")

        if dataset_filter:
            stability_df = stability_df[stability_df["dataset"] == dataset_filter]

        metric_data = stability_df[stability_df["metric"] == metric_name].sort_values("sample_size")

        if metric_data.empty:
            logger.warning(f"No data found for metric: {metric_name}")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot mean with CI ribbon
        ax.plot(
            metric_data["sample_size"],
            metric_data["mean"],
            marker="o",
            linewidth=2,
            markersize=8,
            color="steelblue",
            label="Mean",
        )

        ax.fill_between(
            metric_data["sample_size"],
            metric_data["ci_lower"],
            metric_data["ci_upper"],
            alpha=0.3,
            color="steelblue",
            label="95% Confidence Interval",
        )

        # Add IQR ribbon
        ax.fill_between(
            metric_data["sample_size"],
            metric_data["q25"],
            metric_data["q75"],
            alpha=0.2,
            color="orange",
            label="Interquartile Range",
        )

        ax.set_xlabel("Sample Size", fontweight="bold")
        ax.set_ylabel("Metric Value", fontweight="bold")
        ax.set_title(
            f'{metric_name.replace("sdm_", "").replace("ml_", "")} - Confidence Intervals',
            fontweight="bold",
            fontsize=14,
        )
        ax.set_xscale("log")
        ax.legend(frameon=True)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        safe_name = metric_name.replace("/", "_").replace(" ", "_")
        output_path = self.output_dir / f"ci_{safe_name}.png"
        plt.savefig(output_path, bbox_inches="tight")
        logger.info(f"Saved to {output_path}")
        plt.close()

    def plot_domain_stratified_analysis(
        self,
        stability_df: pd.DataFrame,
        domain_mapping: Dict[str, str],
    ):
        """
        Create faceted plots stratified by domain (Medical/Financial/Social).

        Parameters
        ----------
        stability_df : pd.DataFrame
            Stability analysis results
        domain_mapping : dict
            Mapping of dataset -> domain
        """
        logger.info("Creating domain-stratified analysis...")

        # Add domain column
        stability_df["domain"] = stability_df["dataset"].map(domain_mapping)
        stability_df = stability_df.dropna(subset=["domain"])

        domains = stability_df["domain"].unique()
        n_domains = len(domains)

        fig, axes = plt.subplots(1, n_domains, figsize=(15, 5), sharey=True)
        if n_domains == 1:
            axes = [axes]

        for idx, domain in enumerate(domains):
            domain_data = stability_df[stability_df["domain"] == domain]

            # Aggregate by sample size
            agg_data = domain_data.groupby("sample_size")["cv"].mean().reset_index()

            axes[idx].plot(
                agg_data["sample_size"],
                agg_data["cv"],
                marker="o",
                linewidth=2,
                markersize=8,
                color="steelblue",
            )
            axes[idx].axhline(y=0.3, color="red", linestyle="--", linewidth=2)
            axes[idx].set_xlabel("Sample Size", fontweight="bold")
            axes[idx].set_title(domain, fontweight="bold")
            axes[idx].set_xscale("log")
            axes[idx].grid(True, alpha=0.3)

            if idx == 0:
                axes[idx].set_ylabel("Mean CV", fontweight="bold")

        plt.suptitle("Metric Stability Across Domains", fontweight="bold", fontsize=14, y=1.02)
        plt.tight_layout()
        output_path = self.output_dir / "domain_stratified_stability.png"
        plt.savefig(output_path, bbox_inches="tight")
        logger.info(f"Saved to {output_path}")
        plt.close()

    def create_all_visualizations(self, timestamp: Optional[str] = None):
        """
        Generate all visualization types from saved results.

        Parameters
        ----------
        timestamp : str, optional
            Timestamp of results to visualize (None = most recent)
        """
        logger.info("=" * 80)
        logger.info("CREATING ALL VISUALIZATIONS")
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

        # 1. Metric stability trends
        self.plot_metric_stability_trends(stability_df)

        # 2. Load and plot TSTR correlations
        corr_files = list((self.results_dir / "correlations").glob("correlations_*.csv"))
        if corr_files:
            correlations_by_size = {}
            for corr_file in corr_files:
                # Extract sample size from filename
                parts = corr_file.stem.split("_")
                if len(parts) >= 3:
                    try:
                        sample_size = int(parts[2])
                        correlations_by_size[sample_size] = pd.read_csv(corr_file)
                    except ValueError:
                        continue

            if correlations_by_size:
                self.plot_tstr_correlation_heatmap(correlations_by_size)

        # 3. Confidence intervals for top unstable metrics
        top_unstable = stability_df.nlargest(5, "cv")["metric"].unique()
        for metric in top_unstable[:3]:  # Plot top 3
            self.plot_confidence_intervals(stability_df, metric)

        # 4. Domain-stratified analysis
        domain_mapping = {
            "iris": "Financial",
            "pima_diabetes": "Medical",
            "heart_disease": "Medical",
            "breast_cancer": "Medical",
            "german_credit": "Financial",
            "student_performance": "Social",
        }
        self.plot_domain_stratified_analysis(stability_df, domain_mapping)

        logger.info("=" * 80)
        logger.info(f"All visualizations saved to: {self.output_dir}")
        logger.info("=" * 80)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Create meta-evaluation visualizations")
    parser.add_argument("--results-dir", default="results", help="Directory containing results")
    parser.add_argument("--output-dir", default="results/figures", help="Directory to save figures")
    parser.add_argument("--timestamp", default=None, help="Specific result timestamp to visualize")

    args = parser.parse_args()

    visualizer = MetaEvaluationVisualizer(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
    )

    visualizer.create_all_visualizations(timestamp=args.timestamp)


if __name__ == "__main__":
    main()
