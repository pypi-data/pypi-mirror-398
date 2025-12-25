"""
Feature Selector
Handles feature selection using various methods
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from sklearn.feature_selection import (
    VarianceThreshold, 
    SelectKBest, 
    mutual_info_classif,
    mutual_info_regression,
    f_classif,
    f_regression,
    RFE
)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from .base import BaseProcessor


class FeatureSelector(BaseProcessor):
    """
    Selects features using various methods
    
    Methods:
        - variance: Remove low-variance features
        - correlation: Remove highly correlated features
        - importance: Select by feature importance (tree-based)
        - mutual_info: Select by mutual information
        - rfe: Recursive Feature Elimination
    """
    
    VALID_METHODS = ['variance', 'correlation', 'importance', 'mutual_info', 'rfe']
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize FeatureSelector
        
        Config options:
            - enabled: Whether feature selection is enabled
            - methods: List of selection methods to apply
                - type: Method type
                - threshold: Threshold value (method-specific)
                - top_k: Number of top features to keep
            - task_type: 'classification' or 'regression'
            - exclude_columns: Columns to never remove
        """
        super().__init__(config)
        
        self.enabled = self.config.get('enabled', True)
        self.methods = self.config.get('methods', [])
        self.task_type = self.config.get('task_type', 'classification')
        self.exclude_columns = self.config.get('exclude_columns', [])
        
        # Fitted values
        self._selected_features: List[str] = []
        self._removed_features: List[str] = []
        self._feature_scores: Dict[str, float] = {}
        self._correlation_matrix: Optional[pd.DataFrame] = None
        self._variance_scores: Dict[str, float] = {}
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'FeatureSelector':
        """
        Fit feature selector - identify features to keep/remove
        """
        self._validate_input(df)
        
        if not self.enabled:
            self._selected_features = df.columns.tolist()
            self._removed_features = []
            self._is_fitted = True
            return self
        
        self._feature_names_in = df.columns.tolist()
        features_to_remove = set()
        
        # Get numeric columns for selection
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c not in self.exclude_columns]
        
        for method_config in self.methods:
            method_type = method_config.get('type')
            
            if method_type == 'variance':
                removed = self._fit_variance(df, numeric_cols, method_config)
                features_to_remove.update(removed)
                
            elif method_type == 'correlation':
                removed = self._fit_correlation(df, numeric_cols, method_config)
                features_to_remove.update(removed)
                
            elif method_type == 'importance':
                if y is not None:
                    removed = self._fit_importance(df, y, numeric_cols, method_config)
                    features_to_remove.update(removed)
                    
            elif method_type == 'mutual_info':
                if y is not None:
                    removed = self._fit_mutual_info(df, y, numeric_cols, method_config)
                    features_to_remove.update(removed)
                    
            elif method_type == 'rfe':
                if y is not None:
                    removed = self._fit_rfe(df, y, numeric_cols, method_config)
                    features_to_remove.update(removed)
        
        # Determine final selected features
        self._removed_features = list(features_to_remove)
        self._selected_features = [
            col for col in df.columns 
            if col not in features_to_remove
        ]
        self._feature_names_out = self._selected_features.copy()
        
        # Store fitting stats
        self._fit_stats = {
            "features_in": len(self._feature_names_in),
            "features_out": len(self._selected_features),
            "features_removed": len(self._removed_features),
            "removed_features": self._removed_features,
            "feature_scores": self._feature_scores,
            "variance_scores": self._variance_scores
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply feature selection - keep only selected features
        """
        self._validate_fitted()
        
        if not self.enabled:
            return df.copy()
        
        # Keep only selected features (that exist in df)
        cols_to_keep = [col for col in self._selected_features if col in df.columns]
        
        return df[cols_to_keep].copy()
    
    def _fit_variance(
        self, 
        df: pd.DataFrame, 
        columns: List[str],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Identify low-variance features to remove
        """
        threshold = config.get('threshold', 0.01)
        
        removed = []
        for col in columns:
            variance = df[col].var()
            self._variance_scores[col] = float(variance)
            
            if variance < threshold:
                removed.append(col)
        
        return removed
    
    def _fit_correlation(
        self, 
        df: pd.DataFrame, 
        columns: List[str],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Identify highly correlated features to remove
        """
        threshold = config.get('threshold', 0.95)
        
        # Calculate correlation matrix
        corr_df = df[columns].corr().abs()
        self._correlation_matrix = corr_df
        
        # Find pairs above threshold
        removed = set()
        for i in range(len(corr_df.columns)):
            for j in range(i + 1, len(corr_df.columns)):
                if corr_df.iloc[i, j] > threshold:
                    # Remove the one with lower variance
                    col1, col2 = corr_df.columns[i], corr_df.columns[j]
                    var1 = df[col1].var()
                    var2 = df[col2].var()
                    
                    if var1 < var2:
                        removed.add(col1)
                    else:
                        removed.add(col2)
        
        return list(removed)
    
    def _fit_importance(
        self, 
        df: pd.DataFrame, 
        y: pd.Series,
        columns: List[str],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Identify low-importance features to remove
        """
        threshold = config.get('threshold')
        top_k = config.get('top_k')
        
        # Use Random Forest for importance
        if self.task_type == 'classification':
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        
        # Prepare data
        X = df[columns].fillna(df[columns].median())
        
        model.fit(X, y)
        
        # Get importances
        importances = dict(zip(columns, model.feature_importances_))
        self._feature_scores.update(importances)
        
        # Sort by importance
        sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        
        removed = []
        if top_k:
            # Keep top k
            keep_features = [f[0] for f in sorted_features[:top_k]]
            removed = [f[0] for f in sorted_features[top_k:]]
        elif threshold:
            # Remove below threshold
            removed = [f[0] for f in sorted_features if f[1] < threshold]
        
        return removed
    
    def _fit_mutual_info(
        self, 
        df: pd.DataFrame, 
        y: pd.Series,
        columns: List[str],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Identify low mutual information features to remove
        """
        threshold = config.get('threshold')
        top_k = config.get('top_k')
        
        # Prepare data
        X = df[columns].fillna(df[columns].median())
        
        # Calculate mutual information
        if self.task_type == 'classification':
            mi_scores = mutual_info_classif(X, y, random_state=42)
        else:
            mi_scores = mutual_info_regression(X, y, random_state=42)
        
        # Store scores
        mi_dict = dict(zip(columns, mi_scores))
        for col, score in mi_dict.items():
            self._feature_scores[f"{col}_mi"] = float(score)
        
        # Sort by MI score
        sorted_features = sorted(mi_dict.items(), key=lambda x: x[1], reverse=True)
        
        removed = []
        if top_k:
            keep_features = [f[0] for f in sorted_features[:top_k]]
            removed = [f[0] for f in sorted_features[top_k:]]
        elif threshold:
            removed = [f[0] for f in sorted_features if f[1] < threshold]
        
        return removed
    
    def _fit_rfe(
        self, 
        df: pd.DataFrame, 
        y: pd.Series,
        columns: List[str],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Use Recursive Feature Elimination
        """
        n_features_to_select = config.get('top_k', len(columns) // 2)
        
        # Use Random Forest as base estimator
        if self.task_type == 'classification':
            estimator = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
        else:
            estimator = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        
        # Prepare data
        X = df[columns].fillna(df[columns].median())
        
        # Apply RFE
        rfe = RFE(estimator, n_features_to_select=n_features_to_select, step=1)
        rfe.fit(X, y)
        
        # Get rankings
        rankings = dict(zip(columns, rfe.ranking_))
        for col, rank in rankings.items():
            self._feature_scores[f"{col}_rfe_rank"] = int(rank)
        
        # Get removed features (ranking > 1)
        removed = [col for col, rank in rankings.items() if rank > 1]
        
        return removed
    
    def get_selection_report(self) -> Dict[str, Any]:
        """
        Generate report of feature selection
        """
        return {
            "enabled": self.enabled,
            "methods_applied": [m.get('type') for m in self.methods],
            "features_in": len(self._feature_names_in),
            "features_out": len(self._selected_features),
            "features_removed": self._removed_features,
            "feature_scores": self._feature_scores,
            "variance_scores": self._variance_scores
        }
    
    def get_high_correlations(self, threshold: float = 0.9) -> List[Dict[str, Any]]:
        """
        Get list of highly correlated feature pairs
        """
        if self._correlation_matrix is None:
            return []
        
        correlations = []
        corr = self._correlation_matrix
        
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                if corr.iloc[i, j] > threshold:
                    correlations.append({
                        "feature1": corr.columns[i],
                        "feature2": corr.columns[j],
                        "correlation": float(corr.iloc[i, j])
                    })
        
        return sorted(correlations, key=lambda x: x["correlation"], reverse=True)
