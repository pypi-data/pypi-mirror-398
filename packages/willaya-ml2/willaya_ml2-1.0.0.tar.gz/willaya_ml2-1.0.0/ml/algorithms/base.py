"""
Base Model Interface
All ML algorithms must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd


class BaseMLModel(ABC):
    """
    Abstract base class for all ML models
    Ensures consistent interface across different algorithms
    """
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        self.hyperparameters = hyperparameters or {}
        self.model = None
        self.feature_names: List[str] = []
        self.is_fitted = False
        self._model_type = "base"
    
    @property
    def model_type(self) -> str:
        return self._model_type
    
    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'BaseMLModel':
        """
        Train the model
        
        Args:
            X: Training features
            y: Training labels
            eval_set: Optional validation set (X_val, y_val)
        
        Returns:
            self
        """
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions
        
        Args:
            X: Features to predict on
        
        Returns:
            Predictions array
        """
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities (for classification)
        
        Args:
            X: Features to predict on
        
        Returns:
            Probabilities array
        """
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores
        
        Returns:
            Dict mapping feature name to importance score
        """
        pass
    
    @abstractmethod
    def save_onnx(self, path: str) -> str:
        """
        Export model to ONNX format
        
        Args:
            path: Path to save the model
        
        Returns:
            Path where model was saved
        """
        pass
    
    @abstractmethod
    def load_onnx(self, path: str) -> 'BaseMLModel':
        """
        Load model from ONNX format
        
        Args:
            path: Path to load the model from
        
        Returns:
            self
        """
        pass
    
    def set_feature_names(self, feature_names: List[str]):
        """Set feature names for the model"""
        self.feature_names = feature_names
    
    def get_params(self) -> Dict[str, Any]:
        """Get model hyperparameters"""
        return self.hyperparameters.copy()
    
    def set_params(self, **params):
        """Set model hyperparameters"""
        self.hyperparameters.update(params)


class ClassificationMixin:
    """Mixin for classification models"""
    
    task_type = "classification"
    
    def get_classes(self) -> List[Any]:
        """Get class labels"""
        if hasattr(self.model, 'classes_'):
            return list(self.model.classes_)
        return []


class RegressionMixin:
    """Mixin for regression models"""
    
    task_type = "regression"
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Regression models don't have probabilities"""
        raise NotImplementedError("Regression models don't support predict_proba")
