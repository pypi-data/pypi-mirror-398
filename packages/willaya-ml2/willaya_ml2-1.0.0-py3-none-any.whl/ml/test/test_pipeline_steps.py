"""
Test Pipeline Step Management
Tests adding, viewing, removing, and managing pipeline steps
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime

from ml import preprocessing
from ml.preprocessing import (
    PipelineBuilder, PipelineExecutor,
    MissingValueHandler, OutlierHandler, DuplicateHandler,
    CategoricalEncoder, NumericalScaler,
    FormulaEngine, DateEngineer
)


def generate_test_data(n_samples=100):
    """Generate sample data for testing"""
    np.random.seed(42)

    data = {
        'age': np.random.randint(18, 80, n_samples),
        'income': np.random.exponential(50000, n_samples),
        'score': np.random.normal(700, 50, n_samples),
        'category': np.random.choice(['A', 'B', 'C', 'D'], n_samples),
        'city': np.random.choice(['NYC', 'LA', 'CHI'], n_samples),
        'value_with_missing': np.random.choice([1.0, 2.0, 3.0, np.nan], n_samples, p=[0.3, 0.3, 0.3, 0.1])
    }

    return pd.DataFrame(data)


def test_view_pipeline_steps():
    """Test viewing pipeline steps"""
    print("\n" + "="*80)
    print("TEST: VIEW PIPELINE STEPS")
    print("="*80)

    # Create a manual pipeline
    config = {
        'cleaning': {
            'missing_values': {
                'manual_config': {
                    'strategy': 'median'
                }
            },
            'duplicates': {
                'manual_config': {
                    'action': 'drop'
                }
            }
        },
        'processing': {
            'categorical_encoding': {
                'manual_config': {
                    'default_strategy': 'onehot'
                }
            },
            'numerical_scaling': {
                'manual_config': {
                    'default_strategy': 'standard'
                }
            }
        }
    }

    print("\n1. Building pipeline from config...")
    builder = PipelineBuilder(config)
    builder.build()

    # Get pipeline steps
    steps = builder.get_pipeline_steps()
    print(f"   [OK] Pipeline has {len(steps)} steps")

    # Display each step
    print("\n2. Pipeline steps:")
    for i, step in enumerate(steps, 1):
        print(f"   Step {i}: {step['name']} (stage: {step['stage']})")
        print(f"           Component: {step['component'].__class__.__name__}")

    # Get pipeline info
    info = builder.get_pipeline_info()
    print(f"\n3. Pipeline info:")
    print(f"   Is built: {info['is_built']}")
    print(f"   Total steps: {info['total_steps']}")
    print(f"   Stages:")
    for stage, stage_steps in info['stages'].items():
        if stage_steps:
            print(f"      {stage}: {len(stage_steps)} steps")
            for s in stage_steps:
                print(f"         - {s['name']} ({s['component_type']})")

    print("\n[PASS] View pipeline steps test completed!")
    return True


def test_add_custom_steps():
    """Test adding custom steps to pipeline"""
    print("\n" + "="*80)
    print("TEST: ADD CUSTOM STEPS")
    print("="*80)

    print("\n1. Creating base pipeline...")
    config = {
        'cleaning': {
            'missing_values': {
                'manual_config': {
                    'strategy': 'median'
                }
            }
        }
    }

    builder = PipelineBuilder(config)
    builder.build()

    initial_steps = len(builder.get_pipeline_steps())
    print(f"   [OK] Initial pipeline has {initial_steps} steps")

    print("\n2. Adding custom outlier handler...")
    outlier_handler = OutlierHandler({
        'method': 'iqr',
        'action': 'cap',
        'threshold': 1.5
    })
    builder.add_step(
        name='custom_outlier_handler',
        stage='cleaning',
        component=outlier_handler,
        position=1  # Add after missing values
    )

    steps_after_add = len(builder.get_pipeline_steps())
    print(f"   [OK] Pipeline now has {steps_after_add} steps")

    print("\n3. Adding categorical encoder at end...")
    cat_encoder = CategoricalEncoder({
        'default_strategy': 'label',
        'handle_unknown': 'ignore'
    })
    builder.add_step(
        name='label_encoding',
        stage='processing',
        component=cat_encoder
    )

    final_steps = len(builder.get_pipeline_steps())
    print(f"   [OK] Pipeline now has {final_steps} steps")

    # Verify steps
    print("\n4. Final pipeline steps:")
    for i, step in enumerate(builder.get_pipeline_steps(), 1):
        print(f"   {i}. {step['name']} ({step['stage']})")

    assert final_steps == initial_steps + 2, "Should have 2 more steps"
    print("\n[PASS] Add custom steps test completed!")
    return True


def test_remove_steps():
    """Test removing steps from pipeline"""
    print("\n" + "="*80)
    print("TEST: REMOVE STEPS")
    print("="*80)

    print("\n1. Creating pipeline with multiple steps...")
    config = {
        'cleaning': {
            'missing_values': {
                'manual_config': {
                    'strategy': 'median'
                }
            },
            'duplicates': {
                'manual_config': {
                    'action': 'drop'
                }
            },
            'outliers': {
                'manual_config': {
                    'method': 'iqr',
                    'action': 'cap'
                }
            }
        },
        'processing': {
            'categorical_encoding': {
                'manual_config': {
                    'default_strategy': 'onehot'
                }
            },
            'numerical_scaling': {
                'manual_config': {
                    'default_strategy': 'standard'
                }
            }
        }
    }

    builder = PipelineBuilder(config)
    builder.build()

    initial_steps = len(builder.get_pipeline_steps())
    print(f"   [OK] Initial pipeline has {initial_steps} steps")

    print("\n2. Removing 'duplicates' step...")
    builder.remove_step('duplicates')

    steps_after_remove = len(builder.get_pipeline_steps())
    print(f"   [OK] Pipeline now has {steps_after_remove} steps")

    # Verify the step was removed
    remaining_names = [s['name'] for s in builder.get_pipeline_steps()]
    assert 'duplicates' not in remaining_names, "Duplicates step should be removed"

    print("\n3. Removing 'numerical_scaling' step...")
    builder.remove_step('numerical_scaling')

    final_steps = len(builder.get_pipeline_steps())
    print(f"   [OK] Pipeline now has {final_steps} steps")

    print("\n4. Remaining steps:")
    for i, step in enumerate(builder.get_pipeline_steps(), 1):
        print(f"   {i}. {step['name']}")

    assert final_steps == initial_steps - 2, "Should have 2 fewer steps"
    print("\n[PASS] Remove steps test completed!")
    return True


def test_get_specific_step():
    """Test getting a specific step from pipeline"""
    print("\n" + "="*80)
    print("TEST: GET SPECIFIC STEP")
    print("="*80)

    config = {
        'cleaning': {
            'missing_values': {
                'manual_config': {
                    'strategy': 'mean'
                }
            }
        },
        'processing': {
            'categorical_encoding': {
                'manual_config': {
                    'default_strategy': 'onehot'
                }
            }
        }
    }

    print("\n1. Building pipeline...")
    builder = PipelineBuilder(config)
    builder.build()

    print("\n2. Getting 'missing_values' step...")
    mv_step = builder.get_step('missing_values')

    if mv_step:
        print(f"   [OK] Found step: {mv_step['name']}")
        print(f"   [OK] Stage: {mv_step['stage']}")
        print(f"   [OK] Component type: {mv_step['component'].__class__.__name__}")
    else:
        print("   [FAIL] Step not found")
        return False

    print("\n3. Getting 'categorical_encoding' step...")
    ce_step = builder.get_step('categorical_encoding')

    if ce_step:
        print(f"   [OK] Found step: {ce_step['name']}")
        print(f"   [OK] Component type: {ce_step['component'].__class__.__name__}")
    else:
        print("   [FAIL] Step not found")
        return False

    print("\n4. Trying to get non-existent step...")
    fake_step = builder.get_step('non_existent_step')
    if fake_step is None:
        print("   [OK] Correctly returned None for non-existent step")
    else:
        print("   [FAIL] Should return None for non-existent step")
        return False

    print("\n[PASS] Get specific step test completed!")
    return True


def test_pipeline_execution_with_steps():
    """Test executing pipeline and viewing execution details"""
    print("\n" + "="*80)
    print("TEST: PIPELINE EXECUTION WITH STEPS")
    print("="*80)

    # Generate test data
    df = generate_test_data(200)
    print(f"\n1. Generated test data: {df.shape}")

    # Create pipeline
    config = {
        'cleaning': {
            'missing_values': {
                'manual_config': {
                    'strategy': 'median'
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

    print("\n2. Building and executing pipeline...")
    builder = PipelineBuilder(config)
    builder.build()

    executor = PipelineExecutor(builder)
    transformed_df = executor.fit_transform(df)

    print(f"   [OK] Input shape: {df.shape}")
    print(f"   [OK] Output shape: {transformed_df.shape}")

    # Get fit report
    print("\n3. Fit report:")
    fit_report = executor.get_fit_report()

    print(f"   Input shape: {fit_report['input_shape']}")
    print(f"   Output shape: {fit_report['output_shape']}")
    print(f"   Steps executed: {len(fit_report['steps'])}")

    print("\n4. Step-by-step execution details:")
    for step_report in fit_report['steps']:
        print(f"   Step: {step_report['name']}")
        print(f"      Stage: {step_report['stage']}")
        print(f"      Input shape: {step_report['input_shape']}")
        print(f"      Output shape: {step_report['output_shape']}")
        print(f"      Status: {step_report['status']}")
        if 'fit_stats' in step_report and step_report['fit_stats']:
            print(f"      Fit stats keys: {list(step_report['fit_stats'].keys())}")

    # Get feature names
    print("\n5. Feature transformation:")
    features_in, features_out = executor.get_feature_names()
    print(f"   Features in: {features_in}")
    print(f"   Features out (first 10): {features_out[:10]}")

    print("\n[PASS] Pipeline execution with steps test completed!")
    return True


def test_auto_pipeline_with_fixes():
    """Test auto pipeline with type conversion fixes"""
    print("\n" + "="*80)
    print("TEST: AUTO PIPELINE (WITH FIXES)")
    print("="*80)

    # Generate test data with various types
    df = generate_test_data(150)
    print(f"\n1. Generated test data: {df.shape}")
    print(f"   Columns: {df.columns.tolist()}")

    try:
        print("\n2. Creating auto pipeline...")
        pipeline = preprocessing.create_pipeline(auto_from_data=True, df=df)

        print("   [OK] Pipeline created")

        print("\n3. Fitting and transforming...")
        transformed_df = pipeline.fit_transform(df, verbose=False)

        print(f"   [OK] Transformation successful!")
        print(f"   [OK] Input shape: {df.shape}")
        print(f"   [OK] Output shape: {transformed_df.shape}")

        # Get pipeline info
        builder = pipeline.builder
        info = builder.get_pipeline_info()

        print(f"\n4. Auto pipeline info:")
        print(f"   Total steps: {info['total_steps']}")
        for stage, stage_steps in info['stages'].items():
            if stage_steps:
                print(f"   {stage}: {len(stage_steps)} steps")
                for s in stage_steps:
                    print(f"      - {s['name']}")

        print("\n[PASS] Auto pipeline test completed successfully!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Auto pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all pipeline step tests"""
    print("\n" + "="*80)
    print("PIPELINE STEP MANAGEMENT TEST SUITE")
    print("="*80)
    print(f"Start time: {datetime.now()}")

    results = []

    try:
        # Run tests
        results.append(("View Pipeline Steps", test_view_pipeline_steps()))
        results.append(("Add Custom Steps", test_add_custom_steps()))
        results.append(("Remove Steps", test_remove_steps()))
        results.append(("Get Specific Step", test_get_specific_step()))
        results.append(("Pipeline Execution", test_pipeline_execution_with_steps()))
        results.append(("Auto Pipeline with Fixes", test_auto_pipeline_with_fixes()))

        # Summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status} {test_name}")

        print("\n" + "="*80)
        if passed == total:
            print(f"ALL TESTS PASSED! ({passed}/{total})")
            print("="*80)
            print("\nPipeline step management is working correctly!")
            print("\nFeatures tested:")
            print("  [OK] Viewing pipeline steps")
            print("  [OK] Adding custom steps")
            print("  [OK] Removing steps")
            print("  [OK] Getting specific steps")
            print("  [OK] Pipeline execution and reporting")
            print("  [OK] Auto pipeline with type conversion fixes")
            return 0
        else:
            print(f"SOME TESTS FAILED ({passed}/{total} passed)")
            print("="*80)
            return 1

    except Exception as e:
        print(f"\n[FAIL] Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
