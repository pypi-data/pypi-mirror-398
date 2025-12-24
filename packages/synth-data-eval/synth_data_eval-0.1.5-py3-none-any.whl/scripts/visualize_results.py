"""Visualization of benchmark results."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Setup plotting style
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.2)
plt.rcParams["figure.dpi"] = 300


class ResultsVisualizer:
    """Visualize benchmark results."""

    def __init__(self, results_path: str, output_dir: str = "results/figures"):
        """
        Initialize visualizer.

        Parameters
        ----------
        results_path : str
            Path to results CSV file
        output_dir : str
            Output directory for plots
        """
        self.results_df = pd.read_csv(results_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Aggregate over runs
        self.summary_df = self.results_df.groupby(["dataset", "generator"]).mean().reset_index()

    def plot_all(self):
        """Generate all visualizations."""
        print("Generating visualizations...")

        self.plot_sdmetrics_comparison()
        self.plot_ml_utility_comparison()
        self.plot_privacy_metrics()
        self.plot_training_times()
        self.plot_radar_chart()
        self.plot_heatmap()

        print(f"All plots saved to {self.output_dir}")

    def plot_sdmetrics_comparison(self):
        """Plot SDMetrics quality scores."""
        fig, ax = plt.subplots(figsize=(12, 6))

        if "sdm_quality_score" in self.summary_df.columns:
            data = self.summary_df.pivot(
                index="dataset", columns="generator", values="sdm_quality_score"
            )

            data.plot(kind="bar", ax=ax, width=0.8)
            ax.set_ylabel("Quality Score", fontsize=12)
            ax.set_xlabel("Dataset", fontsize=12)
            ax.set_title(
                "SDMetrics Quality Score by Dataset and Generator", fontsize=14, fontweight="bold"
            )
            ax.legend(title="Generator", bbox_to_anchor=(1.05, 1), loc="upper left")
            ax.set_ylim(0, 1)
            ax.grid(axis="y", alpha=0.3)

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(self.output_dir / "sdmetrics_comparison.png", bbox_inches="tight")
            plt.close()

    def plot_ml_utility_comparison(self):
        """Plot ML utility metrics (TRTR vs TSTR)."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # F1/R2 scores
        metric_cols = [
            col
            for col in self.summary_df.columns
            if "ml_tstr" in col and ("f1_score" in col or "r2_score" in col)
        ]

        if metric_cols:
            metric_col = metric_cols[0]  # Take first match

            # TSTR performance
            data_tstr = self.summary_df.pivot(
                index="dataset", columns="generator", values=metric_col
            )

            data_tstr.plot(kind="bar", ax=axes[0], width=0.8)
            axes[0].set_ylabel("Score", fontsize=12)
            axes[0].set_xlabel("Dataset", fontsize=12)
            axes[0].set_title("ML Utility (TSTR)", fontsize=14, fontweight="bold")
            axes[0].legend(title="Generator", bbox_to_anchor=(1.05, 1), loc="upper left")
            axes[0].set_ylim(0, 1)
            axes[0].grid(axis="y", alpha=0.3)
            axes[0].tick_params(axis="x", rotation=45)

            # Utility ratio
            if "ml_utility_ratio" in self.summary_df.columns:
                data_ratio = self.summary_df.pivot(
                    index="dataset", columns="generator", values="ml_utility_ratio"
                )

                data_ratio.plot(kind="bar", ax=axes[1], width=0.8)
                axes[1].set_ylabel("Ratio (TSTR/TRTR)", fontsize=12)
                axes[1].set_xlabel("Dataset", fontsize=12)
                axes[1].set_title("ML Utility Ratio", fontsize=14, fontweight="bold")
                axes[1].axhline(
                    y=1.0, color="red", linestyle="--", linewidth=2, label="TRTR baseline"
                )
                axes[1].legend(title="Generator", bbox_to_anchor=(1.05, 1), loc="upper left")
                axes[1].grid(axis="y", alpha=0.3)
                axes[1].tick_params(axis="x", rotation=45)

            plt.tight_layout()
            plt.savefig(self.output_dir / "ml_utility_comparison.png", bbox_inches="tight")
            plt.close()

    def plot_privacy_metrics(self):
        """Plot privacy metrics."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # DCR
        if "privacy_dcr" in self.summary_df.columns:
            data_dcr = self.summary_df.pivot(
                index="dataset", columns="generator", values="privacy_dcr"
            )

            data_dcr.plot(kind="bar", ax=axes[0], width=0.8)
            axes[0].set_ylabel("Distance", fontsize=12)
            axes[0].set_xlabel("Dataset", fontsize=12)
            axes[0].set_title("Distance to Closest Record (DCR)", fontsize=14, fontweight="bold")
            axes[0].legend(title="Generator", bbox_to_anchor=(1.05, 1), loc="upper left")
            axes[0].grid(axis="y", alpha=0.3)
            axes[0].tick_params(axis="x", rotation=45)

        # NNDR
        if "privacy_nndr" in self.summary_df.columns:
            data_nndr = self.summary_df.pivot(
                index="dataset", columns="generator", values="privacy_nndr"
            )

            data_nndr.plot(kind="bar", ax=axes[1], width=0.8)
            axes[1].set_ylabel("Ratio", fontsize=12)
            axes[1].set_xlabel("Dataset", fontsize=12)
            axes[1].set_title(
                "Nearest Neighbor Distance Ratio (NNDR)", fontsize=14, fontweight="bold"
            )
            axes[1].axhline(
                y=1.0, color="red", linestyle="--", linewidth=2, label="Real data baseline"
            )
            axes[1].legend(title="Generator", bbox_to_anchor=(1.05, 1), loc="upper left")
            axes[1].grid(axis="y", alpha=0.3)
            axes[1].tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(self.output_dir / "privacy_metrics.png", bbox_inches="tight")
        plt.close()

    def plot_training_times(self):
        """Plot training and generation times."""
        fig, ax = plt.subplots(figsize=(12, 6))

        if "training_time" in self.summary_df.columns:
            # Prepare data
            x = np.arange(len(self.summary_df["dataset"].unique()))
            width = 0.25
            generators = self.summary_df["generator"].unique()

            for i, gen in enumerate(generators):
                gen_data = self.summary_df[self.summary_df["generator"] == gen]
                times = gen_data["training_time"].values
                ax.bar(x + i * width, times, width, label=gen)

            ax.set_ylabel("Time (seconds)", fontsize=12)
            ax.set_xlabel("Dataset", fontsize=12)
            ax.set_title("Training Time Comparison", fontsize=14, fontweight="bold")
            ax.set_xticks(x + width)
            ax.set_xticklabels(self.summary_df["dataset"].unique(), rotation=45, ha="right")
            ax.legend(title="Generator")
            ax.grid(axis="y", alpha=0.3)

            plt.tight_layout()
            plt.savefig(self.output_dir / "training_times.png", bbox_inches="tight")
            plt.close()

    def plot_radar_chart(self):
        """Create radar chart for multi-metric comparison."""
        # Select key metrics
        metrics = []
        metric_names = []

        if "sdm_quality_score" in self.summary_df.columns:
            metrics.append("sdm_quality_score")
            metric_names.append("Quality")

        if "ml_utility_ratio" in self.summary_df.columns:
            metrics.append("ml_utility_ratio")
            metric_names.append("ML Utility")

        if "privacy_dcr" in self.summary_df.columns:
            metrics.append("privacy_dcr")
            metric_names.append("Privacy (DCR)")

        if "sdm_correlation_similarity" in self.summary_df.columns:
            metrics.append("sdm_correlation_similarity")
            metric_names.append("Correlation")

        if len(metrics) < 3:
            print("Not enough metrics for radar chart")
            return

        # Create radar chart for each dataset
        datasets = self.summary_df["dataset"].unique()

        for dataset in datasets:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection="polar"))

            dataset_data = self.summary_df[self.summary_df["dataset"] == dataset]

            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
            angles += angles[:1]  # Complete the circle

            for gen in dataset_data["generator"].unique():
                gen_data = dataset_data[dataset_data["generator"] == gen]

                values = []
                for metric in metrics:
                    val = gen_data[metric].values[0] if len(gen_data) > 0 else 0
                    # Normalize to 0-1 if needed
                    if metric == "privacy_dcr":
                        val = min(val, 2) / 2  # Normalize DCR
                    values.append(val)

                values += values[:1]  # Complete the circle

                ax.plot(angles, values, "o-", linewidth=2, label=gen)
                ax.fill(angles, values, alpha=0.15)

            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metric_names, size=10)
            ax.set_ylim(0, 1)
            ax.set_title(f"Multi-Metric Comparison: {dataset}", size=14, fontweight="bold", pad=20)
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
            ax.grid(True)

            plt.tight_layout()
            plt.savefig(self.output_dir / f"radar_{dataset}.png", bbox_inches="tight")
            plt.close()

    def plot_heatmap(self):
        """Create heatmap of all metrics."""
        # Select numeric columns
        numeric_cols = self.summary_df.select_dtypes(include=[np.number]).columns
        metric_cols = [
            col
            for col in numeric_cols
            if col not in ["run_id", "train_size", "test_size", "synthetic_size"]
        ]

        if len(metric_cols) == 0:
            return

        # Create index combining dataset and generator
        self.summary_df["dataset_generator"] = (
            self.summary_df["dataset"] + " - " + self.summary_df["generator"]
        )

        # Create pivot table
        heatmap_data = self.summary_df.set_index("dataset_generator")[
            metric_cols[:10]
        ]  # Limit to first 10 metrics

        # Normalize each column to 0-1
        heatmap_data_norm = (heatmap_data - heatmap_data.min()) / (
            heatmap_data.max() - heatmap_data.min() + 1e-8
        )

        fig, ax = plt.subplots(figsize=(14, 10))
        sns.heatmap(
            heatmap_data_norm.T,
            annot=False,
            cmap="RdYlGn",
            center=0.5,
            cbar_kws={"label": "Normalized Score"},
            ax=ax,
        )
        ax.set_title("Heatmap of All Metrics (Normalized)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Dataset - Generator", fontsize=12)
        ax.set_ylabel("Metric", fontsize=12)

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(self.output_dir / "metrics_heatmap.png", bbox_inches="tight")
        plt.close()


def main():
    """Main execution function."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python visualize_results.py <results_csv_path>")
        print("Example: python visualize_results.py results/raw/results_20241023_120000.csv")
        return

    results_path = sys.argv[1]

    visualizer = ResultsVisualizer(results_path)
    visualizer.plot_all()


if __name__ == "__main__":
    main()
