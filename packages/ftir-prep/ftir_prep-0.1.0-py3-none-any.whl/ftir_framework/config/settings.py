"""
Default Settings for the FTIR Preprocessing Framework
"""

# Wavelength truncation settings
WAVELENGTH_RANGES = {
    'fingerprint': (900, 1800),      # Fingerprint region
    'amide': (2800, 3050),           # Amide region
    'custom': None                   # For custom ranges
}

# Baseline settings
BASELINE_CONFIG = {
    'rubberband': {
        'method': 'rubberband'
    },
    'polynomial': {
        'method': 'poly',
        'polynomial_order_range': (1, 6)
    }
}

# Normalization settings
NORMALIZATION_CONFIG = {
    'minmax': {},
    'vector': {'norm': 'l2'},
    'amide_i': {
        'range': (1600, 1700)
    }
}

# Smoothing settings
SMOOTHING_CONFIG = {
    'savgol': {
        'window_length': 11,
        'polyorder_range': (1, 6),
        'deriv_range': (0, 2)
    },
    'wavelet': {
        'wavelets': ['db2', 'db3', 'db4'],
        'level_range': (1, 3),
        'mode': 'soft'
    },
    'local_polynomial': {
        'bandwidth_range': (1, 6),
        'iterations': 0
    }
}

# Cross-validation settings
CV_CONFIG = {
    'method': 'StratifiedGroupKFold',  # Combines stratification while respecting groups
    'n_splits': 5,
    'shuffle': False, 
    'random_state': 42,
    'description': 'Stratified cross-validation that respects groups (patients)',
    'shuffle_warning': '''
    ⚠️ WARNING: Shuffling in FTIR data may cause issues:
    
    ✅ RECOMMENDED (shuffle=False):
       - Preserves the natural temporal order of the data
       - Prevents information leakage between correlated samples
       - More realistic for clinical applications
    
    ❌ NOT RECOMMENDED (shuffle=True):
       - May create artificial dependencies between train and test
       - May hide generalization issues
       - May artificially inflate accuracy
    
    💡 For FTIR data, keep shuffle=False unless:
       - You are certain there is no temporal correlation
       - You are specifically testing robustness to shuffling
       - You have independent external validation
    '''
}

# Classifier settings
CLASSIFIER_CONFIG = {
    'RandomForest': {
        'n_estimators': 100,
        'random_state': 42,
        'class_weight': 'balanced',  # Handles class imbalance
        'max_depth': None,
        'min_samples_split': 2,
        'min_samples_leaf': 1
    }
}

# Optimization settings
OPTIMIZATION_CONFIG = {
    'n_trials': 30,
    'direction': 'maximize',
    'timeout': None
}

# Default order of preprocessing techniques
DEFAULT_PIPELINE_ORDER = ['smoothing', 'normalization', 'baseline', 'derivative']
