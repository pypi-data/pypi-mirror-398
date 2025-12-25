"""
FTIR Pipeline Nested Cross-Validation Example

This example demonstrates the nested cross-validation functionality
for unbiased evaluation of FTIR preprocessing pipelines.

This example demonstrates how to use the framework to:
1. Load FTIR data
2. Apply nested cross-validation with automatic Optuna optimization 
3. Get unbiased evaluation scores with optimized pipelines per fold
4. Save detailed nested CV results

IMPORTANT: This example uses Nested CV which provides more robust and unbiased
evaluation compared to traditional optimization + evaluation approaches.

The nested CV process:
- Outer loop: Provides unbiased evaluation (10 folds)  
- Inner loop: Optimizes pipeline using Optuna (5 folds per outer fold)
- Includes: Truncation, baseline correction, normalization, smoothing, derivatives
- Result: True generalization performance estimate
"""

import os
from ftir_framework import (
    FTIRDataLoader,
    PipelineEvaluator,
    OptunaPipelineOptimizer
)


def main():

    print("=== FTIR Framework Nested Cross-Validation Example ===\n")
    print("=" * 60)
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        dataset_path = os.path.join(project_root, "dataset")
        
        print(f"Script directory: {script_dir}")
        print(f"Project root: {project_root}")
        print(f"Dataset path: {dataset_path}")
        
        # 1. Data loading
        print("\n1. Loading data...")
        data_loader = FTIRDataLoader(
            data_path=os.path.join(dataset_path, "absorbance.dat"),
            wavenumbers_path=os.path.join(dataset_path, "wavenumbers.dat")
        )
        
        X, y, wavenumbers = data_loader.load_data(slice_size = 3)
        print(f"   Data loaded: {X.shape[0]} samples, {X.shape[1]} features")

        groups = None  # To use StratifiedKFold without groups
        print(f"   Using StratifiedKFold without groups")
        
        print("2. Setting up evaluation and optimization...")
        print("   Note: Truncation is now integrated into the pipeline optimization process.")
        print("   The optimizer will automatically test different truncation methods:")
        print("   - 'fingerprint': Keeps only 900-1800 cm⁻¹ range")
        print("   - 'fingerprint_amide': Keeps 900-1800 and 2800-3050 cm⁻¹ ranges")
        
        # MAIN CHANGE: Use NestedCV evaluator instead of traditional CV
        evaluator = PipelineEvaluator(
            classifier=None,
            cv_method='NestedCV',  # ← Key change: Nested CV method
            cv_params={
                'outer_folds': 10,        # Outer CV for unbiased evaluation
                'inner_folds': 5,        # Inner CV for optimization
                'base_cv_method': 'StratifiedKFold',  # Base inner CV method
                'shuffle': False,        # Keep False for FTIR data
                'random_state': 42
            }
        )
        
        print(f"   Nested CV Configuration:")
        print(f"   - Outer folds (evaluation): {evaluator.cv_params['outer_folds']}")
        print(f"   - Inner folds (optimization): {evaluator.cv_params['inner_folds']}")
        print(f"   - Base CV method: {evaluator.cv_params['base_cv_method']}")
        
        optimizer = OptunaPipelineOptimizer(X, y, wavenumbers, groups,
                                            evaluator=evaluator,
                                            metric='f1_macro')
        
        print("4. Starting optimization process...")
        print("   Note: Nested CV detected - will execute nested cross-validation automatically.")
        print("   This provides unbiased evaluation but takes longer than traditional optimization.")
        print("\n   Available methods for optimization (same as traditional approach):")
        print(f"   - Truncation methods: {len(optimizer.available_methods['truncation'])}")
        print(f"   - Baseline methods: {len(optimizer.available_methods['baseline'])}")
        print(f"   - Normalization methods: {len(optimizer.available_methods['normalization'])}")
        print(f"   - Smoothing methods: {len(optimizer.available_methods['smoothing'])}")
        print(f"   - Derivative methods: {len(optimizer.available_methods['derivative'])}")
        
        study = optimizer.optimize(n_trials=3)
        print(f"   Nested CV completed!")
        
        best_pipeline = optimizer.best_pipeline
        best_pipeline.save_pipeline("best_pipeline_nested_cv.json")
        print("   Best representative pipeline saved to 'best_pipeline_nested_cv.json'")
        
        metadata = optimizer.get_metadata()
        metadata.to_csv("nested_cv_metadata.csv")
        print(f"   Nested CV metadata saved to nested_cv_metadata.csv")

        print("\n" + "=" * 60)
        print("🎉 NESTED CROSS-VALIDATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"🏆 Unbiased accuracy estimate: {study.best_value:.4f}")
        print(f"📊 Total evaluations (outer folds): {len(study.trials)}")
        print(f"💾 Files saved:")
        print("   - best_pipeline_nested_cv.json (representative optimized pipeline)")
        print("   - nested_cv_metadata.csv (detailed nested CV metadata with unbiased scores)")
        
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: File not found - {e}")
        print("\n🔍 Please check:")
        print("   1. If the data files are in the correct folder")
        print("   2. If the file paths are correct")
        print("   3. If the dataset folder exists")
        print(f"   Expected dataset path: {dataset_path}")
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        print("\n🔍 Please check:")
        print("   1. If the data files are in the correct folder")
        print("   2. If all dependencies are installed")
        print("   3. If there are write permissions in the current folder")
        
        # Show debug information
        import traceback
        print(f"\n📋 Error details:")
        traceback.print_exc()


if __name__ == "__main__":
    main() 
