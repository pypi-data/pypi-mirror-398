"""
Quick Import Test for ML Package
Tests that all modules can be imported correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that all ML package components can be imported"""

    print("Testing ML Package Imports...\n")

    errors = []

    # Test main ML module
    try:
        import ml
        print("[OK] ml module imported")
    except Exception as e:
        error_msg = f"[FAIL] Failed to import ml: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Test ModelFactory
    try:
        from ml import ModelFactory, get_supported_algorithms
        print("[OK] ModelFactory imported")
    except Exception as e:
        error_msg = f"[FAIL] Failed to import ModelFactory: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Test Trainer
    try:
        from ml import ModelTrainer
        print("[OK] ModelTrainer imported")
    except Exception as e:
        error_msg = f"[FAIL] Failed to import ModelTrainer: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Test Evaluator
    try:
        from ml import ModelEvaluator
        print("[OK] ModelEvaluator imported")
    except Exception as e:
        error_msg = f"[FAIL] Failed to import ModelEvaluator: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Test preprocessing
    try:
        from ml import preprocessing
        print("[OK] preprocessing module imported")
    except Exception as e:
        error_msg = f"[FAIL] Failed to import preprocessing: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Test preprocessing components
    try:
        from ml.preprocessing import (
            DataAnalyzer, StatsCalculator, RecommendationEngine,
            MissingValueHandler, OutlierHandler, DuplicateHandler, TypeConverter,
            FormulaEngine, DateEngineer, Aggregator,
            CategoricalEncoder, NumericalScaler, FeatureSelector,
            PipelineBuilder, PipelineExecutor, PipelineRegistry
        )
        print("[OK] All preprocessing components imported")
    except Exception as e:
        error_msg = f"[FAIL] Failed to import preprocessing components: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Test algorithms
    try:
        from ml.algorithms import (
            BaseMLModel,
            XGBoostClassifier, XGBoostRegressor,
            LightGBMClassifier, LightGBMRegressor,
            CatBoostClassifier, CatBoostRegressor,
            RandomForestClassifier, RandomForestRegressor,
            LogisticRegressionClassifier, LinearRegressionModel,
            SVMClassifier, SVMRegressor
        )
        print("[OK] All algorithm models imported")
    except Exception as e:
        error_msg = f"[FAIL] Failed to import algorithms: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Summary
    print("\n" + "="*60)
    if not errors:
        print("ALL IMPORTS SUCCESSFUL! [PASS]")
        print("="*60)
        print("\nThe ML package structure is correct.")
        print("You can now run the comprehensive tests with:")
        print("  python ml/test/test_ml_package.py")
        return 0
    else:
        print(f"IMPORT TESTS FAILED ({len(errors)} errors) [FAIL]")
        print("="*60)
        print("\nErrors encountered:")
        for error in errors:
            print(f"  {error}")
        print("\nPlease install required dependencies:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    exit(test_imports())
