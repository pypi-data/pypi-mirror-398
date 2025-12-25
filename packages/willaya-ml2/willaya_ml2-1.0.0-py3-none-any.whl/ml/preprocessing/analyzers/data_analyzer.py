"""
Data Analyzer
Main entry point for data analysis and auto-detection
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from .stats_calculator import StatsCalculator
from .recommendation import RecommendationEngine


class DataAnalyzer:
    """
    Analyzes data and generates preprocessing recommendations
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with a DataFrame
        
        Args:
            df: Input DataFrame to analyze
        """
        self.df = df
        self.stats_calculator = StatsCalculator(df)
        self.recommendation_engine = RecommendationEngine(self.stats_calculator)
        
        self._analysis_result: Optional[Dict[str, Any]] = None
    
    def analyze(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform comprehensive data analysis
        
        Args:
            sample_size: If provided, analyze only a sample of data
        
        Returns:
            Complete analysis results with recommendations
        """
        df_to_analyze = self.df
        if sample_size and len(self.df) > sample_size:
            df_to_analyze = self.df.sample(n=sample_size, random_state=42)
            self.stats_calculator = StatsCalculator(df_to_analyze)
            self.recommendation_engine = RecommendationEngine(self.stats_calculator)
        
        # Get summary statistics
        summary = self.stats_calculator.get_dataframe_summary()
        
        # Analyze each column
        column_stats = {}
        for column in df_to_analyze.columns:
            column_stats[column] = self.stats_calculator.get_full_column_stats(column)
        
        # Generate recommendations
        recommendations = self.recommendation_engine.get_all_recommendations(column_stats)
        
        # Generate auto config
        auto_config = self.recommendation_engine.generate_auto_config(recommendations)
        
        # Collect warnings and info
        warnings = self._generate_warnings(summary, column_stats)
        info = self._generate_info(summary, column_stats)
        
        self._analysis_result = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "rows_analyzed": len(df_to_analyze),
            "columns_analyzed": len(df_to_analyze.columns),
            "summary": summary,
            "columns": column_stats,
            "recommendations": recommendations,
            "auto_config_generated": auto_config,
            "warnings": warnings,
            "info": info
        }
        
        return self._analysis_result
    
    def _generate_warnings(
        self, 
        summary: Dict[str, Any], 
        column_stats: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate warning messages based on analysis"""
        warnings = []
        
        # High missing rate warning
        for column, stats in column_stats.items():
            missing_pct = stats.get("missing_percent", 0)
            if missing_pct > 50:
                warnings.append(
                    f"Column '{column}' has {missing_pct}% missing values - consider dropping"
                )
            elif missing_pct > 20:
                warnings.append(
                    f"Column '{column}' has significant missing values ({missing_pct}%)"
                )
        
        # Duplicate rows warning
        dup_count = summary.get("duplicate_rows", 0)
        if dup_count > 0:
            dup_pct = round(dup_count / summary.get("total_rows", 1) * 100, 2)
            warnings.append(
                f"Found {dup_count} duplicate rows ({dup_pct}%)"
            )
        
        # High cardinality warning
        for column, stats in column_stats.items():
            if stats.get("cardinality") == "very_high":
                warnings.append(
                    f"Column '{column}' has very high cardinality ({stats.get('unique_count')} unique values)"
                )
        
        # High outlier percentage warning
        for column, stats in column_stats.items():
            outlier_pct = stats.get("outliers_percent", 0)
            if outlier_pct and outlier_pct > 10:
                warnings.append(
                    f"Column '{column}' has high outlier rate ({outlier_pct}%)"
                )
        
        # Low variance warning
        low_var_cols = self.stats_calculator.find_low_variance_columns()
        if low_var_cols:
            warnings.append(
                f"Columns with near-zero variance: {low_var_cols}"
            )
        
        # High correlation warning
        high_corr = self.stats_calculator.find_high_correlations()
        if high_corr:
            warnings.append(
                f"Found {len(high_corr)} highly correlated column pairs"
            )
        
        return warnings
    
    def _generate_info(
        self, 
        summary: Dict[str, Any], 
        column_stats: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate informational messages based on analysis"""
        info = []
        
        # Dataset size info
        rows = summary.get("total_rows", 0)
        cols = summary.get("total_columns", 0)
        info.append(f"Dataset has {rows:,} rows and {cols} columns")
        
        # Column types info
        numeric = summary.get("numeric_columns", 0)
        categorical = summary.get("categorical_columns", 0)
        datetime_cols = summary.get("datetime_columns", 0)
        boolean = summary.get("boolean_columns", 0)
        
        info.append(
            f"Column types: {numeric} numeric, {categorical} categorical, "
            f"{datetime_cols} datetime, {boolean} boolean"
        )
        
        # Memory usage
        memory = summary.get("memory_usage_mb", 0)
        info.append(f"Memory usage: {memory:.2f} MB")
        
        # Datetime columns detected
        if self.stats_calculator.datetime_columns:
            info.append(
                f"Datetime columns detected: {self.stats_calculator.datetime_columns}"
            )
        
        return info
    
    def get_column_analysis(self, column: str) -> Dict[str, Any]:
        """
        Get detailed analysis for a specific column
        
        Args:
            column: Column name
        
        Returns:
            Column analysis with stats and recommendations
        """
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        stats = self.stats_calculator.get_full_column_stats(column)
        
        recommendations = {
            "missing": self.recommendation_engine.recommend_missing_strategy(column, stats),
        }
        
        if stats.get("dtype") == "numeric":
            recommendations["outliers"] = \
                self.recommendation_engine.recommend_outlier_strategy(column, stats)
            recommendations["scaling"] = \
                self.recommendation_engine.recommend_scaling_strategy(column, stats)
        
        if stats.get("dtype") == "categorical":
            recommendations["encoding"] = \
                self.recommendation_engine.recommend_encoding_strategy(column, stats)
        
        return {
            "column": column,
            "stats": stats,
            "recommendations": recommendations
        }
    
    def detect_column_types(self) -> Dict[str, List[str]]:
        """
        Detect and categorize column types
        
        Returns:
            Dict mapping type categories to column lists
        """
        return {
            "numeric": self.stats_calculator.numeric_columns,
            "categorical": self.stats_calculator.categorical_columns,
            "datetime": self.stats_calculator.datetime_columns,
            "boolean": self.stats_calculator.boolean_columns
        }
    
    def detect_id_columns(self) -> List[str]:
        """
        Detect potential ID columns (unique identifiers)
        
        Returns:
            List of potential ID column names
        """
        id_columns = []
        
        for column in self.df.columns:
            # Check if column name suggests it's an ID
            col_lower = column.lower()
            if any(id_hint in col_lower for id_hint in ['id', 'key', 'code', 'uuid']):
                id_columns.append(column)
                continue
            
            # Check if all values are unique
            if self.df[column].nunique() == len(self.df):
                id_columns.append(column)
        
        return id_columns
    
    def detect_target_column(self, hints: Optional[List[str]] = None) -> Optional[str]:
        """
        Try to detect the target column
        
        Args:
            hints: List of possible target column names
        
        Returns:
            Detected target column name or None
        """
        if hints:
            for hint in hints:
                if hint in self.df.columns:
                    return hint
        
        # Common target column names
        common_names = [
            'target', 'label', 'class', 'y', 'outcome', 
            'result', 'approved', 'eligible', 'status',
            'amount', 'value', 'price'
        ]
        
        for name in common_names:
            for column in self.df.columns:
                if name in column.lower():
                    return column
        
        return None
    
    def suggest_derived_features(self) -> List[Dict[str, str]]:
        """
        Suggest potential derived features based on column names
        
        Returns:
            List of suggested derived features
        """
        suggestions = []
        numeric_cols = self.stats_calculator.numeric_columns
        
        # Look for ratio opportunities
        for col1 in numeric_cols:
            for col2 in numeric_cols:
                if col1 != col2:
                    col1_lower = col1.lower()
                    col2_lower = col2.lower()
                    
                    # Income to expense ratios
                    if 'income' in col1_lower and any(x in col2_lower for x in ['expense', 'rent', 'payment', 'cost']):
                        suggestions.append({
                            "name": f"{col1}_to_{col2}_ratio",
                            "formula": f"{col1} / {col2}",
                            "description": f"Ratio of {col1} to {col2}"
                        })
                    
                    # Percentage calculations
                    if 'total' in col1_lower and col2_lower.replace('total', '').strip():
                        suggestions.append({
                            "name": f"{col2}_percent_of_{col1}",
                            "formula": f"({col2} / {col1}) * 100",
                            "description": f"Percentage of {col2} relative to {col1}"
                        })
        
        # Look for age from date
        datetime_cols = self.stats_calculator.datetime_columns
        for col in datetime_cols:
            if any(x in col.lower() for x in ['birth', 'dob', 'start', 'created']):
                suggestions.append({
                    "name": f"days_since_{col}",
                    "formula": f"(current_date - {col}).days",
                    "description": f"Days elapsed since {col}"
                })
        
        return suggestions
    
    @property
    def analysis_result(self) -> Optional[Dict[str, Any]]:
        """Get the last analysis result"""
        return self._analysis_result
