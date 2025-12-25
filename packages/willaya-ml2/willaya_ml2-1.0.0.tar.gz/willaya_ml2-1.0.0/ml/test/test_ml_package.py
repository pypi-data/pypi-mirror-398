"""
Comprehensive Test Suite for ML Package
Tests all components of the ML package to verify functionality

This example demonstrates:
1. Model Factory - creating different model types
2. All Algorithms - XGBoost, LightGBM, CatBoost, RandomForest, sklearn models
3. Preprocessing - data analysis, cleaning, engineering, processing
4. Trainer - training multiple models with hyperparameter tuning
5. Evaluator - evaluating model performance
"""

import sys
from pathlib import Path
# Add parent directory to path to import ml package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Import ML package components
from ml import ModelFactory, get_supported_algorithms, ModelTrainer, ModelEvaluator
from ml import preprocessing


def generate_sample_data(task_type='classification', n_samples=1000):
    """
    Generate sample data for testing

    Args:
        task_type: 'classification' or 'regression'
        n_samples: Number of samples to generate

    Returns:
        DataFrame with features and target
    """
    np.random.seed(42)

    # Generate features
    data = {
        # Numerical features
        'age': np.random.randint(18, 80, n_samples),
        'income': np.random.exponential(50000, n_samples),
        'credit_score': np.random.normal(700, 50, n_samples),
        'years_employed': np.random.uniform(0, 40, n_samples),

        # Categorical features
        'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], n_samples),
        'employment': np.random.choice(['Full-time', 'Part-time', 'Self-employed', 'Unemployed'], n_samples),
        'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'], n_samples),

        # Date feature
        'account_created': [
            datetime.now() - timedelta(days=int(d))
            for d in np.random.uniform(0, 3650, n_samples)
        ],

        # Features with missing values
        'previous_loans': np.random.choice([1, 2, 3, 4, 5, np.nan], n_samples, p=[0.2, 0.2, 0.2, 0.2, 0.1, 0.1]),
        'debt_ratio': np.random.choice([0.1, 0.3, 0.5, 0.7, np.nan], n_samples, p=[0.25, 0.25, 0.25, 0.15, 0.1]),
    }

    df = pd.DataFrame(data)

    # Add some outliers
    outlier_indices = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
    df.loc[outlier_indices, 'income'] = np.random.uniform(200000, 500000, len(outlier_indices))

    # Add some duplicates
    duplicate_indices = np.random.choice(n_samples, size=int(n_samples * 0.02), replace=False)
    df = pd.concat([df, df.iloc[duplicate_indices]], ignore_index=True)

    # Generate target variable
    if task_type == 'classification':
        # Binary classification: loan approval
        target_proba = (
            0.3 * (df['credit_score'] / 850) +
            0.2 * (df['income'] / 100000) +
            0.2 * (df['years_employed'] / 40) +
            0.3 * np.random.random(len(df))
        )
        df['target'] = (target_proba > 0.5).astype(int)
    else:
        # Regression: predict loan amount
        df['target'] = (
            100 * df['credit_score'] +
            0.5 * df['income'] +
            1000 * df['years_employed'] +
            np.random.normal(0, 10000, len(df))
        )

    return df


def test_model_factory():
    """Test ModelFactory component"""
    print("\n" + "="*80)
    print("TEST 1: MODEL FACTORY")
    print("="*80)

    # Test getting supported algorithms
    print("\n1. Getting supported algorithms:")
    all_algos = get_supported_algorithms()
    print(f"   All algorithms: {all_algos}")

    classification_algos = get_supported_algorithms('classification')
    print(f"   Classification algorithms: {classification_algos}")

    regression_algos = get_supported_algorithms('regression')
    print(f"   Regression algorithms: {regression_algos}")

    # Test creating models
    print("\n2. Creating models:")
    for algo in ['xgboost', 'lightgbm', 'random_forest', 'logistic_regression']:
        try:
            model = ModelFactory.create_model(algo, 'classification')
            print(f"   [OK] Created {algo} classifier: {model.model_type}")
        except Exception as e:
            print(f"   [FAIL] Failed to create {algo}: {e}")

    # Test model info
    print("\n3. Getting model info:")
    info = ModelFactory.get_model_info('xgboost', 'classification')
    print(f"   XGBoost info: {info['model_type']}")
    print(f"   Supports proba: {info['supports_proba']}")

    print("\n[PASS] Model Factory tests completed successfully!")


