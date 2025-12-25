"""
Duplicate Handler
Handles duplicate rows in DataFrames
"""
from typing import Dict, Any, List, Optional
import pandas as pd

from .base import BaseCleaner


class DuplicateHandler(BaseCleaner):
    """
    Handles duplicate rows in DataFrames
    
    Actions:
        - drop: Drop all duplicates (keep first by default)
        - keep_first: Keep first occurrence, drop rest
        - keep_last: Keep last occurrence, drop rest
        - none: Do nothing
    """
    
    VALID_ACTIONS = ['drop', 'keep_first', 'keep_last', 'none']
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize DuplicateHandler
        
        Config options:
            - action: How to handle duplicates (default: 'drop')
            - subset: List of columns to check for duplicates (default: all columns)
        """
        super().__init__(config)
        
        self.action = self.config.get('action', 'drop')
        self.subset = self.config.get('subset', None)
        
        # Fitted values
        self._duplicate_count: int = 0
        self._duplicate_indices: List[int] = []
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'DuplicateHandler':
        """
        Fit the handler - identify duplicates
        """
        self._validate_input(df)
        
        # Determine subset
        check_cols = self.subset if self.subset else df.columns.tolist()
        
        # Find duplicates
        if self.action == 'keep_first':
            duplicates = df.duplicated(subset=check_cols, keep='first')
        elif self.action == 'keep_last':
            duplicates = df.duplicated(subset=check_cols, keep='last')
        else:
            duplicates = df.duplicated(subset=check_cols, keep='first')
        
        self._duplicate_count = int(duplicates.sum())
        self._duplicate_indices = df.index[duplicates].tolist()
        
        if self._duplicate_count > 0:
            self._affected_columns = check_cols
        
        # Store fitting stats
        self._fit_stats = {
            "duplicate_count": self._duplicate_count,
            "duplicate_percent": round(self._duplicate_count / len(df) * 100, 2),
            "subset_columns": check_cols,
            "action": self.action
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply duplicate handling
        """
        self._validate_fitted()
        
        if self.action == 'none' or self._duplicate_count == 0:
            self._affected_rows = 0
            return df.copy()
        
        df_result = df.copy()
        check_cols = self.subset if self.subset else df_result.columns.tolist()
        
        if self.action == 'keep_first' or self.action == 'drop':
            df_result = df_result.drop_duplicates(subset=check_cols, keep='first')
        elif self.action == 'keep_last':
            df_result = df_result.drop_duplicates(subset=check_cols, keep='last')
        
        self._affected_rows = len(df) - len(df_result)
        
        return df_result
    
    def get_duplicate_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a report of duplicates in DataFrame
        """
        check_cols = self.subset if self.subset else df.columns.tolist()
        
        # Count duplicates
        duplicates = df.duplicated(subset=check_cols, keep=False)
        duplicate_count = int(duplicates.sum())
        
        # Get duplicate groups
        duplicate_groups = []
        if duplicate_count > 0:
            dup_df = df[duplicates]
            grouped = dup_df.groupby(check_cols).size().reset_index(name='count')
            grouped = grouped[grouped['count'] > 1]
            
            for _, row in grouped.head(10).iterrows():  # Limit to 10 examples
                duplicate_groups.append({
                    "values": {col: row[col] for col in check_cols if col in row.index},
                    "count": int(row['count'])
                })
        
        return {
            "total_duplicates": duplicate_count,
            "duplicate_percent": round(duplicate_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "unique_rows": len(df) - duplicate_count,
            "columns_checked": check_cols,
            "sample_groups": duplicate_groups,
            "action_to_apply": self.action
        }
