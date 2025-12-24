"""Script to download and prepare low-resource datasets.

Downloads small datasets across Medical, Financial, and Social domains
for meta-evaluation experiments.
"""

import logging
import os
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LowResourceDatasetDownloader:
    """Download and prepare low-resource datasets for meta-evaluation."""

    def __init__(self, output_dir: str = "datasets"):
        """
        Initialize downloader.

        Parameters
        ----------
        output_dir : str
            Directory to save datasets
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def download_all(self) -> Dict[str, Dict]:
        """
        Download all low-resource datasets.

        Returns
        -------
        dict
            Dataset configurations for config.yaml
        """
        logger.info("Starting download of low-resource datasets...")

        datasets_config = {}

        # Medical datasets
        datasets_config.update(self._download_medical_datasets())

        # Financial datasets (using UCI datasets as proxies)
        datasets_config.update(self._download_financial_datasets())

        # Social datasets
        datasets_config.update(self._download_social_datasets())

        logger.info(f"Downloaded {len(datasets_config)} datasets")
        return datasets_config

    def _download_medical_datasets(self) -> Dict[str, Dict]:
        """Download small medical datasets."""
        logger.info("Downloading medical datasets...")
        configs = {}

        # 1. Pima Indians Diabetes (768 samples)
        try:
            url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
            df = pd.read_csv(url, header=None)
            df.columns = [
                "Pregnancies",
                "Glucose",
                "BloodPressure",
                "SkinThickness",
                "Insulin",
                "BMI",
                "DiabetesPedigreeFunction",
                "Age",
                "Outcome",
            ]

            output_path = self.output_dir / "pima_diabetes.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded Pima Diabetes: {len(df)} samples")

            configs["pima_diabetes"] = {
                "file": str(output_path),
                "target": "Outcome",
                "task": "classification",
                "test_size": 0.2,
                "discrete_columns": [],
                "sensitive_columns": [],
            }
        except Exception as e:
            logger.error(f"Failed to download Pima Diabetes: {e}")

        # 2. Heart Disease (303 samples)
        try:
            url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
            df = pd.read_csv(url, header=None)
            df.columns = [
                "age",
                "sex",
                "cp",
                "trestbps",
                "chol",
                "fbs",
                "restecg",
                "thalach",
                "exang",
                "oldpeak",
                "slope",
                "ca",
                "thal",
                "target",
            ]

            # Replace missing values (marked as ?)
            df = df.replace("?", pd.NA)
            df = df.dropna()

            # Convert to appropriate types
            for col in df.columns:
                if col != "target":
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Binary classification: 0 = no disease, 1-4 = disease
            df["target"] = (df["target"] > 0).astype(int)

            output_path = self.output_dir / "heart_disease.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded Heart Disease: {len(df)} samples")

            configs["heart_disease"] = {
                "file": str(output_path),
                "target": "target",
                "task": "classification",
                "test_size": 0.2,
                "discrete_columns": ["sex", "cp", "fbs", "restecg", "exang", "slope"],
                "sensitive_columns": ["sex", "age"],
            }
        except Exception as e:
            logger.error(f"Failed to download Heart Disease: {e}")

        # 3. Breast Cancer Wisconsin (569 samples) - from sklearn
        try:
            from sklearn.datasets import load_breast_cancer

            data = load_breast_cancer()
            df = pd.DataFrame(data.data, columns=data.feature_names)
            df["target"] = data.target

            output_path = self.output_dir / "breast_cancer.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded Breast Cancer: {len(df)} samples")

            configs["breast_cancer"] = {
                "file": str(output_path),
                "target": "target",
                "task": "classification",
                "test_size": 0.2,
                "discrete_columns": [],
                "sensitive_columns": [],
            }
        except Exception as e:
            logger.error(f"Failed to download Breast Cancer: {e}")

        return configs

    def _download_financial_datasets(self) -> Dict[str, Dict]:
        """Download small financial datasets."""
        logger.info("Downloading financial datasets...")
        configs = {}

        # 1. German Credit Dataset (1000 samples)
        try:
            url = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"

            # German credit has specific column names
            col_names = [
                "checking_status",
                "duration",
                "credit_history",
                "purpose",
                "credit_amount",
                "savings_status",
                "employment",
                "installment_rate",
                "personal_status_sex",
                "other_parties",
                "residence_since",
                "property_magnitude",
                "age",
                "other_payment_plans",
                "housing",
                "existing_credits",
                "job",
                "num_dependents",
                "own_telephone",
                "foreign_worker",
                "target",
            ]

            df = pd.read_csv(url, sep=" ", header=None, names=col_names)

            # Target: 1 = good credit, 2 = bad credit → remap to 0/1
            df["target"] = (df["target"] == 1).astype(int)

            output_path = self.output_dir / "german_credit.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded German Credit: {len(df)} samples")

            discrete_cols = [
                "checking_status",
                "credit_history",
                "purpose",
                "savings_status",
                "employment",
                "personal_status_sex",
                "other_parties",
                "property_magnitude",
                "other_payment_plans",
                "housing",
                "job",
                "own_telephone",
                "foreign_worker",
            ]

            configs["german_credit"] = {
                "file": str(output_path),
                "target": "target",
                "task": "classification",
                "test_size": 0.2,
                "discrete_columns": discrete_cols,
                "sensitive_columns": ["age", "personal_status_sex"],
            }
        except Exception as e:
            logger.error(f"Failed to download German Credit: {e}")

        # 2. Iris Dataset (150 samples) - very small
        try:
            from sklearn.datasets import load_iris

            data = load_iris()
            df = pd.DataFrame(data.data, columns=data.feature_names)
            df["target"] = data.target

            output_path = self.output_dir / "iris.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded Iris: {len(df)} samples")

            configs["iris"] = {
                "file": str(output_path),
                "target": "target",
                "task": "classification",
                "test_size": 0.2,
                "discrete_columns": [],
                "sensitive_columns": [],
            }
        except Exception as e:
            logger.error(f"Failed to download Iris: {e}")

        return configs

    def _download_social_datasets(self) -> Dict[str, Dict]:
        """Download small social science datasets."""
        logger.info("Downloading social datasets...")
        configs = {}

        # 1. Student Performance (649 samples)
        try:
            url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00320/student.zip"

            # Note: This requires handling zip files
            import io
            import zipfile

            import requests

            response = requests.get(url)
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Use math dataset (smaller)
                with z.open("student-mat.csv") as f:
                    df = pd.read_csv(f, sep=";")

            # Use final grade as target (regression or classification)
            # For classification: pass/fail (G3 >= 10)
            df["pass"] = (df["G3"] >= 10).astype(int)

            output_path = self.output_dir / "student_performance.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded Student Performance: {len(df)} samples")

            discrete_cols = [
                "school",
                "sex",
                "address",
                "famsize",
                "Pstatus",
                "Mjob",
                "Fjob",
                "reason",
                "guardian",
                "schoolsup",
                "famsup",
                "paid",
                "activities",
                "nursery",
                "higher",
                "internet",
                "romantic",
            ]

            configs["student_performance"] = {
                "file": str(output_path),
                "target": "pass",
                "task": "classification",
                "test_size": 0.2,
                "discrete_columns": discrete_cols,
                "sensitive_columns": ["sex", "age"],
            }
        except Exception as e:
            logger.error(f"Failed to download Student Performance: {e}")

        return configs

    def generate_config_yaml(self, datasets_config: Dict[str, Dict]) -> str:
        """
        Generate YAML configuration for the downloaded datasets.

        Parameters
        ----------
        datasets_config : dict
            Dataset configurations

        Returns
        -------
        str
            YAML configuration string
        """
        import yaml

        yaml_str = "# Low-Resource Datasets for Meta-Evaluation\n\n"
        yaml_str += "low_resource_datasets:\n"

        # Convert to YAML
        yaml_str += yaml.dump(datasets_config, default_flow_style=False, indent=2)

        return yaml_str


def main():
    """Main execution function."""
    downloader = LowResourceDatasetDownloader()
    datasets_config = downloader.download_all()

    # Generate and print YAML config
    yaml_config = downloader.generate_config_yaml(datasets_config)
    print("\n" + "=" * 80)
    print("Add the following to your config.yaml:")
    print("=" * 80)
    print(yaml_config)

    # Save to file
    config_output = Path("datasets") / "low_resource_datasets.yaml"
    with open(config_output, "w") as f:
        f.write(yaml_config)
    logger.info(f"\nConfiguration saved to: {config_output}")


if __name__ == "__main__":
    main()
