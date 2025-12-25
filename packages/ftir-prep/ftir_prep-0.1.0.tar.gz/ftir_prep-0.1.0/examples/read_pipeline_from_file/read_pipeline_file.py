"""
FTIR Pipeline Reading Pipeline from File Example

This example demonstrates how to read a pipeline from a file and use it to process data.

This example demonstrates how to use the framework to:
1. Load FTIR data
2. Load a pipeline from a file
3. Process data with the pipeline
"""

import os
from ftir_framework import FTIRDataLoader, FTIRPipeline

def main():

    print("=== FTIR Framework Reading Pipeline from File Example ===\n")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        dataset_path = os.path.join(project_root, "dataset")
        
        print(f"Script directory: {script_dir}")
        print(f"Project root: {project_root}")
        print(f"Dataset path: {dataset_path}")
        
        print("Loading FTIR data...")
        data_loader = FTIRDataLoader(
            data_path=os.path.join(dataset_path, "absorbance.dat"),
            wavenumbers_path=os.path.join(dataset_path, "wavenumbers.dat")
        )

        # The slice size and group size depend on how the initial dataset was configured

        # X, y, wavenumbers = data_loader.load_data(slice_size=3) # If you want to apply slice
        X, y, wavenumbers = data_loader.load_data()

        print(f"Data loaded successfully. Shape: {X.shape}")

        groups = data_loader.create_groups(instances_per_group=3) # In case of slice, no groups needed. Can use instances_per_group=1
        print(f"Groups created successfully. Number of groups: {len(groups)}")

        print("Loading pipeline from file...")
        pipeline = FTIRPipeline.load_pipeline('best_pipeline_found.json')
        print("Pipeline loaded successfully")
        print(f"Pipeline steps: {pipeline.steps}")

        print("Processing data with pipeline...")
        print(f"Original data shape: {X.shape}")
        print(f"Original wavenumber range: {wavenumbers.min():.1f} - {wavenumbers.max():.1f}")
        
        X_processed, wavenumbers_processed = pipeline.process(X, wavenumbers)
        print(f"Data processed successfully. Final shape: {X_processed.shape}")
        print(f"Processed wavenumber range: {wavenumbers_processed.min():.1f} - {wavenumbers_processed.max():.1f}")
        print("Processed data preview:")
        print(X_processed)

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        print("Please check if the data files and pipeline file exist in the correct paths")
        print(f"Expected dataset path: {dataset_path}")
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")
        print("Please check the error details above and verify your data and configuration")

if __name__ == "__main__":
    main()