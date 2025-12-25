"""
Date Engineer
Extracts features from datetime columns
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from .base import BaseEngineer


class DateEngineer(BaseEngineer):
    """
    Extracts various features from datetime columns
    
    Features that can be extracted:
        - year, month, day, dayofweek, dayofyear
        - hour, minute, second (if time component exists)
        - quarter, week, weekofyear
        - is_weekend, is_month_start, is_month_end
        - days_since (from a reference date)
        - cyclical encoding (sin/cos for cyclic features)
    """
    
    EXTRACTABLE_FEATURES = [
        'year', 'month', 'day', 'dayofweek', 'dayofyear',
        'hour', 'minute', 'second', 'quarter', 'week', 'weekofyear',
        'is_weekend', 'is_month_start', 'is_month_end', 'is_quarter_start',
        'is_quarter_end', 'is_year_start', 'is_year_end'
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize DateEngineer
        
        Config options:
            - source_columns: List of datetime columns to process
            - extract: List of features to extract
            - drop_original: Whether to drop original datetime columns
            - cyclical_encoding: Whether to add sin/cos encoding for cyclic features
            - reference_date: Reference date for 'days_since' calculation
        """
        super().__init__(config)
        
        self.source_columns = self.config.get('source_columns', [])
        self.extract = self.config.get('extract', ['year', 'month', 'day', 'dayofweek'])
        self.drop_original = self.config.get('drop_original', False)
        self.cyclical_encoding = self.config.get('cyclical_encoding', False)
        self.reference_date = self.config.get('reference_date', None)
        
        # Fitted values
        self._datetime_columns: List[str] = []
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'DateEngineer':
        """
        Fit the engineer - identify datetime columns
        """
        self._validate_input(df)
        
        self._datetime_columns = []
        self._new_columns = []
        self._dropped_columns = []
        
        # Helper to check if column can be converted to datetime
        def is_datetime_convertible(series: pd.Series) -> bool:
            try:
                sample = series.dropna().head(100)
                if len(sample) == 0:
                    return False
                # Use format='mixed' for pandas 2.0+ (suppresses warnings)
                pd.to_datetime(sample, errors='raise', format='mixed')
                return True
            except Exception:
                return False
        
        # If source_columns specified, use those
        if self.source_columns:
            for col in self.source_columns:
                if col in df.columns:
                    if is_datetime_convertible(df[col]):
                        self._datetime_columns.append(col)
        else:
            # Auto-detect datetime columns
            self._datetime_columns = df.select_dtypes(
                include=['datetime64']
            ).columns.tolist()
            
            # Also check object columns that might be datetime
            for col in df.select_dtypes(include=['object']).columns:
                if is_datetime_convertible(df[col]):
                    self._datetime_columns.append(col)
        
        # Determine new columns
        for col in self._datetime_columns:
            for feature in self.extract:
                self._new_columns.append(f"{col}_{feature}")
            
            if self.cyclical_encoding:
                for cyclic_feat in ['month', 'dayofweek', 'hour']:
                    if cyclic_feat in self.extract:
                        self._new_columns.append(f"{col}_{cyclic_feat}_sin")
                        self._new_columns.append(f"{col}_{cyclic_feat}_cos")
            
            if self.reference_date:
                self._new_columns.append(f"{col}_days_since_ref")
        
        if self.drop_original:
            self._dropped_columns = self._datetime_columns.copy()
        
        # Store fitting stats
        self._fit_stats = {
            "datetime_columns": self._datetime_columns,
            "features_to_extract": self.extract,
            "new_columns_count": len(self._new_columns)
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract datetime features
        """
        self._validate_fitted()
        
        df_result = df.copy()
        
        for col in self._datetime_columns:
            if col not in df_result.columns:
                continue
            
            # Convert to datetime if needed
            dt_series = pd.to_datetime(df_result[col], errors='coerce')
            
            # Extract features
            for feature in self.extract:
                new_col = f"{col}_{feature}"
                
                if feature == 'year':
                    df_result[new_col] = dt_series.dt.year
                elif feature == 'month':
                    df_result[new_col] = dt_series.dt.month
                elif feature == 'day':
                    df_result[new_col] = dt_series.dt.day
                elif feature == 'dayofweek':
                    df_result[new_col] = dt_series.dt.dayofweek
                elif feature == 'dayofyear':
                    df_result[new_col] = dt_series.dt.dayofyear
                elif feature == 'hour':
                    df_result[new_col] = dt_series.dt.hour
                elif feature == 'minute':
                    df_result[new_col] = dt_series.dt.minute
                elif feature == 'second':
                    df_result[new_col] = dt_series.dt.second
                elif feature == 'quarter':
                    df_result[new_col] = dt_series.dt.quarter
                elif feature == 'week' or feature == 'weekofyear':
                    df_result[new_col] = dt_series.dt.isocalendar().week
                elif feature == 'is_weekend':
                    df_result[new_col] = dt_series.dt.dayofweek >= 5
                elif feature == 'is_month_start':
                    df_result[new_col] = dt_series.dt.is_month_start
                elif feature == 'is_month_end':
                    df_result[new_col] = dt_series.dt.is_month_end
                elif feature == 'is_quarter_start':
                    df_result[new_col] = dt_series.dt.is_quarter_start
                elif feature == 'is_quarter_end':
                    df_result[new_col] = dt_series.dt.is_quarter_end
                elif feature == 'is_year_start':
                    df_result[new_col] = dt_series.dt.is_year_start
                elif feature == 'is_year_end':
                    df_result[new_col] = dt_series.dt.is_year_end
            
            # Cyclical encoding
            if self.cyclical_encoding:
                if 'month' in self.extract:
                    df_result[f"{col}_month_sin"] = np.sin(2 * np.pi * dt_series.dt.month / 12)
                    df_result[f"{col}_month_cos"] = np.cos(2 * np.pi * dt_series.dt.month / 12)
                
                if 'dayofweek' in self.extract:
                    df_result[f"{col}_dayofweek_sin"] = np.sin(2 * np.pi * dt_series.dt.dayofweek / 7)
                    df_result[f"{col}_dayofweek_cos"] = np.cos(2 * np.pi * dt_series.dt.dayofweek / 7)
                
                if 'hour' in self.extract:
                    df_result[f"{col}_hour_sin"] = np.sin(2 * np.pi * dt_series.dt.hour / 24)
                    df_result[f"{col}_hour_cos"] = np.cos(2 * np.pi * dt_series.dt.hour / 24)
            
            # Days since reference date
            if self.reference_date:
                ref_date = pd.to_datetime(self.reference_date)
                df_result[f"{col}_days_since_ref"] = (dt_series - ref_date).dt.days
        
        # Drop original columns if requested
        if self.drop_original:
            df_result = df_result.drop(columns=self._datetime_columns, errors='ignore')
        
        return df_result
    
    def get_datetime_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate report of datetime columns
        """
        report = {
            "datetime_columns": [],
            "potential_datetime_columns": []
        }
        
        # Check explicit datetime columns
        for col in df.select_dtypes(include=['datetime64']).columns:
            series = df[col]
            report["datetime_columns"].append({
                "column": col,
                "min_date": str(series.min()),
                "max_date": str(series.max()),
                "null_count": int(series.isna().sum())
            })
        
        # Check object columns that might be datetime
        for col in df.select_dtypes(include=['object']).columns:
            try:
                sample = df[col].dropna().head(100)
                pd.to_datetime(sample, errors='raise')
                report["potential_datetime_columns"].append(col)
            except:
                pass
        
        return report
