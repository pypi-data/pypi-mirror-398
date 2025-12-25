"""
XGBoost Model Implementation
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb
from pathlib import Path

from .base import BaseMLModel, ClassificationMixin, RegressionMixin


class XGBoostClassifier(ClassificationMixin, BaseMLModel):
    """XGBoost Classifier Implementation"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "xgboost_classifier"
        
        # Default hyperparameters
        self.default_params = {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'use_label_encoder': False,
            'random_state': 42
        }
        
        # Merge with provided params
        params = {**self.default_params, **self.hyperparameters}
        self.model = xgb.XGBClassifier(**params)
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'XGBoostClassifier':
        """Train the XGBoost classifier"""
        self.feature_names = list(X.columns)
        
        fit_params = {}
        if eval_set:
            fit_params['eval_set'] = [eval_set]
            fit_params['verbose'] = False
        
        self.model.fit(X, y, **fit_params)
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
        """Export to ONNX format using onnxmltools for XGBoost, with pickle fallback"""
        import logging
        import pickle
        logger = logging.getLogger(__name__)
        
        logger.info(f"XGBoostClassifier save_onnx: feature_names count = {len(self.feature_names)}")
        logger.info(f"XGBoostClassifier save_onnx: feature_names = {self.feature_names[:10]}...")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Try ONNX first, fall back to pickle if it fails
        try:
            from onnxmltools import convert_xgboost
            from onnxmltools.convert.common.data_types import FloatTensorType
            
            initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]
            
            onnx_model = convert_xgboost(
                self.model,
                initial_types=initial_types,
                target_opset=12
            )
            
            with open(path, 'wb') as f:
                f.write(onnx_model.SerializeToString())
            
            logger.info(f"XGBoostClassifier saved to ONNX format successfully")
            return path
            
        except Exception as e:
            logger.warning(f"ONNX conversion failed ({e}), falling back to pickle format")
            
            # Fall back to pickle format
            pickle_path = path.replace('.onnx', '.pkl')
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'hyperparameters': self.hyperparameters,
                'model_type': self._model_type,
                'format': 'pickle'
            }
            
            with open(pickle_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"XGBoostClassifier saved to pickle format at {pickle_path}")
            return pickle_path
    
    def load_onnx(self, path: str) -> 'XGBoostClassifier':
        """Load from ONNX or pickle format"""
        import logging
        import pickle
        logger = logging.getLogger(__name__)
        
        # Check if it's a pickle file
        if path.endswith('.pkl'):
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            self.hyperparameters = model_data.get('hyperparameters', {})
            self.is_fitted = True
            logger.info(f"XGBoostClassifier loaded from pickle format")
            return self
        
        # Otherwise try ONNX
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        logger.info(f"XGBoostClassifier loaded from ONNX format")
        return self


class XGBoostRegressor(RegressionMixin, BaseMLModel):
    """XGBoost Regressor Implementation"""
    
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self._model_type = "xgboost_regressor"
        
        # Default hyperparameters
        self.default_params = {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'reg:squarederror',
            'random_state': 42
        }
        
        # Merge with provided params
        params = {**self.default_params, **self.hyperparameters}
        self.model = xgb.XGBRegressor(**params)
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None
    ) -> 'XGBoostRegressor':
        """Train the XGBoost regressor"""
        self.feature_names = list(X.columns)
        
        fit_params = {}
        if eval_set:
            fit_params['eval_set'] = [eval_set]
            fit_params['verbose'] = False
        
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
        """Export to ONNX format using onnxmltools for XGBoost, with pickle fallback"""
        import logging
        import pickle
        logger = logging.getLogger(__name__)
        
        logger.info(f"XGBoostRegressor save_onnx: feature_names count = {len(self.feature_names)}")
        logger.info(f"XGBoostRegressor save_onnx: feature_names = {self.feature_names[:10]}...")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Try ONNX first, fall back to pickle if it fails
        try:
            from onnxmltools import convert_xgboost
            from onnxmltools.convert.common.data_types import FloatTensorType
            
            initial_types = [('input', FloatTensorType([None, len(self.feature_names)]))]
            
            onnx_model = convert_xgboost(
                self.model,
                initial_types=initial_types,
                target_opset=12
            )
            
            with open(path, 'wb') as f:
                f.write(onnx_model.SerializeToString())
            
            logger.info(f"XGBoostRegressor saved to ONNX format successfully")
            return path
            
        except Exception as e:
            logger.warning(f"ONNX conversion failed ({e}), falling back to pickle format")
            
            # Fall back to pickle format
            pickle_path = path.replace('.onnx', '.pkl')
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'hyperparameters': self.hyperparameters,
                'model_type': self._model_type,
                'format': 'pickle'
            }
            
            with open(pickle_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"XGBoostRegressor saved to pickle format at {pickle_path}")
            return pickle_path
    
    def load_onnx(self, path: str) -> 'XGBoostRegressor':
        """Load from ONNX or pickle format"""
        import logging
        import pickle
        logger = logging.getLogger(__name__)
        
        # Check if it's a pickle file
        if path.endswith('.pkl'):
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            self.hyperparameters = model_data.get('hyperparameters', {})
            self.is_fitted = True
            logger.info(f"XGBoostRegressor loaded from pickle format")
            return self
        
        # Otherwise try ONNX
        import onnxruntime as ort
        self._onnx_session = ort.InferenceSession(path)
        self.is_fitted = True
        logger.info(f"XGBoostRegressor loaded from ONNX format")
        return self
