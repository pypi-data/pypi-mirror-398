# FTIR-Prep: FTIR Preprocessing Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](https://github.com/username/ftir-preprocessing-framework)

A modular and extensible framework for optimizing FTIR preprocessing pipelines for disease diagnosis.

## 🚀 Features

- **Modular**: Component-based reusable architecture
- **Extensible**: Easy addition of new preprocessing techniques
- **Automatic Optimization**: Optuna integration for optimal preprocessing pipeline search
- **Robust Validation**: Support for group-based cross-validation
- **Configurable**: Flexible pipeline configuration system
- **Documented**: Complete documentation with practical examples

## 📋 Supported Preprocessing Techniques

### 🔧 Baseline Correction
- **Rubberband**: Automatic correction using rubberband algorithm
- **Polynomial**: Correction using configurable order polynomials (1-6)
- **Whittaker**: Penalized least squares smoothing with lambda parameter
- **ALS**: Asymmetric Least Squares with lambda and p parameters
- **ArPLS**: Adaptive reweighted penalized least squares
- **DrPLS**: Doubly reweighted penalized least squares
- **GCV Spline**: Generalized cross-validation spline smoothing
- **Gaussian Process**: Baseline correction using Gaussian processes

### 📊 Normalization
- **Min-Max**: Individual Min-Max spectrum normalization
- **Vector**: L1, L2, or maximum normalization
- **Amida I**: Normalization based on amide I band peak (1600-1700 cm⁻¹)
- **Area**: Area under curve normalization

### 🎯 Smoothing
- **Savitzky-Golay**: Polynomial filter with configurable parameters
- **Wavelets**: Denoising using Daubechies wavelets (db2, db3, db4)
- **Local Polynomial**: LOWESS smoothing with configurable bandwidth
- **Whittaker**: Penalized least squares smoothing
- **GCV Spline**: Generalized cross-validation spline smoothing
- **Flat**: Flat window convolution smoothing
- **Hanning**: Hanning window convolution smoothing

### 📈 Derivatives
- **First Derivative**: First derivative calculation via Savitzky-Golay (order 1)
- **Second Derivative**: Second derivative calculation via Savitzky-Golay (order 2)

### ✂️ Wavelength Truncation
- **Fingerprint Region**: Keep only fingerprint region (900-1800 cm⁻¹)
- **Fingerprint + Amide**: Keep fingerprint and amide regions (900-1800, 2800-3050 cm⁻¹)

### 🔍 Model Explainability
- **SHAP Analysis**: Feature importance analysis using SHAP values

## 🏗️ Architecture

```
ftir_framework/
├── core/                    # Core functionalities
│   ├── pipeline.py         # Preprocessing pipeline
│   ├── evaluator.py        # Pipeline evaluation
│   └── explainer.py        # SHAP explainability analysis
├── preprocessing/           # Preprocessing techniques
│   ├── baseline.py         # Baseline correction
│   ├── normalization.py    # Normalization
│   ├── smoothing.py        # Smoothing
│   ├── derivatives.py      # Derivative calculation
│   └── truncation.py      # Wavelength truncation
├── optimization/            # Automatic optimization
│   └── optuna_optimizer.py # Optuna integration
├── utils/                   # Utilities
│   └── data_loader.py      # Data loading
└── config/                  # Configurations
    └── settings.py         # Default parameters
```

## 🚀 Installation

### Requirements
- Python 3.8+
- pip (usually included with Python)

### Installation via PyPI (Recommended - Simplest)


```bash
pip install ftir-prep
```



## 📖 Basic Usage

### 1. Data Loading 
#### 1.1 Separates into groups to guarantee that data from the same patient will be in the same fold in a future classification task
```python
from ftir_framework import FTIRDataLoader

# Load FTIR data
data_loader = FTIRDataLoader(
    data_path="ftir_data.dat",
    wavenumbers_path="wavenumbers.dat"
)

X, y, wavenumbers = data_loader.load_data()

# Create groups var that will be used in classification task to indicate that patient's data must be in the same fold
groups = data_loader.create_groups(instances_per_group=3)
```

