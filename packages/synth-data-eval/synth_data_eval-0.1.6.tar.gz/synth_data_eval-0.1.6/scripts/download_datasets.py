"""Download and prepare all datasets for evaluation."""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetDownloader:
    """Download and prepare evaluation datasets."""

    def __init__(self, data_dir: str = "datasets"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def download_all(self):
        """Download all datasets."""
        logger.info("Starting dataset downloads...")

        # Download datasets, but don't fail if one fails
        try:
            self.download_adult()
        except Exception as e:
            logger.warning(f"Adult dataset download failed: {e}")

        try:
            self.download_credit()
        except Exception as e:
            logger.warning(f"Credit dataset download failed: {e}")

        try:
            self.download_diabetes()
        except Exception as e:
            logger.warning(f"Diabetes dataset download failed: {e}")

        try:
            self.download_california_housing()
        except Exception as e:
            logger.warning(f"California Housing dataset download failed: {e}")

        try:
            self.download_wine_quality()
        except Exception as e:
            logger.warning(f"Wine Quality dataset download failed: {e}")

        logger.info("Dataset download process completed!")

    def download_adult(self):
        """Download Adult Income dataset from UCI."""
        output_path = self.data_dir / "adult.csv"

        if output_path.exists():
            logger.info("✓ Adult dataset already exists, skipping download")
            return

        logger.info("Downloading Adult Income dataset...")

        url = (
            "https://archive.ics.uci.edu/ml/machine-learning-databases/" "adult/adult.data"
        )  # noqa: E501
        columns = [
            "age",
            "workclass",
            "fnlwgt",
            "education",
            "education_num",
            "marital_status",
            "occupation",
            "relationship",
            "race",
            "sex",
            "capital_gain",
            "capital_loss",
            "hours_per_week",
            "native_country",
            "income",
        ]

        try:
            df = pd.read_csv(
                url, names=columns, na_values=" ?", skipinitialspace=True
            )  # noqa: E501
            df = df.dropna()
            df["income"] = (df["income"] == ">50K").astype(int)

            df.to_csv(output_path, index=False)
            logger.info(f"✓ Adult dataset saved: {df.shape}")
        except Exception as e:
            logger.error(f"❌ Failed to download Adult dataset: {e}")
            logger.info("💡 Note: Adult dataset may already exist locally")
            raise

    def download_credit(self):
        """Download Credit Card Default dataset."""
        output_path = self.data_dir / "credit.csv"

        if output_path.exists():
            logger.info("✓ Credit dataset already exists, skipping download")
            return

        logger.info("Downloading Credit Card Default dataset...")

        # Using UCI default of credit card clients dataset
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00350/default%20of%20credit%20card%20clients.xls"  # noqa: E501

        try:
            df = pd.read_excel(url, header=1)
            df.columns = df.columns.str.lower().str.replace(" ", "_")

            df.to_csv(output_path, index=False)
            logger.info(f"✓ Credit dataset saved: {df.shape}")
        except Exception as e:
            logger.warning(f"Could not download credit dataset: {e}")
            logger.info("Please download manually from UCI ML Repository")
            raise

    def download_diabetes(self):
        """Download Diabetes dataset."""
        output_path = self.data_dir / "diabetes.csv"

        if output_path.exists():
            logger.info("✓ Diabetes dataset already exists, skipping download")
            return

        logger.info("Downloading Diabetes dataset...")

        from sklearn.datasets import load_diabetes

        data = load_diabetes(as_frame=True)
        df = data.frame  # type: ignore

        df.to_csv(output_path, index=False)
        logger.info(f"✓ Diabetes dataset saved: {df.shape}")

    def download_california_housing(self):
        """Download California Housing dataset."""
        output_path = self.data_dir / "california_housing.csv"

        if output_path.exists():
            logger.info("✓ California Housing dataset exists, skipping")
            return

        logger.info("Downloading California Housing dataset...")

        from sklearn.datasets import fetch_california_housing

        data = fetch_california_housing(as_frame=True)
        df = data.frame  # type: ignore

        df.to_csv(output_path, index=False)
        logger.info(f"✓ California Housing dataset saved: {df.shape}")

    def download_wine_quality(self):
        """Download Wine Quality dataset from UCI."""
        output_path = self.data_dir / "wine_quality.csv"

        if output_path.exists():
            logger.info("✓ Wine Quality dataset exists, skipping")
            return

        logger.info("Downloading Wine Quality dataset...")

        url = (
            "https://archive.ics.uci.edu/ml/machine-learning-databases/"
            "wine-quality/winequality-red.csv"
        )

        try:
            df = pd.read_csv(url, sep=";")
            df.to_csv(output_path, index=False)
            logger.info(f"✓ Wine Quality dataset saved: {df.shape}")
        except Exception as e:
            logger.error(f"❌ Failed to download Wine Quality dataset: {e}")
            raise


if __name__ == "__main__":
    downloader = DatasetDownloader()
    downloader.download_all()
