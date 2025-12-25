"""
FTIR Pipeline Optimization Search Example

This example demonstrates the automatic optimization functionality
of finding optimal preprocessing pipelines.

This example demonstrates how to use the framework to:
1. Load FTIR data
2. Apply optuna to find the best pipeline for the loaded data (including truncation)
3. Save the best pipeline found
4. Save optimization metadata

IMPORTANT: This example shows THREE different ways to configure the optimizer:
- OPTION 1 (Default): Uses all available methods
- OPTION 2 (Custom): Uses only specific methods you choose
- OPTION 3 (Basic): Uses only basic methods for faster optimization

By default, OPTION 1 is active. To use other options, uncomment the desired section.
"""

import numpy as np
import os
from ftir_framework import (
    FTIRDataLoader,
    PipelineEvaluator,
    OptunaPipelineOptimizer
)


def main():

    print("=== FTIR Framework Pipeline Optimization Search Example ===\n")
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
        
        # X, y, wavenumbers = data_loader.load_data(slice_size=3) # If you want to apply slice
        X, y, wavenumbers = data_loader.load_data()
        print(f"   Data loaded: {X.shape[0]} samples, {X.shape[1]} features")

        groups = data_loader.create_groups(instances_per_group=3) # In case of slice, no groups needed. Can use instances_per_group=1
        print(f"   Groups created: {len(np.unique(groups))}")
        
        print("2. Setting up evaluation and optimization...")
        print("   Note: Truncation is now integrated into the pipeline optimization process.")
        print("   The optimizer will automatically test different truncation methods:")
        print("   - 'fingerprint': Keeps only 900-1800 cm⁻¹ range")
        print("   - 'fingerprint_amide': Keeps 900-1800 and 2800-3050 cm⁻¹ ranges")
        evaluator = PipelineEvaluator(classifier=None,
                                     cv_method='StratifiedGroupKFold',
                                     cv_params={'n_splits': 3,
                                                'shuffler': False,
                                                'random_state': 42})
        
        # OPTION 1: Use default methods (recommended for beginners)
        # If you don't specify available_methods, the optimizer will use these defaults:
        # - truncation: ['fingerprint', 'fingerprint_amide']
        # - baseline: ['none', 'rubberband', 'polynomial', 'whittaker', 'als', 'arpls', 'drpls', 'gcv_spline']
        # - normalization: ['none', 'minmax', 'vector', 'amida_i', 'area']
        # - smoothing: ['none', 'savgol', 'wavelet', 'local_poly', 'whittaker', 'gcv_spline', 'moving_average', 'hanning']
        # - derivative: ['none', 'savgol']
        optimizer = OptunaPipelineOptimizer(X, y, wavenumbers, groups,
                                            evaluator=evaluator,
                                            metric='f1_macro')
        
        # OPTION 2: Specify custom methods (advanced users)
        # Uncomment the lines below to use only specific methods:
        # custom_methods = {
        #     'truncation': ['fingerprint', 'fingerprint_amide'],  # Truncation methods
        #     'baseline': ['none', 'rubberband', 'whittaker'],    # Only these baseline methods
        #     'normalization': ['none', 'minmax', 'area'],        # Only these normalization methods
        #     'smoothing': ['none', 'savgol', 'hanning'],        # Only these smoothing methods
        #     'derivative': ['none', 'savgol']                   # Only these derivative methods
        # }
        # 
        # optimizer = OptunaPipelineOptimizer(X, y, wavenumbers, groups,
        #                                     evaluator=evaluator,
        #                                     metric='f1_macro',
        #                                     available_methods=custom_methods)
        
        # OPTION 3: Use only basic methods (faster optimization)
        # Uncomment the lines below for a simpler, faster search:
        # basic_methods = {
        #     'truncation': ['fingerprint'],                    # Only fingerprint truncation
        #     'baseline': ['none', 'rubberband'],              # Only basic baseline methods
        #     'normalization': ['none', 'minmax'],             # Only basic normalization methods
        #     'smoothing': ['none', 'savgol'],                 # Only basic smoothing methods
        #     'derivative': ['none']                           # No derivatives
        # }
        # 
        # optimizer = OptunaPipelineOptimizer(X, y, wavenumbers, groups,
        #                                     evaluator=evaluator,
        #                                     metric='f1_macro',
        #                                     available_methods=basic_methods)
        
        print("4. Starting optimization process...")
        print("   Note: The number of trials (100) should be adjusted based on the number of methods you're testing.")
        print("   More methods = more trials needed for good optimization.")
        print("   Current configuration will test:")
        print(f"   - Truncation methods: {len(optimizer.available_methods['truncation'])}")
        print(f"   - Baseline methods: {len(optimizer.available_methods['baseline'])}")
        print(f"   - Normalization methods: {len(optimizer.available_methods['normalization'])}")
        print(f"   - Smoothing methods: {len(optimizer.available_methods['smoothing'])}")
        print(f"   - Derivative methods: {len(optimizer.available_methods['derivative'])}")
        
        study = optimizer.optimize(n_trials=100)
        print(f"   Optimization completed. Total trials: {len(study.trials)}")
        
        best_pipeline = optimizer.best_pipeline
        best_pipeline.save_pipeline("best_pipeline_found.json")
        print("   Best pipeline saved to 'best_pipeline_found.json'")
        
        # Save optimization metadata
        metadata = optimizer.get_metadata()
        metadata.to_csv("optimization_metadata.csv")
        print(f"   Optimization metadata saved to optimization_metadata.csv")

        # 6. Final summary
        print("\n" + "=" * 60)
        print("🎉 OPTIMIZATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"🏆 Best accuracy found: {study.best_value:.4f}")
        print(f"📊 Total trials: {len(study.trials)}")
        print(f"💾 Files saved:")
        print("   - best_pipeline_found.json (optimized pipeline)")
        print("   - optimization_metadata.json (detailed optimization metadata)")

        
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