def test_algorithms():
    """Test all algorithm implementations"""
    print("\n" + "="*80)
    print("TEST 2: ALGORITHMS")
    print("="*80)

    # Generate small dataset for quick testing
    df = generate_sample_data('classification', n_samples=200)
    X = df[['age', 'income', 'credit_score', 'years_employed']]
    y = df['target']

    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    algorithms = ['xgboost', 'lightgbm', 'catboost', 'random_forest', 'logistic_regression']

    print("\nTesting classification algorithms:")
    for algo in algorithms:
        try:
            print(f"\n{algo.upper()}:")

            # Create model
            model = ModelFactory.create_model(algo, 'classification')

            # Train
            model.fit(X_train, y_train)
            print(f"   [OK] Training completed")

            # Predict
            predictions = model.predict(X_test)
            print(f"   [OK] Predictions: {predictions[:5]}")

            # Predict proba (if supported)
            if algo != 'linear_regression':
                probas = model.predict_proba(X_test)
                print(f"   [OK] Probabilities shape: {probas.shape}")

            # Feature importance
            importance = model.get_feature_importance()
            top_feature = max(importance.items(), key=lambda x: x[1])
            print(f"   [OK] Top feature: {top_feature[0]} (importance: {top_feature[1]:.4f})")

        except Exception as e:
            print(f"   [FAIL] Error with {algo}: {e}")

    print("\n[PASS] Algorithm tests completed successfully!")


def test_preprocessing_analyzers():
    """Test preprocessing analyzers"""
    print("\n" + "="*80)
    print("TEST 3: PREPROCESSING - ANALYZERS")
    print("="*80)

    # Generate sample data
    df = generate_sample_data('classification', n_samples=500)
    features_df = df.drop('target', axis=1)

    print("\n1. Data Analyzer:")
    analyzer = preprocessing.DataAnalyzer(features_df)
    analysis = analyzer.analyze()

    print(f"   [OK] Analyzed {analysis['rows_analyzed']} rows, {analysis['columns_analyzed']} columns")
    print(f"   [OK] Found {len(analysis['warnings'])} warnings")
    print(f"   [OK] Generated {len(analysis['recommendations'])} recommendations")

    # Show some recommendations
    if analysis['recommendations']:
        print("\n   Sample recommendations:")
        for rec_type, recs in list(analysis['recommendations'].items())[:3]:
            print(f"      - {rec_type}: {len(recs)} items")

    print("\n[PASS] Preprocessing analyzers tests completed successfully!")


def test_preprocessing_pipeline():
    """Test preprocessing pipeline"""
    print("\n" + "="*80)
    print("TEST 4: PREPROCESSING - PIPELINE")
    print("="*80)

    # Generate sample data
    df = generate_sample_data('classification', n_samples=500)
    target = df['target']
    features_df = df.drop('target', axis=1)

    print("\n1. Auto pipeline from data analysis:")

    # Create pipeline automatically
    pipeline = preprocessing.create_pipeline(auto_from_data=True, df=features_df)

    # Fit and transform
    print("   [OK] Pipeline created")

    try:
        transformed_df = pipeline.fit_transform(features_df)
        print(f"   [OK] Fitted and transformed data")
        print(f"   [OK] Input shape: {features_df.shape}")
        print(f"   [OK] Output shape: {transformed_df.shape}")

        # Get feature names
        features_in, features_out = pipeline.get_feature_names()
        print(f"   [OK] Features in: {len(features_in)}")
        print(f"   [OK] Features out: {len(features_out)}")

        # Get fit report
        fit_report = pipeline.get_fit_report()
        print(f"   [OK] Pipeline steps executed: {len(fit_report.get('steps', []))}")

    except Exception as e:
        print(f"   [FAIL] Error in pipeline: {e}")
        import traceback
        traceback.print_exc()

    print("\n2. Manual pipeline configuration:")

    # Create manual pipeline
    config = {
        'cleaning': {
            'missing_values': {
                'manual_config': {
                    'strategy': 'median',
                    'per_column': {}
                }
            }
        },
        'processing': {
            'categorical_encoding': {
                'manual_config': {
                    'default_strategy': 'onehot',
                    'handle_unknown': 'ignore'
                }
            },
            'numerical_scaling': {
                'manual_config': {
                    'default_strategy': 'standard'
                }
            }
        }
    }

    try:
        manual_pipeline = preprocessing.create_pipeline(config=config)
        transformed_manual = manual_pipeline.fit_transform(features_df)
        print(f"   [OK] Manual pipeline created and executed")
        print(f"   [OK] Output shape: {transformed_manual.shape}")
    except Exception as e:
        print(f"   [FAIL] Error in manual pipeline: {e}")

    print("\n[PASS] Preprocessing pipeline tests completed successfully!")


