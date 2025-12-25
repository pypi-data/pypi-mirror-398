# FTIR Framework Usage Examples

This folder contains practical examples of how to use the FTIR Preprocessing Framework.

## 📁 Available Files

### 1. `create_pipeline/direct_configuration.py` - Direct Configuration Example
**Description**: Demonstrates how to create pipelines using direct configuration
- Data loading
- Pipeline creation with direct step addition
- Data processing with custom pipeline

**Usage**:
```bash
python3 examples/create_pipeline/direct_configuration.py
```

**Ideal for**: Users who want to understand direct pipeline configuration

---

### 2. `create_pipeline/pipeline_builder.py` - Pipeline Builder Example
**Description**: Demonstrates how to create pipelines using the fluent PipelineBuilder
- Data loading
- Pipeline creation with PipelineBuilder
- Data processing with built pipeline

**Usage**:
```bash
python3 examples/create_pipeline/pipeline_builder.py
```

**Ideal for**: Users who prefer fluent API for pipeline creation

---

### 3. `compare_pipelines/compare_pipelines.py` - Pipeline Comparison Example
**Description**: Demonstrates how to compare different preprocessing pipelines
- Data loading
- Creation of multiple pipelines
- Pipeline evaluation and comparison
- Performance analysis

**Usage**:
```bash
python3 examples/compare_pipelines/compare_pipelines.py
```

**Ideal for**: Users who want to compare different preprocessing strategies

---

### 4. `pipeline_search/pipeline_search.py` - Pipeline Optimization Example
**Description**: Demonstrates automatic pipeline optimization using Optuna
- Data loading
- Automatic pipeline optimization
- Best pipeline saving
- Results analysis

**Usage**:
```bash
python3 examples/pipeline_search/pipeline_search.py
```

**Ideal for**: Researchers who want to automatically find optimal preprocessing pipelines

---

### 5. `read_pipeline_from_file/read_pipeline_file.py` - Load Pipeline from File Example
**Description**: Demonstrates how to load and use saved pipelines
- Data loading
- Pipeline loading from JSON file
- Data processing with loaded pipeline

**Usage**:
```bash
python3 examples/read_pipeline_from_file/read_pipeline_file.py
```

**Ideal for**: Users who want to reuse previously created pipelines

---

### 6. `explainer_analysis/explainer_example.py` - SHAP explainability analysis Example
**Description**: Demonstrates how to use the FTIRExplainer to generate SHAP-based explanations for FTIR classification models.
- Data loading
- Pipeline creation with direct step addition
- Data processing with custom pipeline
- Get SHAP analysis (csv and png) with default classifier

**Usage**:
```bash
python3 examples/explainer_analysis/explainer_example.py
```

**Ideal for**: Users who want to obtain SHAP analysis for their classifiers

---

## 🚀 How to Run the Examples

### Prerequisites
1. **Framework installed**:
   ```bash
   pip install -e .
   ```

2. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Data available** (for examples that use real data):
   - `dataset/absorbance.dat`
   - `dataset/wavenumbers.dat`

### Execution
```bash
# Navigate to the examples folder
cd examples

# Run the desired example
python3 create_pipeline/direct_configuration.py
python3 create_pipeline/pipeline_builder.py
python3 compare_pipelines/compare_pipelines.py
python3 pipeline_search/pipeline_search.py
python3 read_pipeline_from_file/read_pipeline_file.py
python3 explainer_analysis/explainer_example.py
```

💡 **Tip**: Start with `create_pipeline/direct_configuration.py` if you want to understand basic pipeline creation, or `pipeline_search/pipeline_search.py` if you want to see automatic optimization in action! 