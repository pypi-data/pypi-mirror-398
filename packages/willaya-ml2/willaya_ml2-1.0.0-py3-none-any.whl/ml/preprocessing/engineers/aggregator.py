"""
Aggregator
Creates aggregated features and binning transformations
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

from .base import BaseEngineer


class Aggregator(BaseEngineer):
    """
    Creates aggregated features and performs binning operations
    
    Features:
        - Binning: Discretize continuous variables
        - Group aggregations: Aggregate features by groups
        - Rolling statistics: Calculate rolling windows (if time series)
    """
    
    VALID_BIN_STRATEGIES = ['uniform', 'quantile', 'kmeans', 'custom']
    VALID_AGGREGATIONS = ['mean', 'median', 'sum', 'min', 'max', 'std', 'count', 'nunique']
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Aggregator
        
        Config options:
            - bins: List of binning configurations
                - column: Column to bin
                - strategy: 'uniform', 'quantile', 'kmeans', 'custom'
                - n_bins: Number of bins
                - labels: Optional labels for bins
                - custom_bins: For 'custom' strategy, list of bin edges
            
            - group_aggregations: List of group aggregation configs
                - group_by: Column(s) to group by
                - column: Column to aggregate
                - aggregations: List of aggregation functions
                
            - rolling: List of rolling window configs (for time series)
                - column: Column to calculate rolling stats
                - window: Window size
                - statistics: List of stats to calculate
        """
        super().__init__(config)
        
        self.bins = self.config.get('bins', [])
        self.group_aggregations = self.config.get('group_aggregations', [])
        self.rolling = self.config.get('rolling', [])
        
        # Fitted values
        self._bin_discretizers: Dict[str, KBinsDiscretizer] = {}
        self._custom_bins: Dict[str, List[float]] = {}
        self._group_agg_values: Dict[str, pd.DataFrame] = {}
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'Aggregator':
        """
        Fit the aggregator - learn binning edges and group statistics
        """
        self._validate_input(df)
        
        self._bin_discretizers = {}
        self._custom_bins = {}
        self._group_agg_values = {}
        self._new_columns = []
        
        # Fit binning
        for bin_config in self.bins:
            column = bin_config.get('column')
            strategy = bin_config.get('strategy', 'quantile')
            n_bins = bin_config.get('n_bins', 5)
            custom_bins = bin_config.get('custom_bins')
            
            if column not in df.columns:
                continue
            
            if strategy == 'custom' and custom_bins:
                self._custom_bins[column] = custom_bins
            else:
                # Use sklearn discretizer
                sklearn_strategy = 'uniform' if strategy == 'uniform' else 'quantile'
                if strategy == 'kmeans':
                    sklearn_strategy = 'kmeans'
                
                discretizer = KBinsDiscretizer(
                    n_bins=n_bins,
                    encode='ordinal',
                    strategy=sklearn_strategy
                )
                
                # Fit on non-null values
                valid_data = df[column].dropna().values.reshape(-1, 1)
                if len(valid_data) > 0:
                    discretizer.fit(valid_data)
                    self._bin_discretizers[column] = discretizer
            
            self._new_columns.append(f"{column}_binned")
        
        # Fit group aggregations
        for agg_config in self.group_aggregations:
            group_by = agg_config.get('group_by')
            column = agg_config.get('column')
            aggregations = agg_config.get('aggregations', ['mean'])
            
            if isinstance(group_by, str):
                group_by = [group_by]
            
            if column not in df.columns:
                continue
            
            # Calculate group statistics
            agg_dict = {column: aggregations}
            grouped = df.groupby(group_by).agg(agg_dict)
            grouped.columns = [f"{column}_{agg}_by_{'_'.join(group_by)}" for agg in aggregations]
            
            key = f"{column}_by_{'_'.join(group_by)}"
            self._group_agg_values[key] = grouped
            
            for agg in aggregations:
                self._new_columns.append(f"{column}_{agg}_by_{'_'.join(group_by)}")
        
        # Store fitting stats
        self._fit_stats = {
            "binned_columns": list(self._bin_discretizers.keys()) + list(self._custom_bins.keys()),
            "group_aggregations": list(self._group_agg_values.keys()),
            "new_columns": self._new_columns
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply aggregation transformations
        """
        self._validate_fitted()
        
        df_result = df.copy()
        
        # Apply binning
        for bin_config in self.bins:
            column = bin_config.get('column')
            labels = bin_config.get('labels')
            
            if column not in df_result.columns:
                continue
            
            new_col = f"{column}_binned"
            
            if column in self._custom_bins:
                # Custom binning
                bins = self._custom_bins[column]
                df_result[new_col] = pd.cut(
                    df_result[column],
                    bins=bins,
                    labels=labels if labels else False,
                    include_lowest=True
                )
            elif column in self._bin_discretizers:
                # Sklearn discretizer
                discretizer = self._bin_discretizers[column]
                valid_mask = df_result[column].notna()
                
                binned = np.full(len(df_result), np.nan)
                if valid_mask.any():
                    valid_data = df_result.loc[valid_mask, column].values.reshape(-1, 1)
                    binned[valid_mask] = discretizer.transform(valid_data).flatten()
                
                if labels:
                    # Map to labels
                    label_map = {i: labels[i] for i in range(len(labels))}
                    df_result[new_col] = pd.Series(binned).map(label_map)
                else:
                    df_result[new_col] = binned
        
        # Apply group aggregations
        for agg_config in self.group_aggregations:
            group_by = agg_config.get('group_by')
            column = agg_config.get('column')
            aggregations = agg_config.get('aggregations', ['mean'])
            
            if isinstance(group_by, str):
                group_by = [group_by]
            
            key = f"{column}_by_{'_'.join(group_by)}"
            
            if key in self._group_agg_values:
                grouped = self._group_agg_values[key]
                
                # Merge back to main dataframe
                df_result = df_result.merge(
                    grouped,
                    left_on=group_by,
                    right_index=True,
                    how='left'
                )
        
        # Apply rolling statistics
        for roll_config in self.rolling:
            column = roll_config.get('column')
            window = roll_config.get('window', 3)
            statistics = roll_config.get('statistics', ['mean'])
            
            if column not in df_result.columns:
                continue
            
            rolling = df_result[column].rolling(window=window, min_periods=1)
            
            for stat in statistics:
                new_col = f"{column}_rolling_{stat}_{window}"
                
                if stat == 'mean':
                    df_result[new_col] = rolling.mean()
                elif stat == 'std':
                    df_result[new_col] = rolling.std()
                elif stat == 'min':
                    df_result[new_col] = rolling.min()
                elif stat == 'max':
                    df_result[new_col] = rolling.max()
                elif stat == 'sum':
                    df_result[new_col] = rolling.sum()
        
        return df_result
    
    def add_binning(
        self,
        column: str,
        strategy: str = 'quantile',
        n_bins: int = 5,
        labels: List[str] = None,
        custom_bins: List[float] = None
    ) -> 'Aggregator':
        """
        Add a binning configuration
        """
        self.bins.append({
            'column': column,
            'strategy': strategy,
            'n_bins': n_bins,
            'labels': labels,
            'custom_bins': custom_bins
        })
        self._is_fitted = False
        return self
    
    def add_group_aggregation(
        self,
        group_by: Union[str, List[str]],
        column: str,
        aggregations: List[str] = None
    ) -> 'Aggregator':
        """
        Add a group aggregation configuration
        """
        self.group_aggregations.append({
            'group_by': group_by,
            'column': column,
            'aggregations': aggregations or ['mean']
        })
        self._is_fitted = False
        return self
    
    def get_bin_edges(self, column: str) -> Optional[List[float]]:
        """
        Get bin edges for a column
        """
        if column in self._custom_bins:
            return self._custom_bins[column]
        
        if column in self._bin_discretizers:
            return self._bin_discretizers[column].bin_edges_[0].tolist()
        
        return None
