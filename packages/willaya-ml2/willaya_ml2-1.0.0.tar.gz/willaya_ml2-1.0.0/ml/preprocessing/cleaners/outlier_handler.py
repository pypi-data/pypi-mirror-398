"""
Outlier Handler
Detects and handles outliers in numerical columns
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from .base import BaseCleaner


class OutlierHandler(BaseCleaner):
    """
    Handles outliers using various detection and treatment methods
    
    Detection Methods:
        - iqr: Interquartile Range method
        - zscore: Z-score method
        - isolation_forest: Isolation Forest algorithm
        - lof: Local Outlier Factor
    
    Actions:
        - remove: Remove rows with outliers
        - cap: Cap outliers to boundary values
        - flag: Add a flag column for outliers
        - none: Do nothing
    """
    
    VALID_METHODS = ['iqr', 'zscore', 'isolation_forest', 'lof', 'none']
    VALID_ACTIONS = ['remove', 'cap', 'flag', 'none']
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize OutlierHandler
        
        Config options:
            - method: Detection method (default: 'iqr')
            - action: How to handle outliers (default: 'cap')
            - threshold: Threshold for detection (default: 1.5 for IQR, 3.0 for zscore)
            - per_column: Dict[column_name, {method, action, threshold}]
            - contamination: For isolation_forest/lof (default: 0.1)
        """
        super().__init__(config)
        
        self.method = self.config.get('method', 'iqr')
        self.action = self.config.get('action', 'cap')
        self.threshold = self.config.get('threshold', 1.5 if self.method == 'iqr' else 3.0)
        self.per_column = self.config.get('per_column', {})
        self.contamination = self.config.get('contamination', 0.1)
        
        # Fitted values
        self._bounds: Dict[str, Tuple[float, float]] = {}
        self._numeric_columns: List[str] = []
        self._isolation_forests: Dict[str, IsolationForest] = {}
        self._lof_models: Dict[str, LocalOutlierFactor] = {}
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'OutlierHandler':
        """
        Fit the handler - calculate bounds for each numeric column
        """
        self._validate_input(df)
        
        # Identify numeric columns
        self._numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        self._affected_columns = []
        
        for column in self._numeric_columns:
            method = self._get_column_method(column)
            
            if method == 'none':
                continue
            
            series = df[column].dropna()
            
            if len(series) == 0:
                continue
            
            if method == 'iqr':
                bounds = self._calculate_iqr_bounds(series, column)
            elif method == 'zscore':
                bounds = self._calculate_zscore_bounds(series, column)
            elif method == 'isolation_forest':
                bounds = self._fit_isolation_forest(series, column)
            elif method == 'lof':
                bounds = self._fit_lof(series, column)
            else:
                continue
            
            if bounds:
                self._bounds[column] = bounds
                self._affected_columns.append(column)
        
        # Store fitting stats
        self._fit_stats = {
            "bounds": {k: {"lower": v[0], "upper": v[1]} for k, v in self._bounds.items()},
            "numeric_columns": self._numeric_columns,
            "method": self.method,
            "action": self.action
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply outlier handling
        """
        self._validate_fitted()
        
        df_result = df.copy()
        self._affected_rows = 0
        outlier_mask = pd.Series(False, index=df_result.index)
        
        for column in self._affected_columns:
            if column not in df_result.columns:
                continue
            
            action = self._get_column_action(column)
            method = self._get_column_method(column)
            
            if action == 'none' or method == 'none':
                continue
            
            # Detect outliers
            if method in ['isolation_forest', 'lof']:
                col_outliers = self._detect_model_outliers(df_result[column], column, method)
            else:
                col_outliers = self._detect_bound_outliers(df_result[column], column)
            
            outlier_mask |= col_outliers
            
            # Apply action
            if action == 'cap':
                lower, upper = self._bounds[column]
                df_result[column] = df_result[column].clip(lower=lower, upper=upper)
            elif action == 'flag':
                df_result[f'{column}_outlier_flag'] = col_outliers.astype(int)
            # 'remove' will be handled at the end
        
        # Handle remove action
        remove_columns = [col for col in self._affected_columns 
                        if self._get_column_action(col) == 'remove']
        if remove_columns:
            remove_mask = pd.Series(False, index=df_result.index)
            for column in remove_columns:
                method = self._get_column_method(column)
                if method in ['isolation_forest', 'lof']:
                    col_outliers = self._detect_model_outliers(df[column], column, method)
                else:
                    col_outliers = self._detect_bound_outliers(df[column], column)
                remove_mask |= col_outliers
            
            df_result = df_result[~remove_mask]
        
        self._affected_rows = int(outlier_mask.sum())
        
        return df_result
    
    def _calculate_iqr_bounds(self, series: pd.Series, column: str) -> Tuple[float, float]:
        """Calculate IQR-based bounds"""
        threshold = self._get_column_threshold(column)
        
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        
        return (float(lower), float(upper))
    
    def _calculate_zscore_bounds(self, series: pd.Series, column: str) -> Tuple[float, float]:
        """Calculate Z-score based bounds"""
        threshold = self._get_column_threshold(column)
        
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return (float(mean), float(mean))
        
        lower = mean - threshold * std
        upper = mean + threshold * std
        
        return (float(lower), float(upper))
    
    def _fit_isolation_forest(self, series: pd.Series, column: str) -> Tuple[float, float]:
        """Fit Isolation Forest and return approximate bounds"""
        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        
        data = series.values.reshape(-1, 1)
        model.fit(data)
        self._isolation_forests[column] = model
        
        # Get approximate bounds based on non-outliers
        predictions = model.predict(data)
        non_outliers = series[predictions == 1]
        
        if len(non_outliers) > 0:
            return (float(non_outliers.min()), float(non_outliers.max()))
        return (float(series.min()), float(series.max()))
    
    def _fit_lof(self, series: pd.Series, column: str) -> Tuple[float, float]:
        """Fit Local Outlier Factor and return approximate bounds"""
        model = LocalOutlierFactor(
            n_neighbors=min(20, len(series) - 1),
            contamination=self.contamination,
            novelty=True
        )
        
        data = series.values.reshape(-1, 1)
        model.fit(data)
        self._lof_models[column] = model
        
        # Get approximate bounds
        predictions = model.predict(data)
        non_outliers = series[predictions == 1]
        
        if len(non_outliers) > 0:
            return (float(non_outliers.min()), float(non_outliers.max()))
        return (float(series.min()), float(series.max()))
    
    def _detect_bound_outliers(self, series: pd.Series, column: str) -> pd.Series:
        """Detect outliers using fitted bounds"""
        lower, upper = self._bounds[column]
        return (series < lower) | (series > upper)
    
    def _detect_model_outliers(self, series: pd.Series, column: str, method: str) -> pd.Series:
        """Detect outliers using fitted model"""
        data = series.fillna(series.median()).values.reshape(-1, 1)
        
        if method == 'isolation_forest' and column in self._isolation_forests:
            predictions = self._isolation_forests[column].predict(data)
        elif method == 'lof' and column in self._lof_models:
            predictions = self._lof_models[column].predict(data)
        else:
            return pd.Series(False, index=series.index)
        
        return pd.Series(predictions == -1, index=series.index)
    
    def _get_column_method(self, column: str) -> str:
        """Get the method for a specific column"""
        if column in self.per_column:
            return self.per_column[column].get('method', self.method)
        return self.method
    
    def _get_column_action(self, column: str) -> str:
        """Get the action for a specific column"""
        if column in self.per_column:
            return self.per_column[column].get('action', self.action)
        return self.action
    
    def _get_column_threshold(self, column: str) -> float:
        """Get the threshold for a specific column"""
        if column in self.per_column:
            return self.per_column[column].get('threshold', self.threshold)
        return self.threshold
    
    def get_outlier_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a report of outliers in DataFrame
        """
        self._validate_fitted()
        
        report = {
            "total_outliers": 0,
            "columns": {}
        }
        
        for column in self._affected_columns:
            if column not in df.columns:
                continue
            
            method = self._get_column_method(column)
            
            if method in ['isolation_forest', 'lof']:
                outliers = self._detect_model_outliers(df[column], column, method)
            else:
                outliers = self._detect_bound_outliers(df[column], column)
            
            outlier_count = int(outliers.sum())
            
            if outlier_count > 0:
                bounds = self._bounds.get(column, (None, None))
                report["columns"][column] = {
                    "outlier_count": outlier_count,
                    "outlier_percent": round(outlier_count / len(df) * 100, 2),
                    "lower_bound": bounds[0],
                    "upper_bound": bounds[1],
                    "method": method,
                    "action": self._get_column_action(column)
                }
                report["total_outliers"] += outlier_count
        
        return report
