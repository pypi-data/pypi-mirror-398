"""
Analyzers Module
Auto-detection of data properties and recommendation engine
"""
from .data_analyzer import DataAnalyzer
from .stats_calculator import StatsCalculator
from .recommendation import RecommendationEngine

__all__ = [
    "DataAnalyzer",
    "StatsCalculator", 
    "RecommendationEngine"
]
