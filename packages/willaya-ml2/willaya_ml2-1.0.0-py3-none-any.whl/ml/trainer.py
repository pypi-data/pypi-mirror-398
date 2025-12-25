"""
ML Trainer
Handles model training with hyperparameter tuning
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import optuna
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold

from .model_factory import ModelFactory, get_supported_algorithms
from .preprocessing import PipelineExecutor

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Orchestrates ML model training with:
        - Multiple algorithm training
        - Hyperparameter tuning (Optuna)
        - Cross-validation
        - Model comparison and selection
    """
    
    def __init__(
        self,
        task_type: str = "classification",
        algorithms: List[str] = None,
        config: Dict[str, Any] = None
    ):
        """
        Initialize ModelTrainer
        
        Args:
            task_type: 'classification' or 'regression'
            algorithms: List of algorithms to train
            config: Training configuration
        """
        self.task_type = task_type
        self.algorithms = algorithms or self._get_default_algorithms()
        self.config = config or {}
        
        # Training settings
        self.test_size = self.config.get('test_size', 0.2)
        self.cv_folds = self.config.get('cv_folds', 5)
        self.auto_tune = self.config.get('auto_tune', True)
        self.n_trials = self.config.get('n_trials', 50)
        self.random_state = self.config.get('random_state', 42)
        self.n_jobs = self.config.get('n_jobs', -1)
        
        # Results storage
        self._training_results: Dict[str, Any] = {}
        self._best_model: Optional[Any] = None
        self._best_algorithm: Optional[str] = None
        self._best_params: Optional[Dict[str, Any]] = None
        self._best_score: Optional[float] = None
    
    def _get_default_algorithms(self) -> List[str]:
        """Get default algorithms based on task type"""
        if self.task_type == "classification":
            return ["xgboost", "lightgbm", "random_forest", "logistic_regression"]
        else:
            return ["xgboost", "lightgbm", "random_forest", "linear_regression"]
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparameters: Optional[Dict[str, Dict[str, Any]]] = None,
        callbacks: Optional[Dict[str, callable]] = None
    ) -> Dict[str, Any]:
        """
        Train models with all specified algorithms
        
        Args:
            X: Feature DataFrame
            y: Target Series
            hyperparameters: Optional per-algorithm hyperparameters
            callbacks: Optional callbacks for progress tracking
        
        Returns:
            Training results with metrics for all models
        """
        start_time = datetime.utcnow()
        hyperparameters = hyperparameters or {}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y if self.task_type == "classification" else None
        )
        
        logger.info(f"Training data: {X_train.shape}, Test data: {X_test.shape}")
        
        results = {
            "start_time": start_time.isoformat(),
            "task_type": self.task_type,
            "data_shape": {
                "total": list(X.shape),
                "train": list(X_train.shape),
                "test": list(X_test.shape)
            },
            "algorithms": {},
            "best_algorithm": None,
            "best_score": None
        }
        
        best_score = float('-inf') if self.task_type == "classification" else float('inf')
        
        for algorithm in self.algorithms:
            logger.info(f"Training {algorithm}...")
            
            try:
                # Get hyperparameters
                algo_params = hyperparameters.get(algorithm, {})
                
                # Train with or without tuning
                if self.auto_tune and not algo_params:
                    algo_result = self._train_with_tuning(
                        algorithm, X_train, y_train, X_test, y_test
                    )
                else:
                    algo_result = self._train_single(
                        algorithm, X_train, y_train, X_test, y_test, algo_params
                    )
                
                results["algorithms"][algorithm] = algo_result
                
                # Check if best
                primary_metric = algo_result.get("primary_metric", 0)
                is_better = (
                    (self.task_type == "classification" and primary_metric > best_score) or
                    (self.task_type == "regression" and primary_metric < best_score)
                )
                
                if is_better:
                    best_score = primary_metric
                    results["best_algorithm"] = algorithm
                    results["best_score"] = primary_metric
                    self._best_model = algo_result.get("model")
                    self._best_algorithm = algorithm
                    self._best_params = algo_result.get("hyperparameters", {})
                    self._best_score = primary_metric
                
                # Callback
                if callbacks and "on_algorithm_complete" in callbacks:
                    callbacks["on_algorithm_complete"](algorithm, algo_result)
                    
            except Exception as e:
                logger.error(f"Error training {algorithm}: {e}")
                results["algorithms"][algorithm] = {
                    "status": "error",
                    "error": str(e)
                }
        
        results["end_time"] = datetime.utcnow().isoformat()
        results["duration_seconds"] = (
            datetime.utcnow() - start_time
        ).total_seconds()
        
        self._training_results = results
        
        return results
    
    def _train_single(
        self,
        algorithm: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        hyperparameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Train a single model without tuning"""
        # Create model
        model = ModelFactory.create_model(algorithm, self.task_type, hyperparameters)
        
        # Train
        model.fit(X_train, y_train)
        
        # Evaluate
        from .evaluator import ModelEvaluator
        evaluator = ModelEvaluator(self.task_type)
        metrics = evaluator.evaluate(model, X_test, y_test)
        
        # Cross-validation
        cv_scores = self._cross_validate(model, X_train, y_train)
        
        # Primary metric
        if self.task_type == "classification":
            primary_metric = metrics.get("roc_auc", metrics.get("accuracy", 0))
        else:
            primary_metric = -metrics.get("rmse", float('inf'))  # Negative for comparison
        
        return {
            "status": "success",
            "model": model,
            "hyperparameters": hyperparameters,
            "metrics": metrics,
            "cv_scores": cv_scores,
            "primary_metric": primary_metric,
            "feature_importance": model.get_feature_importance()
        }
    
    def _train_with_tuning(
        self,
        algorithm: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict[str, Any]:
        """Train with hyperparameter tuning using Optuna"""
        
        def objective(trial):
            # Get hyperparameter search space
            params = self._get_search_space(algorithm, trial)
            
            # Create and train model
            model = ModelFactory.create_model(algorithm, self.task_type, params)
            
            # Cross-validation score
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42) \
                if self.task_type == "classification" else \
                KFold(n_splits=3, shuffle=True, random_state=42)
            
            scores = cross_val_score(
                model.model, X_train, y_train, cv=cv,
                scoring='roc_auc' if self.task_type == "classification" else 'neg_root_mean_squared_error',
                n_jobs=self.n_jobs
            )
            
            return scores.mean()
        
        # Run optimization
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(
            direction="maximize" if self.task_type == "classification" else "minimize"
        )
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
        
        # Train final model with best params
        best_params = study.best_params
        return self._train_single(
            algorithm, X_train, y_train, X_test, y_test, best_params
        )
    
    def _get_search_space(self, algorithm: str, trial) -> Dict[str, Any]:
        """Get Optuna search space for algorithm"""
        if algorithm == "xgboost":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            }
        elif algorithm == "lightgbm":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 20, 150),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            }
        elif algorithm == "catboost":
            return {
                "iterations": trial.suggest_int("iterations", 50, 500),
                "depth": trial.suggest_int("depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1e-8, 10.0, log=True),
            }
        elif algorithm == "random_forest":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 20),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
            }
        elif algorithm in ["logistic_regression", "linear_regression"]:
            return {
                "C": trial.suggest_float("C", 1e-4, 10.0, log=True) if algorithm == "logistic_regression" else {},
            }
        elif algorithm == "svm":
            return {
                "C": trial.suggest_float("C", 1e-4, 10.0, log=True),
                "kernel": trial.suggest_categorical("kernel", ["rbf", "linear", "poly"]),
            }
        
        return {}
    
    def _cross_validate(
        self, 
        model, 
        X: pd.DataFrame, 
        y: pd.Series
    ) -> Dict[str, Any]:
        """Perform cross-validation"""
        cv = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=42) \
            if self.task_type == "classification" else \
            KFold(n_splits=self.cv_folds, shuffle=True, random_state=42)
        
        if self.task_type == "classification":
            scoring = ['accuracy', 'roc_auc', 'f1_weighted']
        else:
            scoring = ['neg_mean_squared_error', 'neg_root_mean_squared_error', 'r2']
        
        results = {}
        for metric in scoring:
            try:
                scores = cross_val_score(
                    model.model, X, y, cv=cv, scoring=metric, n_jobs=self.n_jobs
                )
                results[metric] = {
                    "mean": float(scores.mean()),
                    "std": float(scores.std()),
                    "scores": scores.tolist()
                }
            except Exception as e:
                logger.warning(f"CV metric {metric} failed: {e}")
        
        return results
    
    def get_best_model(self) -> Optional[Any]:
        """Get the best trained model"""
        return self._best_model
    
    def get_training_results(self) -> Dict[str, Any]:
        """Get complete training results"""
        return self._training_results
    
    def get_best_algorithm(self) -> Optional[str]:
        """Get name of best performing algorithm"""
        return self._best_algorithm
    
    def save_best_model(self, path: str) -> None:
        """Save the best model to ONNX format"""
        if self._best_model is None:
            raise ValueError("No model trained yet")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._best_model.save_onnx(path)
        logger.info(f"Best model saved to {path}")
    
    def get_comparison_report(self) -> pd.DataFrame:
        """
        Get comparison DataFrame of all trained models
        
        Returns:
            DataFrame with algorithm comparison
        """
        if not self._training_results.get("algorithms"):
            return pd.DataFrame()
        
        rows = []
        for algo, result in self._training_results["algorithms"].items():
            if result.get("status") != "success":
                continue
            
            metrics = result.get("metrics", {})
            cv = result.get("cv_scores", {})
            
            row = {
                "algorithm": algo,
                "primary_metric": result.get("primary_metric"),
            }
            row.update(metrics)
            
            # Add CV scores
            for metric_name, cv_result in cv.items():
                if isinstance(cv_result, dict):
                    row[f"cv_{metric_name}_mean"] = cv_result.get("mean")
                    row[f"cv_{metric_name}_std"] = cv_result.get("std")
            
            rows.append(row)
        
        return pd.DataFrame(rows)
