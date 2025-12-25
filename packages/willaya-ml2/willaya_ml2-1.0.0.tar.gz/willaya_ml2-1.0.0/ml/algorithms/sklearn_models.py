"""
Scikit-learn Model Implementations
Includes: Logistic Regression, Linear Regression, SVM
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.preprocessing import StandardScaler
from pathlib import Path

from .base import BaseMLModel, ClassificationMixin, RegressionMixin


# ============== Logistic Regression ==============

class LogisticRegressionClassifier(ClassificationMixin, BaseMLModel):
    """Logistic Regression Classifier"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "logistic_regression"
        
        self.default_params = {
            'C': 1.0,
            'max_iter': 1000,
            'random_state': 42
        }
        
        params = {**self.default_params, **self.hyperparameters}
        self.model = LogisticRegression(**params)
        self.scaler = StandardScaler()
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'LogisticRegressionClassifier':
        self.feature_names = list(X.columns)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        importance = np.abs(self.model.coef_[0])
        return dict(zip(self.feature_names, importance))
    
    def save_onnx(self, path: str) -> str:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        from sklearn.pipeline import Pipeline
        
        pipeline = Pipeline([('scaler', self.scaler), ('model', self.model)])
        initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]
        
        onnx_model = convert_sklearn(pipeline, initial_types=initial_types, target_opset=12)
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(onnx_model.SerializeToString())
        return path
    
    def load_onnx(self, path: str) -> 'LogisticRegressionClassifier':
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self


# ============== Linear Regression ==============

class LinearRegressionModel(RegressionMixin, BaseMLModel):
    """Linear Regression Model"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "linear_regression"
        
        self.model = LinearRegression()
        self.scaler = StandardScaler()
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'LinearRegressionModel':
        self.feature_names = list(X.columns)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError("Regression models don't support predict_proba")
    
    def get_feature_importance(self) -> Dict[str, float]:
        importance = np.abs(self.model.coef_)
        return dict(zip(self.feature_names, importance))
    
    def save_onnx(self, path: str) -> str:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        from sklearn.pipeline import Pipeline
        
        pipeline = Pipeline([('scaler', self.scaler), ('model', self.model)])
        initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]
        
        onnx_model = convert_sklearn(pipeline, initial_types=initial_types, target_opset=12)
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(onnx_model.SerializeToString())
        return path
    
    def load_onnx(self, path: str) -> 'LinearRegressionModel':
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self


# ============== SVM Classifier ==============

class SVMClassifier(ClassificationMixin, BaseMLModel):
    """SVM Classifier"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "svm_classifier"
        
        self.default_params = {
            'C': 1.0,
            'kernel': 'rbf',
            'probability': True,
            'random_state': 42
        }
        
        params = {**self.default_params, **self.hyperparameters}
        self.model = SVC(**params)
        self.scaler = StandardScaler()
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'SVMClassifier':
        self.feature_names = list(X.columns)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        # SVM doesn't have direct feature importance
        return {name: 0.0 for name in self.feature_names}
    
    def save_onnx(self, path: str) -> str:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        from sklearn.pipeline import Pipeline
        
        pipeline = Pipeline([('scaler', self.scaler), ('model', self.model)])
        initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]
        
        onnx_model = convert_sklearn(pipeline, initial_types=initial_types, target_opset=12)
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(onnx_model.SerializeToString())
        return path
    
    def load_onnx(self, path: str) -> 'SVMClassifier':
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self


# ============== SVM Regressor ==============

class SVMRegressor(RegressionMixin, BaseMLModel):
    """SVM Regressor"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "svm_regressor"
        
        self.default_params = {
            'C': 1.0,
            'kernel': 'rbf'
        }
        
        params = {**self.default_params, **self.hyperparameters}
        self.model = SVR(**params)
        self.scaler = StandardScaler()
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'SVMRegressor':
        self.feature_names = list(X.columns)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError("Regression models don't support predict_proba")
    
    def get_feature_importance(self) -> Dict[str, float]:
        return {name: 0.0 for name in self.feature_names}
    
    def save_onnx(self, path: str) -> str:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        from sklearn.pipeline import Pipeline
        
        pipeline = Pipeline([('scaler', self.scaler), ('model', self.model)])
        initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]
        
        onnx_model = convert_sklearn(pipeline, initial_types=initial_types, target_opset=12)
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(onnx_model.SerializeToString())
        return path
    
    def load_onnx(self, path: str) -> 'SVMRegressor':
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        return self
