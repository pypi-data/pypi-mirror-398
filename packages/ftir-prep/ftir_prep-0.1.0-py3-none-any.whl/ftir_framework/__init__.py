"""
Framework de Pré-processamento FTIR

Um framework modular e extensível para otimização de pipelines de pré-processamento
de espectros FTIR para diagnóstico de doenças.
"""

__version__ = "0.1.0"
__author__ = "Lucas Mendonça"

# Imports principais
from .core.pipeline import FTIRPipeline, PipelineBuilder, create_pipeline_from_order
from .core.evaluator import PipelineEvaluator
from .core.explainer import FTIRExplainer
from .optimization.optuna_optimizer import OptunaPipelineOptimizer
from .utils.data_loader import FTIRDataLoader

# Imports de validação cruzada
from sklearn.model_selection import StratifiedGroupKFold

# Imports de pré-processamento
from .preprocessing.baseline import (
    BaselineCorrector, RubberbandBaselineCorrector, PolynomialBaselineCorrector,
    BaselineCorrectorFactory, baseline_rubberband, baseline_polynomial
)

from .preprocessing.normalization import (
    MinMaxNormalizer, VectorNormalizer, AmidaINormalizer, NormalizerFactory,
    normalize_minmax, normalize_vector, normalize_amida_i
)

from .preprocessing.smoothing import (
    SavitzkyGolaySmoother, WaveletSmoother, LocalPolynomialSmoother, SmootherFactory,
    sg_filter, wavelet_denoising, local_polynomial
)

from .preprocessing.derivatives import (
    DerivativeCalculator, apply_derivative
)

__all__ = [
    # Core
    'FTIRPipeline',
    'PipelineBuilder', 
    'create_pipeline_from_order',
    'PipelineEvaluator',
    'FTIRExplainer',
    
    # Optimization
    'OptunaPipelineOptimizer',
    
    # Data loading
    'FTIRDataLoader',
    
    # Cross-validation
    'StratifiedGroupKFold',
    
    # Baseline
    'BaselineCorrector',
    'RubberbandBaselineCorrector',
    'PolynomialBaselineCorrector',
    'BaselineCorrectorFactory',
    'baseline_rubberband',
    'baseline_polynomial',
    
    # Normalization
    'MinMaxNormalizer',
    'VectorNormalizer',
    'AmidaINormalizer',
    'NormalizerFactory',
    'normalize_minmax',
    'normalize_vector',
    'normalize_amida_i',
    
    # Smoothing
    'SavitzkyGolaySmoother',
    'WaveletSmoother',
    'LocalPolynomialSmoother',
    'SmootherFactory',
    'sg_filter',
    'wavelet_denoising',
    'local_polynomial',
    
    # Derivatives
    'DerivativeCalculator',
    'apply_derivative'
] 