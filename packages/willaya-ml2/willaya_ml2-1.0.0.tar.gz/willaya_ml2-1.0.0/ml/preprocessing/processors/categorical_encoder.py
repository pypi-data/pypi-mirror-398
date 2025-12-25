"""
Categorical Encoder
Handles encoding of categorical variables
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder
from category_encoders import TargetEncoder

from .base import BaseProcessor


class CategoricalEncoder(BaseProcessor):
    """
    Encodes categorical variables using various strategies
    
    Strategies:
        - onehot: One-hot encoding (creates binary columns)
        - label: Label encoding (maps to integers)
        - ordinal: Ordinal encoding (with custom order)
        - target: Target encoding (mean of target per category)
        - frequency: Frequency encoding (category frequency)
        - binary: Binary encoding
    """
    
    VALID_STRATEGIES = ['onehot', 'label', 'ordinal', 'target', 'frequency', 'binary']
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize CategoricalEncoder
        
        Config options:
            - default_strategy: Default encoding strategy
            - per_column: Dict of column-specific strategies
            - handle_unknown: How to handle unknown categories ('ignore', 'error', 'infrequent')
            - min_frequency: Minimum frequency for a category (others grouped as 'infrequent')
            - max_categories: Maximum number of categories to keep
        """
        super().__init__(config)
        
        self.default_strategy = self.config.get('default_strategy', 'onehot')
        self.per_column = self.config.get('per_column', {})
        self.handle_unknown = self.config.get('handle_unknown', 'ignore')
        self.min_frequency = self.config.get('min_frequency', None)
        self.max_categories = self.config.get('max_categories', None)
        
        # Fitted encoders
        self._encoders: Dict[str, Any] = {}
        self._categorical_columns: List[str] = []
        self._column_strategies: Dict[str, str] = {}
        self._frequency_maps: Dict[str, Dict[str, float]] = {}
        self._onehot_columns: Dict[str, List[str]] = {}
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'CategoricalEncoder':
        """
        Fit encoders for categorical columns
        """
        self._validate_input(df)
        
        self._encoders = {}
        self._frequency_maps = {}
        self._onehot_columns = {}
        self._feature_names_in = []
        self._feature_names_out = []
        
        # Identify categorical columns
        self._categorical_columns = df.select_dtypes(
            include=['object', 'category', 'bool']
        ).columns.tolist()
        
        self._feature_names_in = self._categorical_columns.copy()
        
        for column in self._categorical_columns:
            strategy = self._get_column_strategy(column)
            self._column_strategies[column] = strategy
            
            series = df[column].copy()
            
            # Handle infrequent categories
            if self.min_frequency or self.max_categories:
                series = self._handle_infrequent(series)
            
            if strategy == 'onehot':
                encoder = OneHotEncoder(
                    sparse_output=False,
                    handle_unknown='ignore' if self.handle_unknown == 'ignore' else 'error'
                )
                encoder.fit(series.values.reshape(-1, 1))
                self._encoders[column] = encoder
                
                # Track new column names
                categories = encoder.categories_[0]
                new_cols = [f"{column}_{cat}" for cat in categories]
                self._onehot_columns[column] = new_cols
                self._feature_names_out.extend(new_cols)
                
            elif strategy == 'label':
                encoder = LabelEncoder()
                # Fit on non-null values
                valid_values = series.dropna().unique()
                encoder.fit(valid_values)
                self._encoders[column] = encoder
                self._feature_names_out.append(column)
                
            elif strategy == 'ordinal':
                col_config = self.per_column.get(column, {})
                categories = col_config.get('categories', [series.dropna().unique().tolist()])
                
                encoder = OrdinalEncoder(
                    categories=categories,
                    handle_unknown='use_encoded_value',
                    unknown_value=-1
                )
                encoder.fit(series.values.reshape(-1, 1))
                self._encoders[column] = encoder
                self._feature_names_out.append(column)
                
            elif strategy == 'target':
                if y is None:
                    raise ValueError("Target encoding requires y (target variable)")
                
                encoder = TargetEncoder(cols=[column])
                temp_df = pd.DataFrame({column: series})
                encoder.fit(temp_df, y)
                self._encoders[column] = encoder
                self._feature_names_out.append(column)
                
            elif strategy == 'frequency':
                # Calculate frequency map
                freq_map = series.value_counts(normalize=True).to_dict()
                self._frequency_maps[column] = freq_map
                self._feature_names_out.append(column)
                
            elif strategy == 'binary':
                # Binary encoding using pandas get_dummies with drop_first
                encoder = OneHotEncoder(
                    sparse_output=False,
                    drop='first',
                    handle_unknown='ignore'
                )
                encoder.fit(series.values.reshape(-1, 1))
                self._encoders[column] = encoder
                
                categories = encoder.categories_[0][1:]  # Dropped first
                new_cols = [f"{column}_{cat}" for cat in categories]
                self._onehot_columns[column] = new_cols
                self._feature_names_out.extend(new_cols)
        
        # Store fitting stats
        self._fit_stats = {
            "categorical_columns": self._categorical_columns,
            "strategies_used": self._column_strategies,
            "features_in": len(self._feature_names_in),
            "features_out": len(self._feature_names_out)
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply encoding transformations
        """
        self._validate_fitted()
        
        df_result = df.copy()
        columns_to_drop = []
        
        for column in self._categorical_columns:
            if column not in df_result.columns:
                continue
            
            strategy = self._column_strategies[column]
            series = df_result[column].copy()
            
            # Handle infrequent categories
            if self.min_frequency or self.max_categories:
                series = self._handle_infrequent(series)
            
            if strategy == 'onehot':
                encoder = self._encoders[column]
                encoded = encoder.transform(series.values.reshape(-1, 1))
                
                new_cols = self._onehot_columns[column]
                encoded_df = pd.DataFrame(encoded, columns=new_cols, index=df_result.index)
                
                df_result = pd.concat([df_result, encoded_df], axis=1)
                columns_to_drop.append(column)
                
            elif strategy == 'label':
                encoder = self._encoders[column]
                
                # Handle unknown categories
                known_classes = set(encoder.classes_)
                
                def safe_transform(val):
                    if pd.isna(val):
                        return np.nan
                    if val in known_classes:
                        return encoder.transform([val])[0]
                    return -1 if self.handle_unknown == 'ignore' else np.nan
                
                df_result[column] = series.apply(safe_transform)
                
            elif strategy == 'ordinal':
                encoder = self._encoders[column]
                
                # Handle nulls
                null_mask = series.isna()
                encoded = np.full(len(series), np.nan)
                
                if not null_mask.all():
                    valid_values = series[~null_mask].values.reshape(-1, 1)
                    encoded[~null_mask] = encoder.transform(valid_values).flatten()
                
                df_result[column] = encoded
                
            elif strategy == 'target':
                encoder = self._encoders[column]
                temp_df = pd.DataFrame({column: series})
                encoded = encoder.transform(temp_df)
                df_result[column] = encoded[column]
                
            elif strategy == 'frequency':
                freq_map = self._frequency_maps[column]
                default_freq = min(freq_map.values()) if freq_map else 0
                df_result[column] = series.map(freq_map).fillna(default_freq)
                
            elif strategy == 'binary':
                encoder = self._encoders[column]
                encoded = encoder.transform(series.values.reshape(-1, 1))
                
                new_cols = self._onehot_columns[column]
                encoded_df = pd.DataFrame(encoded, columns=new_cols, index=df_result.index)
                
                df_result = pd.concat([df_result, encoded_df], axis=1)
                columns_to_drop.append(column)
        
        # Drop original columns for onehot/binary
        if columns_to_drop:
            df_result = df_result.drop(columns=columns_to_drop)
        
        return df_result
    
    def _get_column_strategy(self, column: str) -> str:
        """Get encoding strategy for a column"""
        if column in self.per_column:
            return self.per_column[column].get('strategy', self.default_strategy)
        return self.default_strategy
    
    def _handle_infrequent(self, series: pd.Series) -> pd.Series:
        """Group infrequent categories"""
        value_counts = series.value_counts()
        
        infrequent_cats = set()
        
        if self.min_frequency:
            freq_threshold = self.min_frequency * len(series)
            infrequent_cats.update(
                value_counts[value_counts < freq_threshold].index
            )
        
        if self.max_categories:
            if len(value_counts) > self.max_categories:
                keep_cats = value_counts.head(self.max_categories).index
                infrequent_cats.update(
                    set(value_counts.index) - set(keep_cats)
                )
        
        if infrequent_cats:
            return series.replace(infrequent_cats, 'INFREQUENT')
        
        return series
    
    def get_encoding_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate report of encoding transformations
        """
        report = {
            "categorical_columns": [],
            "total_new_columns": 0
        }
        
        for col in df.select_dtypes(include=['object', 'category']).columns:
            col_info = {
                "column": col,
                "unique_values": int(df[col].nunique()),
                "strategy": self._get_column_strategy(col)
            }
            
            strategy = col_info["strategy"]
            if strategy == 'onehot':
                col_info["new_columns_count"] = df[col].nunique()
            else:
                col_info["new_columns_count"] = 1
            
            report["categorical_columns"].append(col_info)
            report["total_new_columns"] += col_info["new_columns_count"]
        
        return report
