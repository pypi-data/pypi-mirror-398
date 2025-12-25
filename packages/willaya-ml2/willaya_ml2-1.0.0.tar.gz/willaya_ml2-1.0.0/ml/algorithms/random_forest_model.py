"""
Random Forest Model Implementation
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier as RFClassifier, RandomForestRegressor as RFRegressor
from pathlib import Path

from .base import BaseMLModel, ClassificationMixin, RegressionMixin


class RandomForestClassifier(ClassificationMixin, BaseMLModel):
    """Random Forest Classifier Implementation"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "random_forest_classifier"
        
        # Default hyperparameters
        self.default_params = {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'random_state': 42,
            'n_jobs': -1
        }
        
        # Merge with provided params
        params = {**self.default_params, **self.hyperparameters}
        self.model = RFClassifier(**params)
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'RandomForestClassifier':
        """Train the Random Forest classifier"""
        self.feature_names = list(X.columns)
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities"""
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def save_onnx(self, path: str) -> str:
        """Export to ONNX format"""
        import logging
        logger = logging.getLogger(__name__)
        
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        
        logger.info(f"RandomForest save_onnx: feature_names count = {len(self.feature_names)}")
        logger.info(f"RandomForest save_onnx: feature_names = {self.feature_names[:10]}...")
        
        initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]
        
        try:
            onnx_model = convert_sklearn(
                self.model,
                initial_types=initial_types,
                target_opset=12
            )
        except Exception as e:
            logger.error(f"RandomForest ONNX conversion failed: {e}")
            logger.error(f"Feature names: {self.feature_names}")
            raise
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(onnx_model.SerializeToString())
        
        return path
    
    def load_onnx(self, path: str) -> 'RandomForestClassifier':
        """Load from ONNX format"""
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self


class RandomForestRegressor(RegressionMixin, BaseMLModel):
    """Random Forest Regressor Implementation"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "random_forest_regressor"
        
        # Default hyperparameters
        self.default_params = {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'random_state': 42,
            'n_jobs': -1
        }
        
        # Merge with provided params
        params = {**self.default_params, **self.hyperparameters}
        self.model = RFRegressor(**params)
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'RandomForestRegressor':
        """Train the Random Forest regressor"""
        self.feature_names = list(X.columns)
        self.model.fit(X, y)
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
        import logging
        logger = logging.getLogger(__name__)
        
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        
        logger.info(f"RandomForestRegressor save_onnx: feature_names count = {len(self.feature_names)}")
        logger.info(f"RandomForestRegressor save_onnx: feature_names = {self.feature_names[:10]}...")
        
        initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]        
        
        try:
            onnx_model = convert_sklearn(
                self.model,
                initial_types=initial_types,
                target_opset=12
            )
        except Exception as e:
            logger.error(f"RandomForestRegressor ONNX conversion failed: {e}")
            logger.error(f"Feature names: {self.feature_names}")
            raise
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(onnx_model.SerializeToString())
        
        return path
    
    def load_onnx(self, path: str) -> 'RandomForestRegressor':
        """Load from ONNX format"""
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self
