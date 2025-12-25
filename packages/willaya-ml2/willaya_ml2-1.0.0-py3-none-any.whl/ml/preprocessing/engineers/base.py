"""
Base Engineer
Abstract base class for all feature engineers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd


class BaseEngineer(ABC):
    """
    Abstract base class for feature engineering operations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize engineer with configuration
        """
        self.config = config or {}
        self._is_fitted = False
        self._fit_stats: Dict[str, Any] = {}
        self._new_columns: List[str] = []
        self._dropped_columns: List[str] = []
    
    @property
    def is_fitted(self) -> bool:
        return self._is_fitted
    
    @property
    def fit_stats(self) -> Dict[str, Any]:
        return self._fit_stats
    
    @property
    def new_columns(self) -> List[str]:
        return self._new_columns
    
    @property
    def dropped_columns(self) -> List[str]:
        return self._dropped_columns
    
    @abstractmethod
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'BaseEngineer':
        """
        Fit the engineer to data (learn parameters if needed)
        """
        pass
    
    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply feature engineering transformation
        """
        pass
    
    def fit_transform(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        Fit and transform in one step
        """
        return self.fit(df, y).transform(df)
    
    def get_params(self) -> Dict[str, Any]:
        return self.config.copy()
    
    def set_params(self, **params) -> 'BaseEngineer':
        self.config.update(params)
        return self
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "config": self.config,
            "is_fitted": self._is_fitted,
            "fit_stats": self._fit_stats,
            "new_columns": self._new_columns,
            "dropped_columns": self._dropped_columns
        }
    
    def set_state(self, state: Dict[str, Any]) -> 'BaseEngineer':
        self.config = state.get("config", {})
        self._is_fitted = state.get("is_fitted", False)
        self._fit_stats = state.get("fit_stats", {})
        self._new_columns = state.get("new_columns", [])
        self._dropped_columns = state.get("dropped_columns", [])
        return self
    
    def get_transformation_report(self) -> Dict[str, Any]:
        return {
            "engineer_type": self.__class__.__name__,
            "is_fitted": self._is_fitted,
            "new_columns": self._new_columns,
            "dropped_columns": self._dropped_columns,
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
                f"{self.__class__.__name__} must be fitted before transform. "
                "Call fit() or fit_transform() first."
            )
