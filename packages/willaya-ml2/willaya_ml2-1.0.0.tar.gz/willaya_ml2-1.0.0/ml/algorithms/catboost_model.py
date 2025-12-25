"""
CatBoost Model Implementation
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier as CatBoostCls, CatBoostRegressor as CatBoostReg
from pathlib import Path

from .base import BaseMLModel, ClassificationMixin, RegressionMixin


class CatBoostClassifier(ClassificationMixin, BaseMLModel):
    """CatBoost Classifier Implementation"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "catboost_classifier"
        
        # Default hyperparameters
        self.default_params = {
            'iterations': 100,
            'depth': 6,
            'learning_rate': 0.1,
            'loss_function': 'Logloss',
            'random_seed': 42,
            'verbose': False
        }
        
        # Merge with provided params
        params = {**self.default_params, **self.hyperparameters}
        self.model = CatBoostCls(**params)
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'CatBoostClassifier':
        """Train the CatBoost classifier"""
        self.feature_names = list(X.columns)
        
        fit_params = {}
        if eval_set:
            fit_params['eval_set'] = eval_set
        
        self.model.fit(X, y, **fit_params)
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X).flatten()
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities"""
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def save_onnx(self, path: str) -> str:
        """Export to ONNX format"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(
            path,
            format="onnx",
            export_parameters={'onnx_domain': 'ai.catboost'}
        )
        return path
    
    def load_onnx(self, path: str) -> 'CatBoostClassifier':
        """Load from ONNX format"""
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self


class CatBoostRegressor(RegressionMixin, BaseMLModel):
    """CatBoost Regressor Implementation"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "catboost_regressor"
        
        # Default hyperparameters
        self.default_params = {
            'iterations': 100,
            'depth': 6,
            'learning_rate': 0.1,
            'loss_function': 'RMSE',
            'random_seed': 42,
            'verbose': False
        }
        
        # Merge with provided params
        params = {**self.default_params, **self.hyperparameters}
        self.model = CatBoostReg(**params)
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'CatBoostRegressor':
        """Train the CatBoost regressor"""
        self.feature_names = list(X.columns)
        
        fit_params = {}
        if eval_set:
            fit_params['eval_set'] = eval_set
        
        self.model.fit(X, y, **fit_params)
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Not supported for regression"""
        raise NotImplementedError("Regression models don't support predict_proba")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def save_onnx(self, path: str) -> str:
        """Export to ONNX format"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(
            path,
            format="onnx",
            export_parameters={'onnx_domain': 'ai.catboost'}
        )
        return path
    
    def load_onnx(self, path: str) -> 'CatBoostRegressor':
        """Load from ONNX format"""
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self
