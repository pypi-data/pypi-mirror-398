"""
Numerical Scaler
Handles scaling/normalization of numerical variables
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, 
    MaxAbsScaler, Normalizer
)

from .base import BaseProcessor


class NumericalScaler(BaseProcessor):
    """
    Scales numerical variables using various strategies
    
    Strategies:
        - standard: Z-score normalization (mean=0, std=1)
        - minmax: Scale to [0, 1] range
        - robust: Scale using median and IQR (outlier-robust)
        - maxabs: Scale by maximum absolute value
        - normalizer: Normalize samples to unit norm
        - none: No scaling
    """
    
    VALID_STRATEGIES = ['standard', 'minmax', 'robust', 'maxabs', 'normalizer', 'none']
    
    SCALER_CLASSES = {
        'standard': StandardScaler,
        'minmax': MinMaxScaler,
        'robust': RobustScaler,
        'maxabs': MaxAbsScaler,
        'normalizer': Normalizer
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize NumericalScaler
        
        Config options:
            - default_strategy: Default scaling strategy
            - per_column: Dict of column-specific strategies
            - exclude_columns: Columns to exclude from scaling
        """
        super().__init__(config)
        
        self.default_strategy = self.config.get('default_strategy', 'standard')
        self.per_column = self.config.get('per_column', {})
        self.exclude_columns = self.config.get('exclude_columns', [])
        
        # Fitted scalers
        self._scalers: Dict[str, Any] = {}
        self._numeric_columns: List[str] = []
        self._column_strategies: Dict[str, str] = {}
        self._scaling_params: Dict[str, Dict[str, float]] = {}
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'NumericalScaler':
        """
        Fit scalers for numerical columns
        """
        self._validate_input(df)
        
        self._scalers = {}
        self._scaling_params = {}
        
        # Identify numeric columns
        self._numeric_columns = df.select_dtypes(
            include=[np.number]
        ).columns.tolist()
        
        # Exclude specified columns
        self._numeric_columns = [
            col for col in self._numeric_columns 
            if col not in self.exclude_columns
        ]
        
        self._feature_names_in = self._numeric_columns.copy()
        self._feature_names_out = self._numeric_columns.copy()
        
        for column in self._numeric_columns:
            strategy = self._get_column_strategy(column)
            self._column_strategies[column] = strategy
            
            if strategy == 'none':
                continue
            
            # Get scaler class
            scaler_class = self.SCALER_CLASSES.get(strategy)
            if not scaler_class:
                continue
            
            # Create and fit scaler
            scaler = scaler_class()
            
            # Fit on non-null values
            valid_data = df[column].dropna().values.reshape(-1, 1)
            if len(valid_data) > 0:
                scaler.fit(valid_data)
                self._scalers[column] = scaler
                
                # Store scaling parameters for reference
                self._scaling_params[column] = self._extract_params(scaler, strategy)
        
        # Store fitting stats
        self._fit_stats = {
            "numeric_columns": self._numeric_columns,
            "strategies_used": self._column_strategies,
            "scaling_params": self._scaling_params
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply scaling transformations
        """
        self._validate_fitted()
        
        df_result = df.copy()
        
        for column in self._numeric_columns:
            if column not in df_result.columns:
                continue
            
            strategy = self._column_strategies.get(column, 'none')
            
            if strategy == 'none' or column not in self._scalers:
                continue
            
            scaler = self._scalers[column]
            
            # Handle nulls
            null_mask = df_result[column].isna()
            
            if not null_mask.all():
                # Convert column to float64 first to avoid dtype issues
                df_result[column] = df_result[column].astype('float64')
                
                valid_data = df_result.loc[~null_mask, column].values.reshape(-1, 1)
                scaled = scaler.transform(valid_data)
                
                df_result.loc[~null_mask, column] = scaled.flatten()
        
        return df_result
    
    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse scaling transformations
        """
        self._validate_fitted()
        
        df_result = df.copy()
        
        for column in self._numeric_columns:
            if column not in df_result.columns:
                continue
            
            if column not in self._scalers:
                continue
            
            scaler = self._scalers[column]
            
            # Handle nulls
            null_mask = df_result[column].isna()
            
            if not null_mask.all():
                valid_data = df_result.loc[~null_mask, column].values.reshape(-1, 1)
                
                # Check if scaler has inverse_transform
                if hasattr(scaler, 'inverse_transform'):
                    unscaled = scaler.inverse_transform(valid_data)
                    df_result.loc[~null_mask, column] = unscaled.flatten()
        
        return df_result
    
    def _get_column_strategy(self, column: str) -> str:
        """Get scaling strategy for a column"""
        if column in self.per_column:
            return self.per_column[column].get('strategy', self.default_strategy)
        return self.default_strategy
    
    def _extract_params(self, scaler: Any, strategy: str) -> Dict[str, float]:
        """Extract scaling parameters from fitted scaler"""
        params = {}
        
        if strategy == 'standard':
            params['mean'] = float(scaler.mean_[0])
            params['std'] = float(scaler.scale_[0])
        elif strategy == 'minmax':
            params['min'] = float(scaler.data_min_[0])
            params['max'] = float(scaler.data_max_[0])
            params['scale'] = float(scaler.scale_[0])
        elif strategy == 'robust':
            params['center'] = float(scaler.center_[0])
            params['scale'] = float(scaler.scale_[0])
        elif strategy == 'maxabs':
            params['max_abs'] = float(scaler.max_abs_[0])
        
        return params
    
    def get_scaling_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate report of scaling transformations
        """
        report = {
            "numeric_columns": [],
            "total_columns_scaled": 0
        }
        
        for col in df.select_dtypes(include=[np.number]).columns:
            if col in self.exclude_columns:
                continue
            
            strategy = self._get_column_strategy(col)
            
            col_info = {
                "column": col,
                "strategy": strategy,
                "current_stats": {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max())
                }
            }
            
            if strategy != 'none':
                report["total_columns_scaled"] += 1
            
            report["numeric_columns"].append(col_info)
        
        return report
    
    def get_state(self) -> Dict[str, Any]:
        """Get scaler state for serialization"""
        state = super().get_state()
        state["scaling_params"] = self._scaling_params
        state["column_strategies"] = self._column_strategies
        return state
    
    def set_state(self, state: Dict[str, Any]) -> 'NumericalScaler':
        """Restore scaler state"""
        super().set_state(state)
        self._scaling_params = state.get("scaling_params", {})
        self._column_strategies = state.get("column_strategies", {})
        return self