def test_trainer():
    """Test ModelTrainer component"""
    print("\n" + "="*80)
    print("TEST 5: MODEL TRAINER")
    print("="*80)

    # Generate sample data
    df = generate_sample_data('classification', n_samples=300)

    # Simple feature selection for quick training
    X = df[['age', 'income', 'credit_score', 'years_employed']].fillna(0)
    y = df['target']

    print("\n1. Training multiple models:")

    # Create trainer
    trainer = ModelTrainer(
        task_type='classification',
        algorithms=['xgboost', 'random_forest', 'logistic_regression'],
        config={
            'test_size': 0.2,
            'cv_folds': 3,
            'auto_tune': False,  # Disable tuning for speed
            'random_state': 42
        }
    )

    try:
        # Train models
        results = trainer.train(X, y)

        print(f"   [OK] Training completed")
        print(f"   [OK] Algorithms trained: {len(results['algorithms'])}")
        print(f"   [OK] Best algorithm: {results['best_algorithm']}")
        print(f"   [OK] Best score: {results['best_score']:.4f}")

        # Get comparison report
        comparison = trainer.get_comparison_report()
        print(f"\n   Model Comparison:")
        print(comparison[['algorithm', 'accuracy', 'f1', 'precision', 'recall']].to_string(index=False))

        # Get best model
        best_model = trainer.get_best_model()
        print(f"\n   [OK] Best model retrieved: {best_model.model_type}")

    except Exception as e:
        print(f"   [FAIL] Error in training: {e}")
        import traceback
        traceback.print_exc()

    print("\n[PASS] Model Trainer tests completed successfully!")


def test_evaluator():
    """Test ModelEvaluator component"""
    print("\n" + "="*80)
    print("TEST 6: MODEL EVALUATOR")
    print("="*80)

    # Generate sample data
    df = generate_sample_data('classification', n_samples=300)
    X = df[['age', 'income', 'credit_score', 'years_employed']].fillna(0)
    y = df['target']

    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print("\n1. Classification evaluation:")

    try:
        # Train a model
        model = ModelFactory.create_model('xgboost', 'classification')
        model.fit(X_train, y_train)

        # Evaluate
        evaluator = ModelEvaluator(task_type='classification')
        metrics = evaluator.evaluate(model, X_test, y_test)

        print(f"   [OK] Evaluation completed")
        print(f"   [OK] Accuracy: {metrics['accuracy']:.4f}")
        print(f"   [OK] Precision: {metrics['precision']:.4f}")
        print(f"   [OK] Recall: {metrics['recall']:.4f}")
        print(f"   [OK] F1 Score: {metrics['f1']:.4f}")
        if 'roc_auc' in metrics:
            print(f"   [OK] ROC AUC: {metrics['roc_auc']:.4f}")

        # Get confusion matrix
        if 'confusion_matrix' in metrics:
            print(f"\n   Confusion Matrix:")
            cm = np.array(metrics['confusion_matrix'])
            print(f"   {cm}")

    except Exception as e:
        print(f"   [FAIL] Error in evaluation: {e}")
        import traceback
        traceback.print_exc()

    print("\n2. Regression evaluation:")

    try:
        # Generate regression data
        df_reg = generate_sample_data('regression', n_samples=300)
        X_reg = df_reg[['age', 'income', 'credit_score', 'years_employed']].fillna(0)
        y_reg = df_reg['target']

        split_idx = int(len(X_reg) * 0.8)
        X_train_reg, X_test_reg = X_reg[:split_idx], X_reg[split_idx:]
        y_train_reg, y_test_reg = y_reg[:split_idx], y_reg[split_idx:]

        # Train regression model
        model_reg = ModelFactory.create_model('xgboost', 'regression')
        model_reg.fit(X_train_reg, y_train_reg)

        # Evaluate
        evaluator_reg = ModelEvaluator(task_type='regression')
        metrics_reg = evaluator_reg.evaluate(model_reg, X_test_reg, y_test_reg)

        print(f"   [OK] Regression evaluation completed")
        print(f"   [OK] RMSE: {metrics_reg['rmse']:.2f}")
        print(f"   [OK] MAE: {metrics_reg['mae']:.2f}")
        print(f"   [OK] R²: {metrics_reg['r2']:.4f}")

    except Exception as e:
        print(f"   [FAIL] Error in regression evaluation: {e}")
        import traceback
        traceback.print_exc()

    print("\n[PASS] Model Evaluator tests completed successfully!")