#### 1.2 Slices the data to use only one spectra per patient. Data must be ordered by patient
```python
from ftir_framework import FTIRDataLoader

# Load FTIR data
data_loader = FTIRDataLoader(
    data_path="ftir_data.dat",
    wavenumbers_path="wavenumbers.dat"
)

X, y, wavenumbers = data_loader.load_data(slice_size = 3) #use one of the triplicated spectra per patient
```

### 2. Pipeline Creation
```python
from ftir_framework import FTIRPipeline, PipelineBuilder

# Using direct configuration
pipeline = FTIRPipeline()
pipeline.add_step('truncation', 'fingerprint_amide')
pipeline.add_step('baseline', 'polynomial', polynomial_order=2)
pipeline.add_step('normalization', 'vector')


# Using PipelineBuilder (Fluent API)
pipeline = (PipelineBuilder()
            .add_truncation('fingerprint_amide')
            .add_baseline('rubberband')
            .add_normalization('minmax')
            .add_smoothing('savgol', polyorder=2)
            .add_derivative('savgol',order=1)
            .build())
```

### 3. Execution and Evaluation
```python
from ftir_framework import PipelineEvaluator

# Process data
X_processed, wavenumbers_processed = pipeline.process(X, wavenumbers)

# Evaluate pipeline
evaluator = PipelineEvaluator(classifier=None, # use default Random Forest
                              cv_method='StratifiedGroupKFold', # cross-validation strategy
                              cv_params={'n_splits': 3, #folds
                                        'shuffler': False,
                                        'random_state': 42})
results = evaluator.evaluate_pipeline(pipeline,
                                      X, y,
                                      groups, # groups var created previously
                                      wavenumbers=wavenumbers
)

print(f"Accuracy: {results['mean_accuracy']:.4f} ± {results['std_accuracy']:.4f}")
```

### 4. Automatic Optimization
```python
from ftir_framework import OptunaPipelineOptimizer

# Automatically optimize parameters
optimizer = OptunaPipelineOptimizer(X, y, 
                                    wavenumbers,
                                    groups,
                                    evaluator=evaluator, # previously configured PipelineEvaluator object
                                    metric='f1_macro')
study = optimizer.optimize(n_trials=30)

best_pipeline = optimizer.best_pipeline
best_pipeline.save_pipeline("best_pipeline_found.json") # Saves the best pipeline found in a json file
print("Best pipeline saved to 'best_pipeline_found.json'")

# Save optimization metadata
metadata = optimizer.get_metadata()
metadata.to_csv("optimization_metadata.csv")

```

### 5. Model Explainability
```python
from ftir_framework import FTIRExplainer

# Create explainer
explainer = FTIRExplainer(classifier=your_classifier)

# Analyze feature importance with SHAP
# It will save in output_dir a csv and a png with feature importance data
results = explainer.explain_model(
    X_processed, y, groups,
    split_method='stratified_group',
    feature_names=wavenumbers_processed,
    output_dir="shap_analysis"
)
```

## 🔬 Practical Examples

### Pipeline Creation Examples
```bash
# Direct configuration example
python3 examples/create_pipeline/direct_configuration.py

# PipelineBuilder (Fluent API) example
python3 examples/create_pipeline/pipeline_builder.py
```

### Pipeline Comparison Example
```bash
# Compare different preprocessing strategies
python3 examples/compare_pipelines/compare_pipelines.py
```

### Pipeline Optimization Example
```bash
# Automatic pipeline optimization
python3 examples/pipeline_search/pipeline_search.py
```

### Pipeline Loading Example
```bash
# Load and use saved pipelines
python3 examples/read_pipeline_from_file/read_pipeline_file.py
```

### SHAP Explainability Example
```bash
# Feature importance analysis with SHAP
python3 examples/shap_analysis/explainer_example.py
```

## 🎯 Use Cases

### Disease Diagnosis
- Analysis of FTIR spectra from biological samples
- Biomarker identification
- Automatic sample classification

### Scientific Research
- Methodology comparison
- Protocol optimization
- Result validation


## 📚 Documentation

- **Docstrings**: Complete inline documentation
- **Examples**: Functional example code

## 👥 Authors

- **Lucas Mendonça** - *Initial development* - [GitHub](https://github.com/lucas-mendonca-andrade)


⭐ If this project was useful to you, consider giving it a star on GitHub! 