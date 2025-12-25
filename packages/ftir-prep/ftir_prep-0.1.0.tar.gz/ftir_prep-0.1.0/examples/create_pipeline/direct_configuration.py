"""
Direct configuration example of creating a pipeline with the FTIR Preprocessing Framework

This example demonstrates how to use the framework to:
1. Load FTIR data
2. Create and execute preprocessing pipelines using direct configuration
3. Process data with the custom pipeline steps created
"""

import numpy as np
import os
from ftir_framework import (
    FTIRDataLoader, 
    FTIRPipeline
)


def main():
    try:
        print("=== FTIR Framework Direct Configuration Example ===\n")
        
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
        

        print("2. Creating pipeline using direct configuration...")
        
        # Pipeline: Using direct configuration
        pipeline = FTIRPipeline()
        pipeline.add_step('truncation', 'fingerprint_amide')  # Truncate to fingerprint + amide regions
        pipeline.add_step('baseline', 'polynomial', polynomial_order=3)
        pipeline.add_step('normalization', 'vector')
        pipeline.add_step('smoothing', 'wavelet', wavelet='db3')
        pipeline.add_step('derivative', 'savgol', order=1)
        
        print("   Pipeline created successfully")
        print(f"   Number of steps: {len(pipeline.steps)}\n")

        print("3. Processing data with pipeline...")
        print(f"   Original data shape: {X.shape}")
        print(f"   Original wavenumber range: {wavenumbers.min():.1f} - {wavenumbers.max():.1f}")
        
        X_processed, wavenumbers_processed = pipeline.process(X, wavenumbers)
        print(f"   Data processed successfully. Final shape: {X_processed.shape}")
        print("   Pipeline execution completed!")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        print("Please check if the data files exist in the correct paths")
        print(f"Expected dataset path: {dataset_path}")
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")
        print("Please check the error details above and verify your data and configuration")


if __name__ == "__main__":
    main() 