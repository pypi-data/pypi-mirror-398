"""
Model Evaluator
Comprehensive model evaluation and metrics calculation
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from sklearn.metrics import (
    # Classification metrics
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    precision_recall_curve, roc_curve, average_precision_score,
    log_loss, matthews_corrcoef, cohen_kappa_score,
    # Regression metrics
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error, explained_variance_score,
    max_error, median_absolute_error
)

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Evaluates ML models with comprehensive metrics
    
    Supports:
        - Classification: accuracy, precision, recall, F1, AUC-ROC, etc.
        - Regression: MSE, RMSE, MAE, R², MAPE, etc.
        - Confusion matrix and classification reports
        - Threshold analysis
        - Confidence calibration
    """
    
    def __init__(self, task_type: str = "classification"):
        """
        Initialize ModelEvaluator
        
        Args:
            task_type: 'classification' or 'regression'
        """
        self.task_type = task_type
        self._evaluation_results: Dict[str, Any] = {}
    
    def evaluate(
        self,
        model: Any,
        X: pd.DataFrame,
        y: pd.Series,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Evaluate model performance
        
        Args:
            model: Trained model with predict/predict_proba methods
            X: Feature DataFrame
            y: True labels/values
            threshold: Classification threshold (for binary classification)
        
        Returns:
            Dictionary of metrics
        """
        start_time = datetime.utcnow()
        
        if self.task_type == "classification":
            metrics = self._evaluate_classification(model, X, y, threshold)
        else:
            metrics = self._evaluate_regression(model, X, y)
        
        metrics["evaluation_time"] = datetime.utcnow().isoformat()
        metrics["samples_evaluated"] = len(y)
        
        self._evaluation_results = metrics
        
        return metrics
    
    def _evaluate_classification(
        self,
        model: Any,
        X: pd.DataFrame,
        y: pd.Series,
        threshold: float
    ) -> Dict[str, Any]:
        """Evaluate classification model"""
        # Get predictions
        y_pred = model.predict(X)
        
        # Get probabilities if available
        try:
            y_proba = model.predict_proba(X)
            if len(y_proba.shape) == 2 and y_proba.shape[1] == 2:
                y_proba = y_proba[:, 1]  # Binary classification
            has_proba = True
        except:
            y_proba = None
            has_proba = False
        
        # Basic metrics
        metrics = {
            "accuracy": float(accuracy_score(y, y_pred)),
            "precision": float(precision_score(y, y_pred, average='weighted', zero_division=0)),
            "recall": float(recall_score(y, y_pred, average='weighted', zero_division=0)),
            "f1": float(f1_score(y, y_pred, average='weighted', zero_division=0)),
        }
        
        # Binary-specific metrics
        n_classes = len(np.unique(y))
        if n_classes == 2:
            metrics["precision_binary"] = float(precision_score(y, y_pred, zero_division=0))
            metrics["recall_binary"] = float(recall_score(y, y_pred, zero_division=0))
            metrics["f1_binary"] = float(f1_score(y, y_pred, zero_division=0))
            
            if has_proba:
                # Apply threshold
                y_pred_threshold = (y_proba >= threshold).astype(int)
                metrics["precision_at_threshold"] = float(precision_score(y, y_pred_threshold, zero_division=0))
                metrics["recall_at_threshold"] = float(recall_score(y, y_pred_threshold, zero_division=0))
                metrics["f1_at_threshold"] = float(f1_score(y, y_pred_threshold, zero_division=0))
        
        # AUC metrics
        if has_proba:
            try:
                if n_classes == 2:
                    metrics["roc_auc"] = float(roc_auc_score(y, y_proba))
                    metrics["average_precision"] = float(average_precision_score(y, y_proba))
                else:
                    # Multi-class
                    metrics["roc_auc"] = float(roc_auc_score(
                        y, model.predict_proba(X), multi_class='ovr', average='weighted'
                    ))
            except Exception as e:
                logger.warning(f"Could not calculate AUC: {e}")
        
        # Additional metrics
        try:
            metrics["matthews_corrcoef"] = float(matthews_corrcoef(y, y_pred))
        except:
            pass
        
        try:
            metrics["cohen_kappa"] = float(cohen_kappa_score(y, y_pred))
        except:
            pass
        
        if has_proba:
            try:
                metrics["log_loss"] = float(log_loss(y, model.predict_proba(X)))
            except:
                pass
        
        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        metrics["confusion_matrix"] = cm.tolist()
        
        # Class-wise metrics
        report = classification_report(y, y_pred, output_dict=True, zero_division=0)
        metrics["class_report"] = report
        
        return metrics
    
    def _evaluate_regression(
        self,
        model: Any,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Dict[str, Any]:
        """Evaluate regression model"""
        # Get predictions
        y_pred = model.predict(X)
        
        # Ensure proper shapes
        y_true = y.values.flatten()
        y_pred = np.array(y_pred).flatten()
        
        metrics = {
            "mse": float(mean_squared_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2": float(r2_score(y_true, y_pred)),
            "explained_variance": float(explained_variance_score(y_true, y_pred)),
            "max_error": float(max_error(y_true, y_pred)),
            "median_ae": float(median_absolute_error(y_true, y_pred)),
        }
        
        # MAPE (avoid division by zero)
        try:
            # Filter out zeros in actual values
            mask = y_true != 0
            if mask.sum() > 0:
                metrics["mape"] = float(mean_absolute_percentage_error(
                    y_true[mask], y_pred[mask]
                ))
        except:
            pass
        
        # Residual statistics
        residuals = y_true - y_pred
        metrics["residuals"] = {
            "mean": float(np.mean(residuals)),
            "std": float(np.std(residuals)),
            "min": float(np.min(residuals)),
            "max": float(np.max(residuals)),
            "median": float(np.median(residuals))
        }
        
        return metrics
    
    def calculate_threshold_metrics(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        thresholds: List[float] = None
    ) -> pd.DataFrame:
        """
        Calculate metrics at different classification thresholds
        
        Args:
            y_true: True labels
            y_proba: Predicted probabilities
            thresholds: List of thresholds to evaluate
        
        Returns:
            DataFrame with metrics at each threshold
        """
        if thresholds is None:
            thresholds = np.arange(0.1, 1.0, 0.1)
        
        results = []
        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)
            
            results.append({
                "threshold": threshold,
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1": f1_score(y_true, y_pred, zero_division=0),
                "accuracy": accuracy_score(y_true, y_pred),
                "positive_predictions": y_pred.sum(),
                "positive_rate": y_pred.mean()
            })
        
        return pd.DataFrame(results)
    
    def get_optimal_threshold(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        metric: str = "f1"
    ) -> Tuple[float, float]:
        """
        Find optimal classification threshold
        
        Args:
            y_true: True labels
            y_proba: Predicted probabilities
            metric: Metric to optimize ('f1', 'precision', 'recall')
        
        Returns:
            Tuple of (optimal_threshold, metric_value)
        """
        thresholds = np.arange(0.01, 1.0, 0.01)
        best_threshold = 0.5
        best_score = 0
        
        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)
            
            if metric == "f1":
                score = f1_score(y_true, y_pred, zero_division=0)
            elif metric == "precision":
                score = precision_score(y_true, y_pred, zero_division=0)
            elif metric == "recall":
                score = recall_score(y_true, y_pred, zero_division=0)
            else:
                score = f1_score(y_true, y_pred, zero_division=0)
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
        
        return best_threshold, best_score
    
    def get_roc_curve_data(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray
    ) -> Dict[str, List[float]]:
        """
        Get ROC curve data points
        
        Returns:
            Dict with 'fpr', 'tpr', 'thresholds'
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_proba)
        return {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "thresholds": thresholds.tolist()
        }
    
    def get_pr_curve_data(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray
    ) -> Dict[str, List[float]]:
        """
        Get Precision-Recall curve data points
        
        Returns:
            Dict with 'precision', 'recall', 'thresholds'
        """
        precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
        return {
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "thresholds": thresholds.tolist()
        }
    
    def compare_models(
        self,
        models: Dict[str, Any],
        X: pd.DataFrame,
        y: pd.Series
    ) -> pd.DataFrame:
        """
        Compare multiple models
        
        Args:
            models: Dict of {name: model}
            X: Feature DataFrame
            y: True labels/values
        
        Returns:
            Comparison DataFrame
        """
        results = []
        
        for name, model in models.items():
            metrics = self.evaluate(model, X, y)
            metrics["model"] = name
            results.append(metrics)
        
        df = pd.DataFrame(results)
        
        # Reorder columns
        cols = ["model"] + [c for c in df.columns if c != "model"]
        return df[cols]
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of last evaluation"""
        if not self._evaluation_results:
            return {}
        
        summary = {
            "task_type": self.task_type,
            "samples": self._evaluation_results.get("samples_evaluated"),
            "evaluation_time": self._evaluation_results.get("evaluation_time")
        }
        
        if self.task_type == "classification":
            summary["key_metrics"] = {
                "accuracy": self._evaluation_results.get("accuracy"),
                "f1": self._evaluation_results.get("f1"),
                "roc_auc": self._evaluation_results.get("roc_auc"),
                "precision": self._evaluation_results.get("precision"),
                "recall": self._evaluation_results.get("recall")
            }
        else:
            summary["key_metrics"] = {
                "rmse": self._evaluation_results.get("rmse"),
                "mae": self._evaluation_results.get("mae"),
                "r2": self._evaluation_results.get("r2"),
                "mape": self._evaluation_results.get("mape")
            }
        
        return summary
    
    @staticmethod
    def format_confusion_matrix(
        cm: np.ndarray,
        labels: List[str] = None
    ) -> pd.DataFrame:
        """
        Format confusion matrix as DataFrame
        
        Args:
            cm: Confusion matrix array
            labels: Class labels
        
        Returns:
            Formatted DataFrame
        """
        if labels is None:
            labels = [f"Class_{i}" for i in range(len(cm))]
        
        return pd.DataFrame(
            cm,
            index=[f"Actual_{l}" for l in labels],
            columns=[f"Predicted_{l}" for l in labels]
        )
