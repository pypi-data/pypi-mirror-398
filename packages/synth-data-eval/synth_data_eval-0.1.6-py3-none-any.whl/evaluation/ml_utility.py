"""Machine Learning utility evaluation."""

import logging
from typing import Dict, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger(__name__)


class MLUtilityEvaluator:
    """
    Evaluate ML utility of synthetic data.

    Tests whether models trained on synthetic data can perform well
    on real test data.
    """

    def __init__(self, task_type: str = "classification", random_state: int = 42):
        """
        Initialize evaluator.

        Parameters
        ----------
        task_type : str
            'classification' or 'regression'
        random_state : int
            Random seed
        """
        self.task_type = task_type
        self.random_state = random_state
        self.results: Dict[str, Union[Dict[str, float], float]] = {}

    def evaluate(
        self,
        real_train: pd.DataFrame,
        real_test: pd.DataFrame,
        synthetic_train: pd.DataFrame,
        target_col: str,
    ) -> Dict[str, Union[Dict[str, float], float]]:
        """
        Run ML utility evaluation.

        Parameters
        ----------
        real_train : pd.DataFrame
            Real training data
        real_test : pd.DataFrame
            Real test data
        synthetic_train : pd.DataFrame
            Synthetic training data
        target_col : str
            Name of target column

        Returns
        -------
        dict
            Dictionary of evaluation metrics
        """
        logger.info("Running ML Utility evaluation...")

        # Prepare data
        X_real_train, y_real_train = self._prepare_data(real_train, target_col)
        X_real_test, y_real_test = self._prepare_data(real_test, target_col)
        X_synth_train, y_synth_train = self._prepare_data(synthetic_train, target_col)

        results: Dict[str, Union[Dict[str, float], float]] = {}

        # Check if synthetic data has valid target distribution
        if self.task_type == "classification":
            n_classes_real = len(np.unique(y_real_train))
            n_classes_synth = len(np.unique(y_synth_train))

            logger.info(
                f"Real train classes: {n_classes_real}, Synthetic classes: {n_classes_synth}"
            )
            logger.info(
                f"Real train class distribution: {np.unique(y_real_train, return_counts=True)}"
            )
            logger.info(
                f"Synthetic class distribution: {np.unique(y_synth_train, return_counts=True)}"
            )

            if n_classes_synth < 2:
                logger.warning(
                    f"Synthetic data has only {n_classes_synth} class(es). "
                    "Cannot train classifier. Returning zero scores."
                )
                return self._get_default_results()

        # Train on Real, Test on Real (TRTR) - baseline
        try:
            results["trtr"] = self._train_evaluate(
                X_real_train, y_real_train, X_real_test, y_real_test, label="TRTR"
            )
        except Exception as e:
            logger.error(f"TRTR evaluation failed: {e}", exc_info=True)
            results["trtr"] = self._get_default_metrics()

        # Train on Synthetic, Test on Real (TSTR) - key metric
        try:
            results["tstr"] = self._train_evaluate(
                X_synth_train, y_synth_train, X_real_test, y_real_test, label="TSTR"
            )
        except Exception as e:
            logger.error(f"TSTR evaluation failed: {e}", exc_info=True)
            results["tstr"] = self._get_default_metrics()

        # Calculate utility ratio
        try:
            if self.task_type == "classification":
                metric_key = "f1_score"
            else:
                metric_key = "r2_score"

            trtr_score = results["trtr"].get(metric_key, 1e-8)  # type: ignore
            tstr_score = results["tstr"].get(metric_key, 0.0)  # type: ignore

            results["utility_ratio"] = tstr_score / (trtr_score + 1e-8)
        except Exception as e:
            logger.warning(f"Could not compute utility ratio: {e}")
            results["utility_ratio"] = 0.0

        self.results = results
        return results

    def _prepare_data(self, data: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target."""
        X = data.drop(columns=[target_col])
        y = data[target_col]

        # Encode categorical features
        for col in X.select_dtypes(include=["object", "category"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))

        # Scale numerical features
        scaler = StandardScaler()
        X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)

        return X, y

    def _train_evaluate(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        label: str,
    ) -> Dict[str, float]:
        """Train models and evaluate."""
        results = {}

        if self.task_type == "classification":
            # Random Forest
            rf_model = RandomForestClassifier(
                n_estimators=100, random_state=self.random_state, n_jobs=-1
            )
            rf_model.fit(X_train, y_train)
            y_pred = rf_model.predict(X_test)

            results["accuracy"] = accuracy_score(y_test, y_pred)
            results["f1_score"] = f1_score(y_test, y_pred, average="weighted", zero_division=0)

            # AUC - with safety checks
            try:
                if hasattr(rf_model, "predict_proba"):
                    y_pred_proba = rf_model.predict_proba(X_test)
                    n_classes_pred = y_pred_proba.shape[1]
                    n_classes_test = len(np.unique(y_test))

                    logger.info(
                        f"{label} - Prediction shape: {y_pred_proba.shape}, "
                        f"Test classes: {n_classes_test}"
                    )

                    # Only compute ROC-AUC if we have proper binary
                    # or multi-class setup
                    if n_classes_pred >= 2 and n_classes_test >= 2:
                        if n_classes_pred == 2 and n_classes_test == 2:
                            # Binary classification
                            results["roc_auc"] = roc_auc_score(y_test, y_pred_proba[:, 1])
                        elif n_classes_pred > 2 and n_classes_test > 2:
                            # Multi-class
                            results["roc_auc"] = roc_auc_score(
                                y_test, y_pred_proba, multi_class="ovr", average="weighted"
                            )
                        else:
                            logger.warning(
                                f"{label} - Class mismatch: "
                                "pred={n_classes_pred}, "
                                "test={n_classes_test}. Skipping ROC-AUC."
                                "Skipping ROC-AUC."
                            )
                            results["roc_auc"] = 0.0
                    else:
                        logger.warning(f"{label} - Insufficient classes for ROC-AUC")
                        results["roc_auc"] = 0.0
                else:
                    results["roc_auc"] = 0.0
            except Exception as e:
                logger.warning(f"{label} - ROC-AUC computation failed: {e}")
                results["roc_auc"] = 0.0

            # Logistic Regression
            try:
                lr_model = LogisticRegression(max_iter=1000, random_state=self.random_state)
                lr_model.fit(X_train, y_train)
                y_pred_lr = lr_model.predict(X_test)

                results["lr_accuracy"] = accuracy_score(y_test, y_pred_lr)
                results["lr_f1_score"] = f1_score(
                    y_test, y_pred_lr, average="weighted", zero_division=0
                )
            except Exception as e:
                logger.warning(f"{label} - Logistic Regression failed: {e}")
                results["lr_accuracy"] = 0.0
                results["lr_f1_score"] = 0.0

        else:  # regression
            # Random Forest
            rf_model = RandomForestRegressor(
                n_estimators=100, random_state=self.random_state, n_jobs=-1
            )
            rf_model.fit(X_train, y_train)
            y_pred = rf_model.predict(X_test)

            results["rmse"] = np.sqrt(mean_squared_error(y_test, y_pred))
            results["r2_score"] = r2_score(y_test, y_pred)

            # Linear Regression
            try:
                lr_model = LinearRegression()
                lr_model.fit(X_train, y_train)
                y_pred_lr = lr_model.predict(X_test)

                results["lr_rmse"] = np.sqrt(mean_squared_error(y_test, y_pred_lr))
                results["lr_r2_score"] = r2_score(y_test, y_pred_lr)
            except Exception as e:
                logger.warning(f"{label} - Linear Regression failed: {e}")
                results["lr_rmse"] = float("inf")
                results["lr_r2_score"] = 0.0

        logger.info(f"{label} evaluation completed")
        return results

    def _get_default_metrics(self) -> Dict[str, float]:
        """Return default metrics when evaluation fails."""
        if self.task_type == "classification":
            return {
                "accuracy": 0.0,
                "f1_score": 0.0,
                "roc_auc": 0.0,
                "lr_accuracy": 0.0,
                "lr_f1_score": 0.0,
            }
        else:
            return {
                "rmse": float("inf"),
                "r2_score": 0.0,
                "lr_rmse": float("inf"),
                "lr_r2_score": 0.0,
            }

    def _get_default_results(self) -> Dict[str, Union[Dict[str, float], float]]:
        """Return default results structure."""
        return {
            "trtr": self._get_default_metrics(),
            "tstr": self._get_default_metrics(),
            "utility_ratio": 0.0,
        }

    def get_summary(self) -> pd.DataFrame:
        """Get summary comparison of TRTR vs TSTR."""
        if not self.results:
            return pd.DataFrame()

        comparison = pd.DataFrame({"TRTR": self.results["trtr"], "TSTR": self.results["tstr"]})

        return comparison
