"""
Statistics Calculator
Calculates various statistics for data analysis
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


class StatsCalculator:
    """
    Calculates comprehensive statistics for DataFrames and columns
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        self._categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self._datetime_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
        self._boolean_columns = df.select_dtypes(include=['bool']).columns.tolist()
    
    @property
    def numeric_columns(self) -> List[str]:
        return self._numeric_columns
    
    @property
    def categorical_columns(self) -> List[str]:
        return self._categorical_columns
    
    @property
    def datetime_columns(self) -> List[str]:
        return self._datetime_columns
    
    @property
    def boolean_columns(self) -> List[str]:
        return self._boolean_columns
    
    def get_column_dtype(self, column: str) -> str:
        """Get the dtype category of a column"""
        if column in self._numeric_columns:
            return "numeric"
        elif column in self._categorical_columns:
            return "categorical"
        elif column in self._datetime_columns:
            return "datetime"
        elif column in self._boolean_columns:
            return "boolean"
        else:
            return "unknown"
    
    def calculate_missing_stats(self, column: str) -> Dict[str, Any]:
        """Calculate missing value statistics for a column"""
        total = len(self.df)
        missing_count = self.df[column].isna().sum()
        
        return {
            "missing_count": int(missing_count),
            "missing_percent": round(missing_count / total * 100, 2) if total > 0 else 0,
            "non_missing_count": int(total - missing_count)
        }
    
    def calculate_numeric_stats(self, column: str) -> Dict[str, Any]:
        """Calculate statistics for a numeric column"""
        series = self.df[column].dropna()
        
        if len(series) == 0:
            return {}
        
        # Basic stats
        stats = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "q1": float(series.quantile(0.25)),
            "q3": float(series.quantile(0.75)),
        }
        
        # Add skewness and kurtosis
        try:
            stats["skewness"] = float(scipy_stats.skew(series))
            stats["kurtosis"] = float(scipy_stats.kurtosis(series))
        except:
            stats["skewness"] = None
            stats["kurtosis"] = None
        
        # Calculate outliers using IQR
        outlier_stats = self.calculate_outliers_iqr(series)
        stats.update(outlier_stats)
        
        return stats
    
    def calculate_outliers_iqr(
        self, 
        series: pd.Series, 
        threshold: float = 1.5
    ) -> Dict[str, Any]:
        """Calculate outlier statistics using IQR method"""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        
        return {
            "outliers_count": int(len(outliers)),
            "outliers_percent": round(len(outliers) / len(series) * 100, 2) if len(series) > 0 else 0,
            "outliers_lower_bound": float(lower_bound),
            "outliers_upper_bound": float(upper_bound)
        }
    
    def calculate_outliers_zscore(
        self, 
        series: pd.Series, 
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """Calculate outlier statistics using Z-score method"""
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return {
                "outliers_count": 0,
                "outliers_percent": 0.0
            }
        
        z_scores = np.abs((series - mean) / std)
        outliers = series[z_scores > threshold]
        
        return {
            "outliers_count": int(len(outliers)),
            "outliers_percent": round(len(outliers) / len(series) * 100, 2) if len(series) > 0 else 0
        }
    
    def calculate_categorical_stats(self, column: str) -> Dict[str, Any]:
        """Calculate statistics for a categorical column"""
        series = self.df[column].dropna()
        
        if len(series) == 0:
            return {}
        
        value_counts = series.value_counts()
        unique_count = len(value_counts)
        
        # Determine cardinality level
        if unique_count <= 5:
            cardinality = "low"
        elif unique_count <= 20:
            cardinality = "medium"
        elif unique_count <= 100:
            cardinality = "high"
        else:
            cardinality = "very_high"
        
        # Get top values
        top_n = min(10, unique_count)
        top_values = [
            {"value": str(val), "count": int(cnt), "percent": round(cnt / len(series) * 100, 2)}
            for val, cnt in value_counts.head(top_n).items()
        ]
        
        return {
            "unique_count": unique_count,
            "cardinality": cardinality,
            "top_values": top_values,
            "mode": str(value_counts.index[0]) if len(value_counts) > 0 else None,
            "mode_frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0
        }
    
    def calculate_datetime_stats(self, column: str) -> Dict[str, Any]:
        """Calculate statistics for a datetime column"""
        series = pd.to_datetime(self.df[column], errors='coerce').dropna()
        
        if len(series) == 0:
            return {}
        
        return {
            "min_date": str(series.min()),
            "max_date": str(series.max()),
            "date_range_days": (series.max() - series.min()).days,
            "has_time_component": any(series.dt.time != pd.Timestamp('00:00:00').time())
        }
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """Calculate correlation matrix for numeric columns"""
        if len(self._numeric_columns) < 2:
            return pd.DataFrame()
        
        return self.df[self._numeric_columns].corr()
    
    def find_high_correlations(self, threshold: float = 0.9) -> List[Dict[str, Any]]:
        """Find pairs of highly correlated columns"""
        corr_matrix = self.calculate_correlation_matrix()
        
        if corr_matrix.empty:
            return []
        
        high_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    high_corr.append({
                        "column1": corr_matrix.columns[i],
                        "column2": corr_matrix.columns[j],
                        "correlation": round(corr_value, 4)
                    })
        
        return high_corr
    
    def calculate_variance(self) -> Dict[str, float]:
        """Calculate variance for all numeric columns"""
        variances = {}
        for col in self._numeric_columns:
            variances[col] = float(self.df[col].var())
        return variances
    
    def find_low_variance_columns(self, threshold: float = 0.01) -> List[str]:
        """Find columns with low variance"""
        variances = self.calculate_variance()
        return [col for col, var in variances.items() if var < threshold]
    
    def get_full_column_stats(self, column: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a column"""
        dtype = self.get_column_dtype(column)
        
        stats = {
            "column_name": column,
            "dtype": dtype,
            "pandas_dtype": str(self.df[column].dtype)
        }
        
        # Add missing stats
        stats.update(self.calculate_missing_stats(column))
        
        # Add unique count
        stats["unique_count"] = int(self.df[column].nunique())
        
        # Add type-specific stats
        if dtype == "numeric":
            stats.update(self.calculate_numeric_stats(column))
        elif dtype == "categorical":
            stats.update(self.calculate_categorical_stats(column))
        elif dtype == "datetime":
            stats.update(self.calculate_datetime_stats(column))
        elif dtype == "boolean":
            value_counts = self.df[column].value_counts()
            stats["true_count"] = int(value_counts.get(True, 0))
            stats["false_count"] = int(value_counts.get(False, 0))
        
        return stats
    
    def get_dataframe_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the entire DataFrame"""
        return {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "numeric_columns": len(self._numeric_columns),
            "categorical_columns": len(self._categorical_columns),
            "datetime_columns": len(self._datetime_columns),
            "boolean_columns": len(self._boolean_columns),
            "total_missing_values": int(self.df.isna().sum().sum()),
            "total_missing_percent": round(
                self.df.isna().sum().sum() / (len(self.df) * len(self.df.columns)) * 100, 2
            ) if len(self.df) > 0 and len(self.df.columns) > 0 else 0,
            "duplicate_rows": int(self.df.duplicated().sum()),
            "memory_usage_mb": round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
