"""
Recommendation Engine
Suggests optimal preprocessing strategies based on data analysis
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from .stats_calculator import StatsCalculator


class RecommendationEngine:
    """
    Generates preprocessing recommendations based on data characteristics
    """
    
    def __init__(self, stats_calculator: StatsCalculator):
        self.stats = stats_calculator
    
    def recommend_missing_strategy(
        self, 
        column: str, 
        column_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend strategy for handling missing values
        
        Returns:
            Dict with strategy, reason, and confidence
        """
        dtype = column_stats.get("dtype", "unknown")
        missing_percent = column_stats.get("missing_percent", 0)
        
        # If too many missing, suggest drop or constant
        if missing_percent > 50:
            return {
                "strategy": "drop",
                "reason": f"High missing rate ({missing_percent}%) - consider dropping column or using constant",
                "confidence": 0.7,
                "alternative": "constant"
            }
        
        if dtype == "numeric":
            # Check for skewness
            skewness = column_stats.get("skewness")
            outliers_percent = column_stats.get("outliers_percent", 0)
            
            if skewness is not None and abs(skewness) > 1:
                # Skewed distribution - use median
                return {
                    "strategy": "median",
                    "reason": f"Skewed distribution (skewness={skewness:.2f}) - median is more robust",
                    "confidence": 0.9
                }
            elif outliers_percent and outliers_percent > 5:
                # Has outliers - use median
                return {
                    "strategy": "median",
                    "reason": f"Contains outliers ({outliers_percent}%) - median is more robust",
                    "confidence": 0.85
                }
            else:
                # Normal distribution - mean is fine
                return {
                    "strategy": "mean",
                    "reason": "Approximately normal distribution - mean imputation appropriate",
                    "confidence": 0.8
                }
        
        elif dtype == "categorical":
            cardinality = column_stats.get("cardinality", "medium")
            
            if cardinality in ["low", "medium"]:
                return {
                    "strategy": "mode",
                    "reason": "Categorical with manageable cardinality - use most frequent value",
                    "confidence": 0.85
                }
            else:
                return {
                    "strategy": "constant",
                    "reason": "High cardinality categorical - use constant 'MISSING' category",
                    "confidence": 0.75,
                    "fill_value": "MISSING"
                }
        
        elif dtype == "boolean":
            return {
                "strategy": "mode",
                "reason": "Boolean column - use most frequent value",
                "confidence": 0.9
            }
        
        elif dtype == "datetime":
            return {
                "strategy": "drop",
                "reason": "Datetime column - dropping missing dates is usually safest",
                "confidence": 0.7,
                "alternative": "ffill"
            }
        
        else:
            return {
                "strategy": "drop",
                "reason": "Unknown column type - dropping rows with missing values",
                "confidence": 0.5
            }
    
    def recommend_outlier_strategy(
        self, 
        column: str, 
        column_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend strategy for handling outliers
        """
        dtype = column_stats.get("dtype", "unknown")
        
        if dtype != "numeric":
            return {
                "method": "none",
                "action": "none",
                "reason": "Non-numeric column - outlier detection not applicable",
                "confidence": 1.0
            }
        
        outliers_percent = column_stats.get("outliers_percent", 0)
        skewness = column_stats.get("skewness")
        
        if outliers_percent == 0:
            return {
                "method": "none",
                "action": "none",
                "reason": "No outliers detected",
                "confidence": 1.0
            }
        
        # Determine detection method
        if skewness is not None and abs(skewness) > 2:
            method = "iqr"
            method_reason = "Highly skewed data - IQR method preferred"
        else:
            method = "zscore"
            method_reason = "Approximately symmetric data - Z-score method appropriate"
        
        # Determine action
        if outliers_percent < 1:
            action = "remove"
            action_reason = "Very few outliers - safe to remove"
        elif outliers_percent < 5:
            action = "cap"
            action_reason = "Moderate outliers - capping preserves data"
        else:
            action = "flag"
            action_reason = "Many outliers - flag as feature instead of removing"
        
        return {
            "method": method,
            "action": action,
            "reason": f"{method_reason}. {action_reason}",
            "confidence": 0.8,
            "threshold": 1.5 if method == "iqr" else 3.0
        }
    
    def recommend_encoding_strategy(
        self, 
        column: str, 
        column_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend strategy for categorical encoding
        """
        dtype = column_stats.get("dtype", "unknown")
        
        if dtype != "categorical":
            return {
                "strategy": "none",
                "reason": "Non-categorical column",
                "confidence": 1.0
            }
        
        cardinality = column_stats.get("cardinality", "medium")
        unique_count = column_stats.get("unique_count", 0)
        
        if cardinality == "low":
            return {
                "strategy": "onehot",
                "reason": f"Low cardinality ({unique_count} unique) - one-hot encoding efficient",
                "confidence": 0.95
            }
        
        elif cardinality == "medium":
            if unique_count <= 10:
                return {
                    "strategy": "onehot",
                    "reason": f"Medium cardinality ({unique_count} unique) - one-hot still manageable",
                    "confidence": 0.85
                }
            else:
                return {
                    "strategy": "target",
                    "reason": f"Medium-high cardinality ({unique_count} unique) - target encoding recommended",
                    "confidence": 0.8,
                    "alternative": "frequency"
                }
        
        elif cardinality == "high":
            return {
                "strategy": "target",
                "reason": f"High cardinality ({unique_count} unique) - target encoding prevents explosion",
                "confidence": 0.85,
                "alternative": "frequency"
            }
        
        else:  # very_high
            return {
                "strategy": "frequency",
                "reason": f"Very high cardinality ({unique_count} unique) - frequency encoding most robust",
                "confidence": 0.75,
                "alternative": "target",
                "warning": "Consider feature engineering or grouping rare categories"
            }
    
    def recommend_scaling_strategy(
        self, 
        column: str, 
        column_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend strategy for numerical scaling
        """
        dtype = column_stats.get("dtype", "unknown")
        
        if dtype != "numeric":
            return {
                "strategy": "none",
                "reason": "Non-numeric column",
                "confidence": 1.0
            }
        
        outliers_percent = column_stats.get("outliers_percent", 0)
        skewness = column_stats.get("skewness")
        min_val = column_stats.get("min", 0)
        max_val = column_stats.get("max", 1)
        
        # Check if already normalized
        if min_val >= 0 and max_val <= 1:
            return {
                "strategy": "none",
                "reason": "Values already in [0,1] range - no scaling needed",
                "confidence": 0.9
            }
        
        # Check for outliers
        if outliers_percent and outliers_percent > 5:
            return {
                "strategy": "robust",
                "reason": f"Contains significant outliers ({outliers_percent}%) - robust scaler recommended",
                "confidence": 0.9
            }
        
        # Check for skewness
        if skewness is not None and abs(skewness) > 2:
            return {
                "strategy": "robust",
                "reason": f"Highly skewed (skewness={skewness:.2f}) - robust scaler handles asymmetry",
                "confidence": 0.85
            }
        
        # Default to standard scaling
        return {
            "strategy": "standard",
            "reason": "Standard scaling (z-score normalization) - suitable for most ML algorithms",
            "confidence": 0.85
        }
    
    def recommend_feature_selection(
        self, 
        df_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend feature selection strategies
        """
        recommendations = {
            "enabled": True,
            "methods": [],
            "warnings": []
        }
        
        # Low variance check
        low_variance_cols = self.stats.find_low_variance_columns(threshold=0.01)
        if low_variance_cols:
            recommendations["methods"].append({
                "type": "variance",
                "threshold": 0.01,
                "reason": f"Found {len(low_variance_cols)} low-variance columns",
                "columns_affected": low_variance_cols
            })
        
        # High correlation check
        high_corr_pairs = self.stats.find_high_correlations(threshold=0.95)
        if high_corr_pairs:
            recommendations["methods"].append({
                "type": "correlation",
                "threshold": 0.95,
                "reason": f"Found {len(high_corr_pairs)} highly correlated column pairs",
                "pairs": high_corr_pairs
            })
            recommendations["warnings"].append(
                f"Consider removing one of each correlated pair: {high_corr_pairs}"
            )
        
        return recommendations
    
    def get_all_recommendations(
        self, 
        all_column_stats: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations for all columns
        """
        recommendations = {
            "missing_values": {},
            "outliers": {},
            "categorical_encoding": {},
            "numerical_scaling": {},
            "feature_selection": {}
        }
        
        for column, stats in all_column_stats.items():
            # Missing values
            if stats.get("missing_percent", 0) > 0:
                recommendations["missing_values"][column] = \
                    self.recommend_missing_strategy(column, stats)
            
            # Outliers (numeric only)
            if stats.get("dtype") == "numeric":
                recommendations["outliers"][column] = \
                    self.recommend_outlier_strategy(column, stats)
            
            # Encoding (categorical only)
            if stats.get("dtype") == "categorical":
                recommendations["categorical_encoding"][column] = \
                    self.recommend_encoding_strategy(column, stats)
            
            # Scaling (numeric only)
            if stats.get("dtype") == "numeric":
                recommendations["numerical_scaling"][column] = \
                    self.recommend_scaling_strategy(column, stats)
        
        # Feature selection
        df_stats = self.stats.get_dataframe_summary()
        recommendations["feature_selection"] = \
            self.recommend_feature_selection(df_stats)
        
        return recommendations
    
    def generate_auto_config(
        self, 
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate preprocessing config from recommendations
        """
        config = {
            "cleaning": {
                "missing_values": {
                    "mode": "auto",
                    "manual_config": {
                        "per_column": {}
                    }
                },
                "outliers": {
                    "mode": "auto",
                    "manual_config": {
                        "per_column": {}
                    }
                },
                "duplicates": {
                    "mode": "auto",
                    "manual_config": {
                        "action": "drop"
                    }
                },
                "type_conversion": {
                    "mode": "auto"
                }
            },
            "feature_engineering": {
                "derived_features": {
                    "mode": "manual",
                    "manual_config": {
                        "features": []
                    }
                },
                "date_features": {
                    "mode": "auto"
                },
                "binning": {
                    "mode": "manual",
                    "manual_config": {
                        "bins": []
                    }
                }
            },
            "processing": {
                "categorical_encoding": {
                    "mode": "auto",
                    "manual_config": {
                        "per_column": {}
                    }
                },
                "numerical_scaling": {
                    "mode": "auto",
                    "manual_config": {
                        "per_column": {}
                    }
                },
                "feature_selection": {
                    "mode": "auto",
                    "manual_config": {
                        "enabled": True,
                        "methods": []
                    }
                }
            },
            "settings": {
                "random_state": 42,
                "n_jobs": -1,
                "verbose": True
            }
        }
        
        # Populate per-column configs from recommendations
        for column, rec in recommendations.get("missing_values", {}).items():
            config["cleaning"]["missing_values"]["manual_config"]["per_column"][column] = {
                "strategy": rec["strategy"]
            }
            if "fill_value" in rec:
                config["cleaning"]["missing_values"]["manual_config"]["per_column"][column]["fill_value"] = rec["fill_value"]
        
        for column, rec in recommendations.get("outliers", {}).items():
            if rec.get("method") != "none":
                config["cleaning"]["outliers"]["manual_config"]["per_column"][column] = {
                    "method": rec["method"],
                    "action": rec["action"],
                    "threshold": rec.get("threshold", 1.5)
                }
        
        for column, rec in recommendations.get("categorical_encoding", {}).items():
            if rec.get("strategy") != "none":
                config["processing"]["categorical_encoding"]["manual_config"]["per_column"][column] = {
                    "strategy": rec["strategy"]
                }
        
        for column, rec in recommendations.get("numerical_scaling", {}).items():
            if rec.get("strategy") != "none":
                config["processing"]["numerical_scaling"]["manual_config"]["per_column"][column] = {
                    "strategy": rec["strategy"]
                }
        
        # Feature selection methods
        fs_rec = recommendations.get("feature_selection", {})
        if fs_rec.get("methods"):
            config["processing"]["feature_selection"]["manual_config"]["methods"] = [
                {"type": m["type"], "threshold": m["threshold"]}
                for m in fs_rec.get("methods", [])
            ]
        
        return config