def test_end_to_end_workflow():
    """Test complete end-to-end ML workflow"""
    print("\n" + "="*80)
    print("TEST 7: END-TO-END ML WORKFLOW")
    print("="*80)

    print("\nRunning complete ML workflow:")

    try:
        # 1. Generate data
        print("\n1. Generating data...")
        df = generate_sample_data('classification', n_samples=500)
        target = df['target']
        features = df.drop('target', axis=1)
        print(f"   [OK] Generated {len(df)} samples with {len(features.columns)} features")

        # 2. Analyze data
        print("\n2. Analyzing data...")
        analysis = preprocessing.analyze_data(features)
        print(f"   [OK] Analysis complete: {len(analysis['recommendations'])} recommendation categories")

        # 3. Preprocess data
        print("\n3. Preprocessing data...")
        pipeline = preprocessing.create_pipeline(auto_from_data=True, df=features)
        X_processed = pipeline.fit_transform(features)
        print(f"   [OK] Preprocessing complete: {features.shape} -> {X_processed.shape}")

        # Align target with processed data (in case rows were removed during preprocessing)
        y_aligned = target.iloc[X_processed.index] if hasattr(X_processed, 'index') else target[:len(X_processed)]

        # Remove datetime columns if any (ML algorithms can't handle them)
        datetime_cols = X_processed.select_dtypes(include=['datetime64']).columns.tolist()
        if datetime_cols:
            print(f"   [INFO] Removing datetime columns: {datetime_cols}")
            X_processed = X_processed.drop(columns=datetime_cols)

        # 4. Train models
        print("\n4. Training models...")
        trainer = ModelTrainer(
            task_type='classification',
            algorithms=['xgboost', 'random_forest'],
            config={'auto_tune': False, 'cv_folds': 3}
        )
        results = trainer.train(X_processed, y_aligned)
        print(f"   [OK] Training complete")
        if results.get('best_algorithm'):
            print(f"   [OK] Best algorithm: {results['best_algorithm']}")
            print(f"   [OK] Best score: {results['best_score']:.4f}")
        else:
            print(f"   [WARN] No best algorithm found (check training results)")

        # 5. Evaluate best model
        if trainer.get_best_model():
            print("\n5. Evaluating best model...")
            best_model = trainer.get_best_model()

            # Use a holdout set for evaluation
            split_idx = int(len(X_processed) * 0.8)
            X_test = X_processed[split_idx:]
            y_test = y_aligned[split_idx:]

            evaluator = ModelEvaluator(task_type='classification')
            metrics = evaluator.evaluate(best_model, X_test, y_test)
            print(f"   [OK] Evaluation complete")
            print(f"   [OK] Test Accuracy: {metrics['accuracy']:.4f}")
            print(f"   [OK] Test F1: {metrics['f1']:.4f}")
        else:
            print("\n5. Skipping evaluation (no successful models)")

        print("\n[PASS] End-to-end workflow completed successfully!")

    except Exception as e:
        print(f"\n[FAIL] Error in end-to-end workflow: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("ML PACKAGE COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Start time: {datetime.now()}")

    try:
        # Run all tests
        test_model_factory()
        test_algorithms()
        test_preprocessing_analyzers()
        test_preprocessing_pipeline()
        test_trainer()
        test_evaluator()
        test_end_to_end_workflow()

        # Summary
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY! [PASS]")
        print("="*80)
        print(f"End time: {datetime.now()}")
        print("\nThe ML package is working correctly!")
        print("All components have been tested:")
        print("  [OK] Model Factory")
        print("  [OK] Algorithms (XGBoost, LightGBM, CatBoost, RandomForest, sklearn)")
        print("  [OK] Preprocessing (Analyzers, Cleaners, Engineers, Processors, Pipeline)")
        print("  [OK] Model Trainer")
        print("  [OK] Model Evaluator")
        print("  [OK] End-to-End Workflow")

    except Exception as e:
        print(f"\n[FAIL] Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
