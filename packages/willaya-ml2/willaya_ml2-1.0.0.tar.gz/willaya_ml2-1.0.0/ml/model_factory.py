"""
Model Factory
Creates ML models based on algorithm name and task type
"""
from typing import Dict, Any, Optional, Type, List
from enum import Enum

from .algorithms import (
    BaseMLModel,
    XGBoostClassifier, XGBoostRegressor,
    LightGBMClassifier, LightGBMRegressor,
    CatBoostClassifier, CatBoostRegressor,
    RandomForestClassifier, RandomForestRegressor,
    LogisticRegressionClassifier, LinearRegressionModel,
    SVMClassifier, SVMRegressor
)


class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class AlgorithmType(str, Enum):
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    RANDOM_FOREST = "random_forest"
    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR_REGRESSION = "linear_regression"
    SVM = "svm"


# Model registry - maps (algorithm, task) to model class
MODEL_REGISTRY: Dict[tuple, Type[BaseMLModel]] = {
    # XGBoost
    (AlgorithmType.XGBOOST, TaskType.CLASSIFICATION): XGBoostClassifier,
    (AlgorithmType.XGBOOST, TaskType.REGRESSION): XGBoostRegressor,
    
    # LightGBM
    (AlgorithmType.LIGHTGBM, TaskType.CLASSIFICATION): LightGBMClassifier,
    (AlgorithmType.LIGHTGBM, TaskType.REGRESSION): LightGBMRegressor,
    
    # CatBoost
    (AlgorithmType.CATBOOST, TaskType.CLASSIFICATION): CatBoostClassifier,
    (AlgorithmType.CATBOOST, TaskType.REGRESSION): CatBoostRegressor,
    
    # Random Forest
    (AlgorithmType.RANDOM_FOREST, TaskType.CLASSIFICATION): RandomForestClassifier,
    (AlgorithmType.RANDOM_FOREST, TaskType.REGRESSION): RandomForestRegressor,
    
    # Logistic Regression (classification only)
    (AlgorithmType.LOGISTIC_REGRESSION, TaskType.CLASSIFICATION): LogisticRegressionClassifier,
    
    # Linear Regression (regression only)
    (AlgorithmType.LINEAR_REGRESSION, TaskType.REGRESSION): LinearRegressionModel,
    
    # SVM
    (AlgorithmType.SVM, TaskType.CLASSIFICATION): SVMClassifier,
    (AlgorithmType.SVM, TaskType.REGRESSION): SVMRegressor,
}


# Convenience function - standalone
def get_supported_algorithms(task_type: Optional[str] = None) -> List[str]:
    """
    Get list of supported algorithms
    
    Args:
        task_type: Filter by task type (optional) - 'classification' or 'regression'
    
    Returns:
        List of supported algorithm names
    """
    if task_type:
        try:
            task_enum = TaskType(task_type.lower())
            return list(set(
                algo.value for algo, task in MODEL_REGISTRY.keys()
                if task == task_enum
            ))
        except ValueError:
            return []
    return list(set(algo.value for algo, _ in MODEL_REGISTRY.keys()))


class ModelFactory:
    """
    Factory class for creating ML models
    Supports dynamic model creation based on algorithm and task type
    """
    
    @staticmethod
    def get_available_algorithms(task_type: Optional[TaskType] = None) -> list:
        """
        Get list of available algorithms
        
        Args:
            task_type: Filter by task type (optional)
        
        Returns:
            List of available algorithm names
        """
        if task_type:
            return [
                algo.value for algo, task in MODEL_REGISTRY.keys()
                if task == task_type
            ]
        return list(set(algo.value for algo, _ in MODEL_REGISTRY.keys()))
    
    @staticmethod
    def get_supported_algorithms(task_type: Optional[str] = None) -> List[str]:
        """Alias for get_available_algorithms with string input"""
        return get_supported_algorithms(task_type)
    
    @staticmethod
    def create_model(
        algorithm: str,
        task_type: str,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> BaseMLModel:
        """
        Create a model instance
        
        Args:
            algorithm: Algorithm name (e.g., 'xgboost', 'lightgbm')
            task_type: Task type ('classification' or 'regression')
            hyperparameters: Optional hyperparameters dict
        
        Returns:
            Model instance
        
        Raises:
            ValueError: If algorithm or task type is not supported
        """
        try:
            algo_enum = AlgorithmType(algorithm.lower())
            task_enum = TaskType(task_type.lower())
        except ValueError as e:
            raise ValueError(f"Invalid algorithm or task type: {e}")
        
        key = (algo_enum, task_enum)
        
        if key not in MODEL_REGISTRY:
            raise ValueError(
                f"Combination of algorithm '{algorithm}' and task type '{task_type}' "
                f"is not supported. Available: {list(MODEL_REGISTRY.keys())}"
            )
        
        model_class = MODEL_REGISTRY[key]
        return model_class(hyperparameters=hyperparameters or {})
    
    @staticmethod
    def get_default_hyperparameters(algorithm: str, task_type: str) -> Dict[str, Any]:
        """
        Get default hyperparameters for an algorithm
        
        Args:
            algorithm: Algorithm name
            task_type: Task type
        
        Returns:
            Default hyperparameters dict
        """
        model = ModelFactory.create_model(algorithm, task_type)
        return model.default_params if hasattr(model, 'default_params') else {}
    
    @staticmethod
    def validate_hyperparameters(
        algorithm: str,
        task_type: str,
        hyperparameters: Dict[str, Any]
    ) -> tuple:
        """
        Validate hyperparameters for an algorithm
        
        Args:
            algorithm: Algorithm name
            task_type: Task type
            hyperparameters: Hyperparameters to validate
        
        Returns:
            Tuple of (is_valid, errors list)
        """
        try:
            # Try to create model with the hyperparameters
            ModelFactory.create_model(algorithm, task_type, hyperparameters)
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    @staticmethod
    def supports_proba(algorithm: str, task_type: str) -> bool:
        """Check if model supports probability predictions"""
        if task_type.lower() == 'regression':
            return False
        
        # All classification models support proba
        return True
    
    @staticmethod
    def get_model_info(algorithm: str, task_type: str) -> Dict[str, Any]:
        """
        Get information about a model
        
        Returns:
            Dict with model info
        """
        model = ModelFactory.create_model(algorithm, task_type)
        return {
            'algorithm': algorithm,
            'task_type': task_type,
            'model_type': model.model_type,
            'supports_proba': ModelFactory.supports_proba(algorithm, task_type),
            'default_hyperparameters': ModelFactory.get_default_hyperparameters(algorithm, task_type)
        }


# Convenience function
def create_model(
    algorithm: str,
    task_type: str,
    hyperparameters: Optional[Dict[str, Any]] = None
) -> BaseMLModel:
    """Shortcut function for creating models"""
    return ModelFactory.create_model(algorithm, task_type, hyperparameters)
