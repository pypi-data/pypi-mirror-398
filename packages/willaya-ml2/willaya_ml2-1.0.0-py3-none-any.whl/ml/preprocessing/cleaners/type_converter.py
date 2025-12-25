"""
Type Converter
Handles data type conversions in DataFrames
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

from .base import BaseCleaner


class TypeConverter(BaseCleaner):
    """
    Handles data type conversions with auto-detection support
    
    Supported conversions:
        - int/integer: Convert to integer
        - float: Convert to float
        - str/string: Convert to string
        - bool/boolean: Convert to boolean
        - datetime: Convert to datetime
        - category: Convert to categorical
    """
    
    TYPE_MAPPING = {
        'int': 'int64',
        'integer': 'int64',
        'float': 'float64',
        'str': 'object',
        'string': 'object',
        'bool': 'bool',
        'boolean': 'bool',
        'datetime': 'datetime64[ns]',
        'category': 'category'
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize TypeConverter
        
        Config options:
            - conversions: List of {column, to_type} dicts
            - auto_detect: Whether to auto-detect types (default: True)
            - datetime_formats: Dict of column -> datetime format
        """
        super().__init__(config)
        
        self.conversions = self.config.get('conversions', [])
        self.auto_detect = self.config.get('auto_detect', True)
        self.datetime_formats = self.config.get('datetime_formats', {})
        
        # Fitted values
        self._detected_conversions: Dict[str, str] = {}
        self._conversion_errors: List[Dict[str, Any]] = []
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'TypeConverter':
        """
        Fit the converter - detect appropriate types
        """
        self._validate_input(df)
        
        self._detected_conversions = {}
        self._conversion_errors = []
        
        # Process explicit conversions
        for conv in self.conversions:
            column = conv.get('column')
            to_type = conv.get('to_type')
            
            if column in df.columns and to_type:
                self._detected_conversions[column] = to_type
        
        # Auto-detect types if enabled
        if self.auto_detect:
            for column in df.columns:
                if column not in self._detected_conversions:
                    detected = self._auto_detect_type(df[column])
                    if detected and detected != str(df[column].dtype):
                        self._detected_conversions[column] = detected
        
        self._affected_columns = list(self._detected_conversions.keys())
        
        # Store fitting stats
        self._fit_stats = {
            "detected_conversions": self._detected_conversions,
            "auto_detect": self.auto_detect,
            "original_dtypes": {col: str(df[col].dtype) for col in self._affected_columns}
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply type conversions
        """
        self._validate_fitted()
        
        df_result = df.copy()
        self._conversion_errors = []
        self._affected_rows = 0
        
        for column, target_type in self._detected_conversions.items():
            if column not in df_result.columns:
                continue
            
            try:
                df_result[column] = self._convert_column(
                    df_result[column], 
                    target_type, 
                    column
                )
            except Exception as e:
                self._conversion_errors.append({
                    "column": column,
                    "target_type": target_type,
                    "error": str(e)
                })
        
        return df_result
    
    def _auto_detect_type(self, series: pd.Series) -> Optional[str]:
        """
        Auto-detect the best type for a series
        """
        # Skip if already optimal
        if series.dtype == 'object':
            # Try numeric
            try:
                numeric_series = pd.to_numeric(series.dropna(), errors='raise')
                if (numeric_series == numeric_series.astype(int)).all():
                    return 'int'
                return 'float'
            except:
                pass
            
            # Try datetime
            try:
                pd.to_datetime(series.dropna(), errors='raise')
                return 'datetime'
            except:
                pass
            
            # Try boolean
            unique_vals = series.dropna().unique()
            if len(unique_vals) <= 2:
                bool_vals = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}
                if all(str(v).lower() in bool_vals for v in unique_vals):
                    return 'bool'
            
            # Check if categorical is better
            if len(unique_vals) < len(series) * 0.5:  # Less than 50% unique
                return 'category'
        
        # Check if float can be int
        if series.dtype == 'float64':
            non_null = series.dropna()
            if len(non_null) > 0 and (non_null == non_null.astype(int)).all():
                return 'int'
        
        return None
    
    def _convert_column(
        self, 
        series: pd.Series, 
        target_type: str, 
        column: str
    ) -> pd.Series:
        """
        Convert a series to target type
        """
        target_dtype = self.TYPE_MAPPING.get(target_type, target_type)
        
        if target_type in ['int', 'integer']:
            # Handle missing values for integer conversion
            return pd.to_numeric(series, errors='coerce').astype('Int64')
        
        elif target_type == 'float':
            return pd.to_numeric(series, errors='coerce')
        
        elif target_type in ['str', 'string']:
            return series.astype(str).replace('nan', np.nan)
        
        elif target_type in ['bool', 'boolean']:
            return self._convert_to_bool(series)
        
        elif target_type == 'datetime':
            fmt = self.datetime_formats.get(column)
            if fmt:
                return pd.to_datetime(series, format=fmt, errors='coerce')
            return pd.to_datetime(series, errors='coerce', infer_datetime_format=True)
        
        elif target_type == 'category':
            return series.astype('category')
        
        else:
            return series.astype(target_dtype)
    
    def _convert_to_bool(self, series: pd.Series) -> pd.Series:
        """
        Convert series to boolean
        """
        # Map common boolean representations
        bool_map = {
            'true': True, 'false': False,
            'yes': True, 'no': False,
            'y': True, 'n': False,
            't': True, 'f': False,
            '1': True, '0': False,
            1: True, 0: False,
            1.0: True, 0.0: False
        }
        
        def convert_value(val):
            if pd.isna(val):
                return np.nan
            if isinstance(val, bool):
                return val
            key = str(val).lower() if isinstance(val, str) else val
            return bool_map.get(key, np.nan)
        
        result = series.apply(convert_value)
        return result.astype('boolean')
    
    def get_type_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a report of data types in DataFrame
        """
        report = {
            "current_dtypes": {},
            "suggested_conversions": {},
            "memory_usage": {}
        }
        
        for column in df.columns:
            current_dtype = str(df[column].dtype)
            report["current_dtypes"][column] = current_dtype
            report["memory_usage"][column] = int(df[column].memory_usage(deep=True))
            
            # Detect suggested conversion
            suggested = self._auto_detect_type(df[column])
            if suggested and suggested != current_dtype:
                report["suggested_conversions"][column] = {
                    "from": current_dtype,
                    "to": suggested,
                    "reason": self._get_conversion_reason(df[column], suggested)
                }
        
        report["total_memory_mb"] = round(
            sum(report["memory_usage"].values()) / 1024 / 1024, 2
        )
        
        return report
    
    def _get_conversion_reason(self, series: pd.Series, target_type: str) -> str:
        """
        Get reason for suggesting a type conversion
        """
        reasons = {
            'int': "Column contains only integer values",
            'float': "Column contains numeric values with decimals",
            'bool': "Column contains only boolean-like values",
            'datetime': "Column contains date/time values",
            'category': "Column has limited unique values, category saves memory"
        }
        return reasons.get(target_type, "Type optimization")
