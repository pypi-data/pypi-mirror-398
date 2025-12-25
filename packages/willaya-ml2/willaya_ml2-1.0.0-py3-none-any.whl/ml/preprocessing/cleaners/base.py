"""
Base Cleaner
Abstract base class for all data cleaners
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


class BaseCleaner(ABC):
    """
    Abstract base class for data cleaning operations
    All cleaners must implement fit, transform, and fit_transform
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize cleaner with configuration
        
        Args:
            config: Cleaner-specific configuration
        """
        self.config = config or {}
        self._is_fitted = False
        self._fit_stats: Dict[str, Any] = {}
        self._affected_columns: List[str] = []
        self._affected_rows: int = 0
    
    @property
    def is_fitted(self) -> bool:
        """Check if cleaner has been fitted"""
        return self._is_fitted
    
    @property
    def fit_stats(self) -> Dict[str, Any]:
        """Get statistics from fitting"""
        return self._fit_stats
    
    @property
    def affected_columns(self) -> List[str]:
        """Get list of columns affected by cleaning"""
        return self._affected_columns
    
    @property
    def affected_rows(self) -> int:
        """Get count of rows affected by cleaning"""
        return self._affected_rows
    
    @abstractmethod
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'BaseCleaner':
        """
        Fit the cleaner to data (learn parameters)
        
        Args:
            df: Input DataFrame
            y: Optional target series (for supervised methods)
        
        Returns:
            self
        """
        pass
    
    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply cleaning transformation
        
        Args:
            df: Input DataFrame
        
        Returns:
            Cleaned DataFrame
        """
        pass
    
    def fit_transform(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        Fit and transform in one step
        
        Args:
            df: Input DataFrame
            y: Optional target series
        
        Returns:
            Cleaned DataFrame
        """
        return self.fit(df, y).transform(df)
    
    def get_params(self) -> Dict[str, Any]:
        """Get cleaner parameters"""
        return self.config.copy()
    
    def set_params(self, **params) -> 'BaseCleaner':
        """Set cleaner parameters"""
        self.config.update(params)
        return self
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get cleaner state for serialization
        
        Returns:
            Dict containing cleaner state
        """
        return {
            "config": self.config,
            "is_fitted": self._is_fitted,
            "fit_stats": self._fit_stats,
            "affected_columns": self._affected_columns
        }
    
    def set_state(self, state: Dict[str, Any]) -> 'BaseCleaner':
        """
        Restore cleaner state from serialization
        
        Args:
            state: Previously saved state dict
        
        Returns:
            self
        """
        self.config = state.get("config", {})
        self._is_fitted = state.get("is_fitted", False)
        self._fit_stats = state.get("fit_stats", {})
        self._affected_columns = state.get("affected_columns", [])
        return self
    
    def get_transformation_report(self) -> Dict[str, Any]:
        """
        Get report of transformations applied
        
        Returns:
            Report dict with transformation details
        """
        return {
            "cleaner_type": self.__class__.__name__,
            "is_fitted": self._is_fitted,
            "affected_columns": self._affected_columns,
            "affected_rows": self._affected_rows,
            "fit_stats": self._fit_stats,
            "config": self.config
        }
    
    def _validate_input(self, df: pd.DataFrame) -> None:
        """
        Validate input DataFrame
        
        Args:
            df: DataFrame to validate
        
        Raises:
            ValueError: If DataFrame is invalid
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("Input DataFrame is empty")
    
    def _validate_fitted(self) -> None:
        """
        Validate that cleaner has been fitted
        
        Raises:
            ValueError: If cleaner hasn't been fitted
        """
        if not self._is_fitted:
            raise ValueError(
                f"{self.__class__.__name__} must be fitted before transform. "
                "Call fit() or fit_transform() first."
            )
