"""
Comparison between pipelines example of the FTIR Preprocessing Framework

This example demonstrates how to use the framework to:
1. Load FTIR data
2. Create and execute preprocessing pipelines
3. Evaluate different configurations
"""

import numpy as np
import os
from ftir_framework import (
    FTIRDataLoader, 
    FTIRPipeline, 
    PipelineBuilder,
    PipelineEvaluator
)


def main():
    try:
        print("=== FTIR Framework Comparison between pipelines Example ===\n")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir)) 
        dataset_path = os.path.join(project_root, "dataset")
        
        print(f"Script directory: {script_dir}")
        print(f"Project root: {project_root}")
        print(f"Dataset path: {dataset_path}")
        
        # 1. Data loading
        print("\n1. Loading data...")

        # Replace with the correct paths to your data
        data_loader = FTIRDataLoader(
            data_path=os.path.join(dataset_path, "absorbance.dat"),
            wavenumbers_path=os.path.join(dataset_path, "wavenumbers.dat")
        )
        
        X, y, wavenumbers = data_loader.load_data()
        groups = data_loader.create_groups(instances_per_group=3)
        
        print(f"   Data loaded: {X.shape[0]} samples, {X.shape[1]} features")
        print(f"   Wavenumber range: {wavenumbers.min():.1f} - {wavenumbers.max():.1f}")
        print(f"   Number of classes: {len(np.unique(y))}")
        print(f"   Groups created: {len(np.unique(groups))}\n")
        

        print("2. Creating preprocessing pipelines...")
        
        # Pipeline 1: Using PipelineBuilder
        pipeline1 = (PipelineBuilder()
                     .add_truncation('fingerprint_amide')  # Truncate to fingerprint + amide regions
                     .add_baseline('rubberband')
                     .add_normalization('minmax')
                     .add_smoothing('savgol', polyorder=2)
                     .build())
        
        # Pipeline 2: Using direct configuration
        pipeline2 = FTIRPipeline()
        pipeline2.add_step('truncation', 'fingerprint')  # Only fingerprint region
        pipeline2.add_step('baseline', 'polynomial', polynomial_order=3)
        pipeline2.add_step('normalization', 'vector')
        pipeline2.add_step('smoothing', 'wavelet', wavelet='db3')
        pipeline2.add_step('derivative', 'savgol', order=1)
        
        
        pipelines = {
            'Pipeline 1 (Fingerprint+Amide + Rubberband + MinMax + SavGol)': pipeline1,
            'Pipeline 2 (Fingerprint + Polynomial + Vector + Wavelet + First Derivative)': pipeline2
        }
        
        print(f"   {len(pipelines)} pipelines created\n")
        
        # 3. Pipeline evaluation
        print("3. Evaluating pipelines...")
        evaluator = PipelineEvaluator(cv_method='GroupKFold', cv_params={'n_splits': 5})
        
        comparison_results = evaluator.compare_pipelines(
            pipelines, X, y, groups, wavenumbers=wavenumbers
        )
        
        # Generate report
        best_name, best_results = comparison_results['best_pipeline_name'], comparison_results['best_results']
        print(f"BEST PIPELINE: {best_name}\n")
        print(f"   Score: {best_results:.4f}")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        print("Please check if the data files exist in the correct paths")
        print(f"Expected dataset path: {dataset_path}")
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")
        print("Please check the error details above and verify your data and configuration")


if __name__ == "__main__":
    main() 