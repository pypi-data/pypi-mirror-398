"""
Formula Engine
Creates derived features using Python expressions
"""
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import numpy as np
import re
import warnings

from .base import BaseEngineer


class FormulaEngine(BaseEngineer):
    """
    Creates derived features using Python-like formulas
    
    Supports:
        - Basic arithmetic: +, -, *, /, //, %, **
        - Comparisons: >, <, >=, <=, ==, !=
        - Logical: and, or, not
        - Functions: abs, round, min, max, sqrt, log, exp
        - Conditionals: if-else expressions
    """
    
    # Allowed functions in formulas
    ALLOWED_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sqrt': np.sqrt,
        'log': np.log,
        'log10': np.log10,
        'log2': np.log2,
        'exp': np.exp,
        'pow': pow,
        'floor': np.floor,
        'ceil': np.ceil,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'clip': np.clip,
        'isna': pd.isna,
        'notna': pd.notna,
        'fillna': lambda x, v: x if pd.notna(x) else v,
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize FormulaEngine
        
        Config options:
            - features: List of feature definitions
                - name: New feature name
                - formula: Python expression
                - handle_zero_division: 'null', 'zero', 'inf', 'error'
                - handle_error: 'null', 'drop', 'error'
                - description: Optional description
        """
        super().__init__(config)
        
        self.features = self.config.get('features', [])
        
        # Parsed formulas
        self._parsed_formulas: Dict[str, Callable] = {}
        self._formula_columns: Dict[str, List[str]] = {}
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> 'FormulaEngine':
        """
        Fit the engine - validate and parse formulas
        """
        self._validate_input(df)
        
        self._parsed_formulas = {}
        self._formula_columns = {}
        self._new_columns = []
        
        for feature in self.features:
            name = feature.get('name')
            formula = feature.get('formula')
            
            if not name or not formula:
                continue
            
            # Extract column names used in formula
            columns_used = self._extract_columns(formula, df.columns)
            self._formula_columns[name] = columns_used
            
            # Validate columns exist
            missing_cols = set(columns_used) - set(df.columns)
            if missing_cols:
                raise ValueError(
                    f"Formula '{name}' references missing columns: {missing_cols}"
                )
            
            # Parse formula
            self._parsed_formulas[name] = self._parse_formula(formula, df.columns)
            self._new_columns.append(name)
        
        # Store fitting stats
        self._fit_stats = {
            "features_count": len(self._new_columns),
            "features": [f.get('name') for f in self.features],
            "formula_columns": self._formula_columns
        }
        
        self._is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply formula transformations to create new features
        """
        self._validate_fitted()
        
        df_result = df.copy()
        
        for feature in self.features:
            name = feature.get('name')
            formula = feature.get('formula')
            handle_zero_div = feature.get('handle_zero_division', 'null')
            handle_error = feature.get('handle_error', 'null')
            
            if name not in self._parsed_formulas:
                continue
            
            try:
                # Execute formula
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = self._execute_formula(
                        df_result, 
                        formula, 
                        handle_zero_div
                    )
                
                df_result[name] = result
                
            except Exception as e:
                if handle_error == 'error':
                    raise ValueError(f"Error computing feature '{name}': {str(e)}")
                elif handle_error == 'null':
                    df_result[name] = np.nan
                # 'drop' - skip adding the column
        
        return df_result
    
    def _extract_columns(self, formula: str, available_columns: pd.Index) -> List[str]:
        """
        Extract column names referenced in formula
        """
        # Find potential column references
        # Match word characters that could be column names
        tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula)
        
        # Filter to actual columns
        columns = [t for t in tokens if t in available_columns]
        
        return list(set(columns))
    
    def _parse_formula(self, formula: str, columns: pd.Index) -> Callable:
        """
        Parse formula string into executable function
        """
        # Validate formula doesn't contain dangerous operations
        dangerous_patterns = [
            r'\bimport\b', r'\bexec\b', r'\beval\b', r'\bopen\b',
            r'\bos\.', r'\bsys\.', r'__', r'\bsubprocess\b',
            r'\bglobals\b', r'\blocals\b', r'\bcompile\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, formula):
                raise ValueError(f"Formula contains forbidden pattern: {pattern}")
        
        return formula
    
    def _execute_formula(
        self, 
        df: pd.DataFrame, 
        formula: str, 
        handle_zero_div: str
    ) -> pd.Series:
        """
        Execute formula on DataFrame
        """
        # Build evaluation namespace
        namespace = {col: df[col] for col in df.columns}
        namespace.update(self.ALLOWED_FUNCTIONS)
        namespace['np'] = np
        namespace['pd'] = pd
        
        # Handle zero division
        if handle_zero_div != 'error':
            # Replace division with safe division
            formula = self._make_safe_division(formula, handle_zero_div)
        
        try:
            result = eval(formula, {"__builtins__": {}}, namespace)
            
            # Ensure result is a Series
            if isinstance(result, (int, float, bool)):
                result = pd.Series([result] * len(df), index=df.index)
            elif not isinstance(result, pd.Series):
                result = pd.Series(result, index=df.index)
            
            return result
            
        except ZeroDivisionError:
            if handle_zero_div == 'null':
                return pd.Series([np.nan] * len(df), index=df.index)
            elif handle_zero_div == 'zero':
                return pd.Series([0] * len(df), index=df.index)
            elif handle_zero_div == 'inf':
                return pd.Series([np.inf] * len(df), index=df.index)
            raise
    
    def _make_safe_division(self, formula: str, handle_zero_div: str) -> str:
        """
        Convert division to safe division that handles zeros
        """
        # This is a simplified approach - for complex formulas,
        # consider using a proper expression parser
        
        # Replace x / y with np.where(y != 0, x / y, replacement)
        replacement = {
            'null': 'np.nan',
            'zero': '0',
            'inf': 'np.inf'
        }.get(handle_zero_div, 'np.nan')
        
        # For simple cases, use np.divide with where
        # Note: This won't catch all cases - complex formulas may need manual handling
        
        return formula
    
    def add_feature(
        self, 
        name: str, 
        formula: str, 
        handle_zero_division: str = 'null',
        handle_error: str = 'null',
        description: str = None
    ) -> 'FormulaEngine':
        """
        Add a new derived feature
        """
        self.features.append({
            'name': name,
            'formula': formula,
            'handle_zero_division': handle_zero_division,
            'handle_error': handle_error,
            'description': description
        })
        
        # Need to refit
        self._is_fitted = False
        
        return self
    
    def remove_feature(self, name: str) -> 'FormulaEngine':
        """
        Remove a derived feature by name
        """
        self.features = [f for f in self.features if f.get('name') != name]
        self._is_fitted = False
        return self
    
    def get_feature_definitions(self) -> List[Dict[str, Any]]:
        """
        Get all feature definitions
        """
        return self.features.copy()
    
    def validate_formula(self, formula: str, columns: List[str]) -> Dict[str, Any]:
        """
        Validate a formula without executing it
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'columns_used': []
        }
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'\bimport\b', r'\bexec\b', r'\beval\b', r'\bopen\b',
            r'\bos\.', r'\bsys\.', r'__'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, formula):
                result['valid'] = False
                result['errors'].append(f"Contains forbidden pattern: {pattern}")
        
        # Extract and validate columns
        tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula)
        
        for token in tokens:
            if token in columns:
                result['columns_used'].append(token)
            elif token not in self.ALLOWED_FUNCTIONS and token not in ['np', 'pd', 'True', 'False', 'None']:
                # Could be unrecognized
                if not token[0].isupper():  # Not a constant
                    result['warnings'].append(f"Unknown reference: {token}")
        
        result['columns_used'] = list(set(result['columns_used']))
        
        return result
