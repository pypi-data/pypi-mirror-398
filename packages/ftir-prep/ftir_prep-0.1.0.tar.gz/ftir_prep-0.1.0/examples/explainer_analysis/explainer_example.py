"""
FTIRExplainer example for SHAP explainability analysis

This example demonstrates how to use the FTIRExplainer to generate
SHAP-based explanations for FTIR classification models.
"""

import numpy as np
import os
from ftir_framework.core.pipeline import FTIRPipeline
from ftir_framework.core.explainer import FTIRExplainer
from ftir_framework.utils.data_loader import FTIRDataLoader


def main():
    """Main function demonstrating SHAP analysis with FTIR data"""
    print("=== FTIR SHAP Explainability Analysis Example ===\n")
    
    try:
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        dataset_path = os.path.join(project_root, "dataset")
        
        print(f"Script directory: {script_dir}")
        print(f"Project root: {project_root}")
        print(f"Dataset path: {dataset_path}")
        
        print("\n1. Loading FTIR data...")
        data_loader = FTIRDataLoader(
            data_path=os.path.join(dataset_path, "absorbance.dat"),
            wavenumbers_path=os.path.join(dataset_path, "wavenumbers.dat")
        )
        
        X, y, wavenumbers = data_loader.load_data()
        groups = data_loader.create_groups(instances_per_group=3)
        
        print(f"   Data loaded: {X.shape[0]} samples, {X.shape[1]} features")
        print(f"   Classes: {np.unique(y)} (counts: {np.bincount(y)})")
        print(f"   Groups created: {len(np.unique(groups))} groups")
        print(f"   Wavenumber range: {wavenumbers.min():.0f} - {wavenumbers.max():.0f} cm⁻¹")
        
        print("\n2. Creating preprocessing pipeline...")
        pipeline = FTIRPipeline()
        pipeline.add_step('truncation', 'fingerprint_amide') 
        pipeline.add_step('baseline', 'polynomial', polynomial_order=3)
        pipeline.add_step('normalization', 'vector')
        pipeline.add_step('smoothing', 'wavelet', wavelet='db3')
        pipeline.add_step('derivative', 'savgol', order=1)
        
        print("   Pipeline steps:", pipeline.get_pipeline_summary()['steps'])
        
        print("\n3. Processing data through pipeline...")
        X_processed, wavenumbers_processed = pipeline.process(X, wavenumbers)
        
        feature_names = [f"wn_{wn:.0f}" for wn in wavenumbers_processed[:X_processed.shape[1]]]
        
        print(f"   Processed data shape: {X_processed.shape}")
        
        print("\n4. Creating SHAP explainer...")

        explainer = FTIRExplainer()
        
        print("\n5. Running SHAP explainability analysis...")
        results = explainer.explain_model(
            X_processed=X_processed,
            y=y,
            groups=groups,
            split_method='stratified_group',
            test_size=0.2,
            feature_names=feature_names,
            output_dir="shap_analysis_output"
        )
        
        # 6. Display results
        print_results_summary(results)
        
        
        print("\n🎉 SHAP analysis completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Data files not found: {e}")
        print("💡 Make sure the dataset files exist in the dataset/ directory")
        print("   Expected files: absorbance.dat, wavenumbers.dat")
    except ImportError as e:
        print("❌ SHAP not installed")
        print("💡 Install with: pip install shap")
    except Exception as e:
        print(f"❌ Error during execution: {e}")


def print_results_summary(results):
    """Prints a summary of SHAP analysis results"""
    print(f"\n📊 SHAP ANALYSIS RESULTS:")
    print(f"   Split method: {results['split_method']}")
    print(f"   Train samples: {results['n_train_samples']}")
    print(f"   Test samples: {results['n_test_samples']}")
    print(f"   Features: {results['n_features']}")
    print(f"   Actual test size: {results['test_size_actual']:.3f}")
    print(f"   📁 Output directory: {results['output_dir']}")
    
    # List generated files
    files_generated = []
    if 'summary_plot' in results:
        files_generated.append("Summary Plot")
    if 'bar_plot' in results:
        files_generated.append("Bar Plot")
    if 'waterfall_plots' in results:
        files_generated.append(f"{len(results['waterfall_plots'])} Waterfall Plots")
    if 'shap_values_csv' in results:
        files_generated.append("SHAP Values CSV")
    if 'importance_csv' in results:
        files_generated.append("Feature Importance CSV")
    
    print(f"   ✅ Generated files: {', '.join(files_generated)}")


def analyze_top_features(explainer, results):
    """Analyzes and displays the most important features"""
    print("\n🔍 TOP 10 MOST IMPORTANT FEATURES:")
    top_features = explainer.get_top_features(results['importance_csv'], n_features=10)
    
    for i, row in top_features.iterrows():
        wavenumber = row['feature_name'].replace('wn_', '')
        print(f"   {row['rank']:2d}. {row['feature_name']:12s} ({wavenumber:>4s} cm⁻¹) - "
              f"Importance: {row['mean_abs_shap']:.4f}")
    
    # Generate custom plot
    plot_path = explainer.plot_top_features(
        results['importance_csv'],
        n_features=15,
        output_path=os.path.join(results['output_dir'], "top_15_features.png")
    )
    print(f"\n📊 Top features plot saved to: {plot_path}")
    
    # Show chemical significance hints
    print("\n🧪 Chemical significance hints:")
    print("   - Look for peaks around 1650 cm⁻¹ (Amide I)")
    print("   - Check 2850-2950 cm⁻¹ (C-H stretches)")
    print("   - Examine 1000-1300 cm⁻¹ (fingerprint region)")
    print("   - Consider 1450-1550 cm⁻¹ (Amide II)")


if __name__ == "__main__":
    main()
