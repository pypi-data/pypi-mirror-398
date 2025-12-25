"""
Preprocessing Module
Complete preprocessing pipeline for ML data preparation

This module provides:
    - Data analysis and auto-recommendation
    - Cleaning: missing values, outliers, duplicates, type conversion
    - Feature Engineering: derived features, date features, binning
    - Processing: categorical encoding, numerical scaling, feature selection
    - Pipeline building, execution, and versioning
"""

# Analyzers
from .analyzers import (
    DataAnalyzer,
    StatsCalculator,
    RecommendationEngine
)

# Cleaners
from .cleaners import (
    BaseCleaner,
    MissingValueHandler,
    OutlierHandler,
    DuplicateHandler,
    TypeConverter
)

# Engineers
from .engineers import (
    BaseEngineer,
    FormulaEngine,
    DateEngineer,
    Aggregator
)

# Processors
from .processors import (
    BaseProcessor,
    CategoricalEncoder,
    NumericalScaler,
    FeatureSelector
)

# Pipeline
from .pipeline_builder import PipelineBuilder
from .pipeline_executor import PipelineExecutor
from .pipeline_registry import PipelineRegistry


__all__ = [
    # Analyzers
    "DataAnalyzer",
    "StatsCalculator",
    "RecommendationEngine",
    
    # Cleaners
    "BaseCleaner",
    "MissingValueHandler",
    "OutlierHandler",
    "DuplicateHandler",
    "TypeConverter",
    
    # Engineers
    "BaseEngineer",
    "FormulaEngine",
    "DateEngineer",
    "Aggregator",
    
    # Processors
    "BaseProcessor",
    "CategoricalEncoder",
    "NumericalScaler",
    "FeatureSelector",
    
    # Pipeline
    "PipelineBuilder",
    "PipelineExecutor",
    "PipelineRegistry"
]


def create_pipeline(
    config: dict = None,
    auto_from_data: bool = False,
    df = None
) -> PipelineExecutor:
    """
    Convenience function to create a preprocessing pipeline
    
    Args:
        config: Pipeline configuration dict
        auto_from_data: If True, analyze df and auto-generate config
        df: DataFrame for auto-detection (required if auto_from_data=True)
    
    Returns:
        PipelineExecutor ready for fit/transform
    
    Example:
        # Manual config
        executor = create_pipeline(config={
            'cleaning': {...},
            'feature_engineering': {...},
            'processing': {...}
        })
        
        # Auto from data
        executor = create_pipeline(auto_from_data=True, df=my_dataframe)
    """
    builder = PipelineBuilder(config)
    
    if auto_from_data:
        if df is None:
            raise ValueError("df required when auto_from_data=True")
        builder.build_from_auto(df)
    else:
        builder.build()
    
    return PipelineExecutor(builder)


def analyze_data(df) -> dict:
    """
    Convenience function to analyze a DataFrame
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Analysis results with recommendations
    
    Example:
        analysis = analyze_data(my_dataframe)
        print(analysis['recommendations'])
        print(analysis['auto_config_generated'])
    """
    analyzer = DataAnalyzer(df)
    return analyzer.analyze()
