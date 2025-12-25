"""
ML Module
Machine Learning components for the Willaya Project

Includes:
    - Model Factory: Create and manage ML models
    - Preprocessing: Data preparation pipeline
    - Trainer: Model training with hyperparameter tuning
    - Evaluator: Model evaluation and metrics
"""

from .model_factory import ModelFactory, get_supported_algorithms
from .trainer import ModelTrainer
from .evaluator import ModelEvaluator

# Preprocessing submodule
from . import preprocessing

__all__ = [
    "ModelFactory",
    "get_supported_algorithms",
    "ModelTrainer",
    "ModelEvaluator",
    "preprocessing"
]
