"""
Pipeline Executor
Executes preprocessing pipelines on data
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from datetime import datetime
import logging

from .pipeline_builder import PipelineBuilder

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """
    Executes preprocessing pipelines
    
    Handles:
        - Fitting pipelines on training data
        - Transforming new data
        - Saving/loading fitted pipelines
        - Generating transformation reports
    """
    
    def __init__(self, builder: PipelineBuilder = None):
        """
        Initialize PipelineExecutor
        
        Args:
            builder: Built PipelineBuilder instance
        """
        self.builder = builder
        self._is_fitted = False
        self._fit_report: Dict[str, Any] = {}
        self._transform_report: Dict[str, Any] = {}
        self._feature_names_in: List[str] = []
        self._feature_names_out: List[str] = []
        self._fitting_stats: Dict[str, Any] = {}
    
    def fit(
        self, 
        df: pd.DataFrame, 
        y: Optional[pd.Series] = None,
        verbose: bool = True
    ) -> 'PipelineExecutor':
        """
        Fit all pipeline components
        
        Args:
            df: Training DataFrame
            y: Optional target variable (for supervised methods)
            verbose: Whether to log progress
        
        Returns:
            self
        """
        if self.builder is None or not self.builder.is_built:
            raise ValueError("Pipeline must be built before fitting")
        
        self._feature_names_in = df.columns.tolist()
        self._fit_report = {
            'start_time': datetime.utcnow().isoformat(),
            'input_shape': list(df.shape),
            'steps': []
        }
        
        current_df = df.copy()
        
        for step in self.builder.get_pipeline_steps():
            step_name = step['name']
            component = step['component']
            
            if verbose:
                logger.info(f"Fitting step: {step_name}")
            
            step_report = {
                'name': step_name,
                'stage': step['stage'],
                'input_shape': list(current_df.shape)
            }
            
            try:
                # Fit the component
                component.fit(current_df, y)
                
                # Transform for next step
                current_df = component.transform(current_df)
                
                step_report['output_shape'] = list(current_df.shape)
                step_report['status'] = 'success'
                step_report['fit_stats'] = component.fit_stats
                
            except Exception as e:
                step_report['status'] = 'error'
                step_report['error'] = str(e)
                logger.error(f"Error in step {step_name}: {e}")
                raise
            
            self._fit_report['steps'].append(step_report)
        
        self._feature_names_out = current_df.columns.tolist()
        self._fit_report['end_time'] = datetime.utcnow().isoformat()
        self._fit_report['output_shape'] = list(current_df.shape)
        self._fit_report['feature_names_out'] = self._feature_names_out
        
        self._is_fitted = True
        
        return self
    
    def transform(
        self, 
        df: pd.DataFrame,
        verbose: bool = False
    ) -> pd.DataFrame:
        """
        Transform data using fitted pipeline
        
        Args:
            df: DataFrame to transform
            verbose: Whether to log progress
        
        Returns:
            Transformed DataFrame
        """
        if not self._is_fitted:
            raise ValueError("Pipeline must be fitted before transform")
        
        self._transform_report = {
            'start_time': datetime.utcnow().isoformat(),
            'input_shape': list(df.shape),
            'steps': []
        }
        
        current_df = df.copy()
        
        for step in self.builder.get_pipeline_steps():
            step_name = step['name']
            component = step['component']
            
            if verbose:
                logger.info(f"Transforming step: {step_name}")
            
            step_report = {
                'name': step_name,
                'input_shape': list(current_df.shape)
            }
            
            try:
                current_df = component.transform(current_df)
                step_report['output_shape'] = list(current_df.shape)
                step_report['status'] = 'success'
                
            except Exception as e:
                step_report['status'] = 'error'
                step_report['error'] = str(e)
                logger.error(f"Error in step {step_name}: {e}")
                raise
            
            self._transform_report['steps'].append(step_report)
        
        self._transform_report['end_time'] = datetime.utcnow().isoformat()
        self._transform_report['output_shape'] = list(current_df.shape)
        
        return current_df
    
    def fit_transform(
        self, 
        df: pd.DataFrame, 
        y: Optional[pd.Series] = None,
        verbose: bool = True
    ) -> pd.DataFrame:
        """
        Fit and transform in one step
        
        Args:
            df: Training DataFrame
            y: Optional target variable
            verbose: Whether to log progress
        
        Returns:
            Transformed DataFrame
        """
        self.fit(df, y, verbose)
        return self.transform(df, verbose=False)
    
    def save(self, path: str) -> None:
        """
        Save fitted pipeline to file
        
        Args:
            path: Path to save pipeline (pickle file)
        """
        if not self._is_fitted:
            raise ValueError("Pipeline must be fitted before saving")
        
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Collect state from all components
        pipeline_state = {
            'config': self.builder.config,
            'is_fitted': self._is_fitted,
            'feature_names_in': self._feature_names_in,
            'feature_names_out': self._feature_names_out,
            'fit_report': self._fit_report,
            'steps': []
        }
        
        for step in self.builder.get_pipeline_steps():
            step_state = {
                'name': step['name'],
                'stage': step['stage'],
                'component_class': step['component'].__class__.__name__,
                'component_state': step['component'].get_state()
            }
            pipeline_state['steps'].append(step_state)
        
        with open(save_path, 'wb') as f:
            pickle.dump(pipeline_state, f)
        
        # Also save metadata as JSON
        metadata_path = save_path.with_suffix('.json')
        metadata = {
            'feature_names_in': self._feature_names_in,
            'feature_names_out': self._feature_names_out,
            'config': self.builder.config,
            'fit_report': self._fit_report,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Pipeline saved to {save_path}")
    
    @classmethod
    def load(cls, path: str) -> 'PipelineExecutor':
        """
        Load fitted pipeline from file
        
        Args:
            path: Path to pipeline file
        
        Returns:
            Loaded PipelineExecutor
        """
        with open(path, 'rb') as f:
            pipeline_state = pickle.load(f)
        
        # Rebuild pipeline
        builder = PipelineBuilder(pipeline_state['config'])
        builder.build()
        
        # Restore component states
        for step_state, step in zip(pipeline_state['steps'], builder.get_pipeline_steps()):
            step['component'].set_state(step_state['component_state'])
        
        # Create executor
        executor = cls(builder)
        executor._is_fitted = pipeline_state['is_fitted']
        executor._feature_names_in = pipeline_state['feature_names_in']
        executor._feature_names_out = pipeline_state['feature_names_out']
        executor._fit_report = pipeline_state.get('fit_report', {})
        
        logger.info(f"Pipeline loaded from {path}")
        
        return executor
    
    def get_fit_report(self) -> Dict[str, Any]:
        """Get the fitting report"""
        return self._fit_report.copy()
    
    def get_transform_report(self) -> Dict[str, Any]:
        """Get the latest transform report"""
        return self._transform_report.copy()
    
    def get_feature_names(self) -> Tuple[List[str], List[str]]:
        """
        Get input and output feature names
        
        Returns:
            Tuple of (input_features, output_features)
        """
        return self._feature_names_in.copy(), self._feature_names_out.copy()
    
    def preview(
        self, 
        df: pd.DataFrame, 
        sample_size: int = 10
    ) -> Dict[str, Any]:
        """
        Preview pipeline transformations on sample data
        
        Args:
            df: Input DataFrame
            sample_size: Number of rows to preview
        
        Returns:
            Preview results with before/after samples
        """
        if not self._is_fitted:
            raise ValueError("Pipeline must be fitted before preview")
        
        # Sample data
        sample_df = df.head(sample_size)
        
        preview = {
            'sample_size': len(sample_df),
            'input_columns': sample_df.columns.tolist(),
            'input_sample': sample_df.to_dict(orient='records'),
            'transformations': []
        }
        
        current_df = sample_df.copy()
        
        for step in self.builder.get_pipeline_steps():
            step_name = step['name']
            component = step['component']
            
            before_cols = current_df.columns.tolist()
            current_df = component.transform(current_df)
            after_cols = current_df.columns.tolist()
            
            transformation = {
                'step': step_name,
                'columns_before': len(before_cols),
                'columns_after': len(after_cols),
                'new_columns': list(set(after_cols) - set(before_cols)),
                'removed_columns': list(set(before_cols) - set(after_cols))
            }
            preview['transformations'].append(transformation)
        
        preview['output_columns'] = current_df.columns.tolist()
        preview['output_sample'] = current_df.to_dict(orient='records')
        
        return preview
    
    @property
    def is_fitted(self) -> bool:
        return self._is_fitted
    
    @property
    def feature_names_in(self) -> List[str]:
        return self._feature_names_in
    
    @property
    def feature_names_out(self) -> List[str]:
        return self._feature_names_out
