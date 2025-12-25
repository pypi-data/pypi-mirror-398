"""
Pipeline Builder
Constructs preprocessing pipelines from configuration
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

from .cleaners import MissingValueHandler, OutlierHandler, DuplicateHandler, TypeConverter
from .engineers import FormulaEngine, DateEngineer, Aggregator
from .processors import CategoricalEncoder, NumericalScaler, FeatureSelector
from .analyzers import DataAnalyzer


class PipelineBuilder:
    """
    Builds preprocessing pipelines from configuration
    
    Pipeline stages:
        1. Cleaning: missing values, outliers, duplicates, type conversion
        2. Feature Engineering: derived features, date features, binning
        3. Processing: categorical encoding, numerical scaling, feature selection
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize PipelineBuilder
        
        Args:
            config: Complete preprocessing configuration
        """
        self.config = config or {}
        self._pipeline_steps: List[Dict[str, Any]] = []
        self._is_built = False
    
    def build(self) -> 'PipelineBuilder':
        """
        Build pipeline from configuration
        """
        self._pipeline_steps = []
        
        # Stage 1: Cleaning
        cleaning_config = self.config.get('cleaning', {})
        self._build_cleaning_stage(cleaning_config)
        
        # Stage 2: Feature Engineering
        engineering_config = self.config.get('feature_engineering', {})
        self._build_engineering_stage(engineering_config)
        
        # Stage 3: Processing
        processing_config = self.config.get('processing', {})
        self._build_processing_stage(processing_config)
        
        self._is_built = True
        return self
    
    def _build_cleaning_stage(self, config: Dict[str, Any]) -> None:
        """Build cleaning stage components"""
        
        # Type Conversion (first to ensure correct types)
        type_config = config.get('type_conversion', {})
        if type_config.get('mode') != 'none':
            manual = type_config.get('manual_config', {})
            self._pipeline_steps.append({
                'name': 'type_conversion',
                'stage': 'cleaning',
                'component': TypeConverter({
                    'conversions': manual.get('conversions', []),
                    'auto_detect': type_config.get('mode') == 'auto'
                })
            })
        
        # Missing Values
        missing_config = config.get('missing_values', {})
        if missing_config:
            manual = missing_config.get('manual_config', {})
            self._pipeline_steps.append({
                'name': 'missing_values',
                'stage': 'cleaning',
                'component': MissingValueHandler({
                    'strategy': manual.get('strategy', 'median'),
                    'fill_value': manual.get('fill_value'),
                    'per_column': manual.get('per_column', {})
                })
            })
        
        # Outliers
        outlier_config = config.get('outliers', {})
        if outlier_config:
            manual = outlier_config.get('manual_config', {})
            self._pipeline_steps.append({
                'name': 'outliers',
                'stage': 'cleaning',
                'component': OutlierHandler({
                    'method': manual.get('method', 'iqr'),
                    'action': manual.get('action', 'cap'),
                    'threshold': manual.get('threshold', 1.5),
                    'per_column': manual.get('per_column', {})
                })
            })
        
        # Duplicates
        dup_config = config.get('duplicates', {})
        if dup_config:
            manual = dup_config.get('manual_config', {})
            self._pipeline_steps.append({
                'name': 'duplicates',
                'stage': 'cleaning',
                'component': DuplicateHandler({
                    'action': manual.get('action', 'drop'),
                    'subset': manual.get('subset')
                })
            })
    
    def _build_engineering_stage(self, config: Dict[str, Any]) -> None:
        """Build feature engineering stage components"""
        
        # Derived Features
        derived_config = config.get('derived_features', {})
        if derived_config and derived_config.get('mode') == 'manual':
            manual = derived_config.get('manual_config', {})
            features = manual.get('features', [])
            if features:
                self._pipeline_steps.append({
                    'name': 'derived_features',
                    'stage': 'engineering',
                    'component': FormulaEngine({
                        'features': features
                    })
                })
        
        # Date Features
        date_config = config.get('date_features', {})
        if date_config:
            manual = date_config.get('manual_config', {})
            self._pipeline_steps.append({
                'name': 'date_features',
                'stage': 'engineering',
                'component': DateEngineer({
                    'source_columns': manual.get('source_columns', []),
                    'extract': manual.get('extract', ['year', 'month', 'day', 'dayofweek']),
                    'drop_original': manual.get('drop_original', False),
                    'cyclical_encoding': manual.get('cyclical_encoding', False)
                })
            })
        
        # Binning
        binning_config = config.get('binning', {})
        if binning_config and binning_config.get('mode') == 'manual':
            manual = binning_config.get('manual_config', {})
            bins = manual.get('bins', [])
            if bins:
                self._pipeline_steps.append({
                    'name': 'binning',
                    'stage': 'engineering',
                    'component': Aggregator({
                        'bins': bins
                    })
                })
    
    def _build_processing_stage(self, config: Dict[str, Any]) -> None:
        """Build processing stage components"""
        
        # Categorical Encoding
        cat_config = config.get('categorical_encoding', {})
        if cat_config:
            manual = cat_config.get('manual_config', {})
            self._pipeline_steps.append({
                'name': 'categorical_encoding',
                'stage': 'processing',
                'component': CategoricalEncoder({
                    'default_strategy': manual.get('default_strategy', 'onehot'),
                    'per_column': manual.get('per_column', {}),
                    'handle_unknown': manual.get('handle_unknown', 'ignore'),
                    'min_frequency': manual.get('min_frequency'),
                    'max_categories': manual.get('max_categories')
                })
            })
        
        # Numerical Scaling
        scale_config = config.get('numerical_scaling', {})
        if scale_config:
            manual = scale_config.get('manual_config', {})
            self._pipeline_steps.append({
                'name': 'numerical_scaling',
                'stage': 'processing',
                'component': NumericalScaler({
                    'default_strategy': manual.get('default_strategy', 'standard'),
                    'per_column': manual.get('per_column', {}),
                    'exclude_columns': manual.get('exclude_columns', [])
                })
            })
        
        # Feature Selection
        selection_config = config.get('feature_selection', {})
        if selection_config:
            manual = selection_config.get('manual_config', {})
            task_type = self.config.get('settings', {}).get('task_type', 'classification')
            self._pipeline_steps.append({
                'name': 'feature_selection',
                'stage': 'processing',
                'component': FeatureSelector({
                    'enabled': manual.get('enabled', True),
                    'methods': manual.get('methods', []),
                    'task_type': task_type,
                    'exclude_columns': manual.get('exclude_columns', [])
                })
            })
    
    def build_from_auto(self, df: pd.DataFrame) -> 'PipelineBuilder':
        """
        Build pipeline automatically from data analysis
        
        Args:
            df: Input DataFrame to analyze
        
        Returns:
            self with built pipeline
        """
        # Analyze data
        analyzer = DataAnalyzer(df)
        analysis = analyzer.analyze()
        
        # Use auto-generated config
        self.config = analysis['auto_config_generated']
        
        return self.build()
    
    def get_pipeline_steps(self) -> List[Dict[str, Any]]:
        """Get list of pipeline steps"""
        return self._pipeline_steps.copy()
    
    def get_step(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific pipeline step by name"""
        for step in self._pipeline_steps:
            if step['name'] == name:
                return step
        return None
    
    def remove_step(self, name: str) -> 'PipelineBuilder':
        """Remove a step from the pipeline"""
        self._pipeline_steps = [s for s in self._pipeline_steps if s['name'] != name]
        return self
    
    def add_step(
        self, 
        name: str, 
        stage: str, 
        component: Any, 
        position: Optional[int] = None
    ) -> 'PipelineBuilder':
        """
        Add a custom step to the pipeline
        
        Args:
            name: Step name
            stage: Stage name (cleaning, engineering, processing)
            component: Pipeline component instance
            position: Optional position in pipeline
        """
        step = {
            'name': name,
            'stage': stage,
            'component': component
        }
        
        if position is not None:
            self._pipeline_steps.insert(position, step)
        else:
            self._pipeline_steps.append(step)
        
        return self
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the built pipeline"""
        stages = {'cleaning': [], 'engineering': [], 'processing': []}
        
        for step in self._pipeline_steps:
            stage = step['stage']
            if stage in stages:
                stages[stage].append({
                    'name': step['name'],
                    'component_type': step['component'].__class__.__name__
                })
        
        return {
            'is_built': self._is_built,
            'total_steps': len(self._pipeline_steps),
            'stages': stages
        }
    
    @property
    def is_built(self) -> bool:
        return self._is_built
