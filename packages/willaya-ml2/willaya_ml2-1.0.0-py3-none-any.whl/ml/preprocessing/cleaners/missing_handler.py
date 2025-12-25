"""
Missing Value Handler
Handles missing values in DataFrames with multiple strategies
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer, KNNImputer

from .base import BaseCleaner


class MissingValueHandler(BaseCleaner):
    """
    Handles missing values using various strategies
    
    Strategies:
        - drop: Drop rows with missing values
        - mean: Fill with column mean (numeric)
        - median: Fill with column median (numeric)
        - mode: Fill with most frequent value
        - constant: Fill with a constant value
        - knn: K-nearest neighbors imputation
        - ffill: Forward fill
        - bfill: Backward fill
        - interpolate: Linear interpolation
    """
    
    VALID_STRATEGIES = [
        'drop', 'mean', 'median', 'mode', 'constant', 
        'knn', 'ffill', 'bfill', 'interpolate'
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize MissingValueHandler
        
        Config options:
            - strategy: Default strategy for all columns
            - fill_value: Value for 'constant' strategy
            - per_column: Dict[column_name, {strategy, fill_value}]
            - knn_neighbors: Number of neighbors for KNN imputation
        """
        super().__init__(config)
        
        self.strategy = self.config.get('strategy', 'median')
        self.fill_value = self.config.get('fill_value', None)
        self.per_column = self.config.get('per_column', {})
        self.knn_neighbors = self.config.get('knn_neighbors', 5)
        
        # Fitted values
        self._fill_values: Dict[str, Any] = {}
        self._knn_imputer: Optional[KNNImputer] = None
        self._numeric_columns: List[str] = []
        self._categorical_columns: List[str] = []
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'MissingValueHandler':
        """
        Fit the handler - calculate fill values for each column
        """
        self._validate_input(df)
        
        # Identify column types (including nullable integer types)
        numeric_types = [np.number]
        self._numeric_columns = df.select_dtypes(include=numeric_types).columns.tolist()
        # Also check for nullable integer types (Int64, Int32, etc.)
        for col in df.columns:
            if hasattr(df[col].dtype, 'name') and df[col].dtype.name.startswith('Int'):
                if col not in self._numeric_columns:
                    self._numeric_columns.append(col)

        self._categorical_columns = df.select_dtypes(
            include=['object', 'category', 'bool']
        ).columns.tolist()
        
        # Calculate fill values for each column
        self._fill_values = {}
        columns_with_missing = df.columns[df.isna().any()].tolist()
        self._affected_columns = columns_with_missing
        
        for column in columns_with_missing:
            strategy = self._get_column_strategy(column)
            
            if strategy == 'drop':
                self._fill_values[column] = None
            elif strategy == 'mean':
                if column in self._numeric_columns:
                    self._fill_values[column] = df[column].mean()
                else:
                    # Fallback to mode for non-numeric
                    self._fill_values[column] = df[column].mode().iloc[0] if not df[column].mode().empty else None
            elif strategy == 'median':
                if column in self._numeric_columns:
                    self._fill_values[column] = df[column].median()
                else:
                    self._fill_values[column] = df[column].mode().iloc[0] if not df[column].mode().empty else None
            elif strategy == 'mode':
                mode_result = df[column].mode()
                self._fill_values[column] = mode_result.iloc[0] if not mode_result.empty else None
            elif strategy == 'constant':
                col_config = self.per_column.get(column, {})
                self._fill_values[column] = col_config.get('fill_value', self.fill_value)
            elif strategy == 'knn':
                # KNN will be fitted separately
                self._fill_values[column] = 'knn'
            else:
                # ffill, bfill, interpolate - no pre-calculation needed
                self._fill_values[column] = strategy
        
        # Fit KNN imputer if needed
        if 'knn' in self._fill_values.values():
            knn_columns = [col for col, val in self._fill_values.items() if val == 'knn']
            numeric_knn = [col for col in knn_columns if col in self._numeric_columns]
            if numeric_knn:
                self._knn_imputer = KNNImputer(n_neighbors=self.knn_neighbors)
                self._knn_imputer.fit(df[numeric_knn])
        
        # Store fitting stats
        self._fit_stats = {
            "columns_with_missing": columns_with_missing,
            "fill_values": {k: str(v) for k, v in self._fill_values.items()},
            "missing_counts": df[columns_with_missing].isna().sum().to_dict()
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply missing value handling
        """
        self._validate_fitted()
        
        df_result = df.copy()
        rows_before = len(df_result)
        self._affected_rows = 0
        
        # Track which rows had missing values
        rows_with_missing = df_result.isna().any(axis=1)
        
        for column, fill_value in self._fill_values.items():
            if column not in df_result.columns:
                continue
            
            strategy = self._get_column_strategy(column)
            
            if strategy == 'drop':
                # Mark for dropping (will drop at end)
                continue
            elif strategy == 'ffill':
                df_result[column] = df_result[column].fillna(method='ffill')
            elif strategy == 'bfill':
                df_result[column] = df_result[column].fillna(method='bfill')
            elif strategy == 'interpolate':
                df_result[column] = df_result[column].interpolate(method='linear')
            elif strategy == 'knn' and self._knn_imputer is not None:
                # Apply KNN imputation
                knn_columns = [col for col, val in self._fill_values.items() 
                              if val == 'knn' and col in self._numeric_columns]
                if column in knn_columns:
                    imputed = self._knn_imputer.transform(df_result[knn_columns])
                    df_result[knn_columns] = imputed
            else:
                # Simple fill with calculated value
                if fill_value is not None:
                    # Handle nullable integer dtypes (Int64, Int32, etc.)
                    if hasattr(df_result[column].dtype, 'name') and df_result[column].dtype.name.startswith('Int'):
                        # Convert float fill value to int for nullable integer columns
                        fill_value_converted = int(fill_value) if not pd.isna(fill_value) else fill_value
                        df_result[column] = df_result[column].fillna(fill_value_converted)
                    else:
                        df_result[column] = df_result[column].fillna(fill_value)
        
        # Handle 'drop' strategy
        drop_columns = [col for col, val in self._fill_values.items() 
                       if val is None and self._get_column_strategy(col) == 'drop']
        if drop_columns:
            df_result = df_result.dropna(subset=drop_columns)
        
        self._affected_rows = rows_with_missing.sum()
        
        return df_result
    
    def _get_column_strategy(self, column: str) -> str:
        """Get the strategy for a specific column"""
        if column in self.per_column:
            return self.per_column[column].get('strategy', self.strategy)
        return self.strategy
    
    def get_missing_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a report of missing values in DataFrame
        """
        missing_counts = df.isna().sum()
        missing_percent = (df.isna().sum() / len(df) * 100).round(2)
        
        report = {
            "total_missing": int(missing_counts.sum()),
            "total_missing_percent": round(missing_counts.sum() / (len(df) * len(df.columns)) * 100, 2),
            "columns": {}
        }
        
        for column in df.columns:
            if missing_counts[column] > 0:
                report["columns"][column] = {
                    "missing_count": int(missing_counts[column]),
                    "missing_percent": float(missing_percent[column]),
                    "strategy_to_apply": self._get_column_strategy(column)
                }
        
        return report
