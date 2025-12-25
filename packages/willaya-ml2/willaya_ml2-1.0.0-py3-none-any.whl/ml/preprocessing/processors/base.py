"""
Base Processor
Abstract base class for all data processors (encoding, scaling, selection)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd


class BaseProcessor(ABC):
    """
    Abstract base class for data processing operations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._is_fitted = False
        self._fit_stats: Dict[str, Any] = {}
        self._feature_names_in: List[str] = []
        self._feature_names_out: List[str] = []
    
    @property
    def is_fitted(self) -> bool:
        return self._is_fitted
    
    @property
    def fit_stats(self) -> Dict[str, Any]:
        return self._fit_stats
    
    @property
    def feature_names_in(self) -> List[str]:
        return self._feature_names_in
    
    @property
    def feature_names_out(self) -> List[str]:
        return self._feature_names_out
    
    @abstractmethod
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'BaseProcessor':
        pass
    
    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        pass
    
    def fit_transform(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> pd.DataFrame:
        return self.fit(df, y).transform(df)
    
    def get_params(self) -> Dict[str, Any]:
        return self.config.copy()
    
    def set_params(self, **params) -> 'BaseProcessor':
        self.config.update(params)
        return self
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "config": self.config,
            "is_fitted": self._is_fitted,
            "fit_stats": self._fit_stats,
            "feature_names_in": self._feature_names_in,
            "feature_names_out": self._feature_names_out
        }
    
    def set_state(self, state: Dict[str, Any]) -> 'BaseProcessor':
        self.config = state.get("config", {})
        self._is_fitted = state.get("is_fitted", False)
        self._fit_stats = state.get("fit_stats", {})
        self._feature_names_in = state.get("feature_names_in", [])
        self._feature_names_out = state.get("feature_names_out", [])
        return self
    
    def get_transformation_report(self) -> Dict[str, Any]:
        return {
            "processor_type": self.__class__.__name__,
            "is_fitted": self._is_fitted,
            "features_in": len(self._feature_names_in),
            "features_out": len(self._feature_names_out),
            "fit_stats": self._fit_stats,
            "config": self.config
        }
    
    def _validate_input(self, df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Input DataFrame is empty")
    
    def _validate_fitted(self) -> None:
        if not self._is_fitted:
            raise ValueError(
                f"{self.__class__.__name__} must be fitted before transform."
            )
