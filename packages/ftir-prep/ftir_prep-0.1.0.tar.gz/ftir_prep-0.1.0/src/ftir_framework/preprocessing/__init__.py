"""
FTIR preprocessing module
"""

from .baseline import (
    BaselineCorrector, RubberbandBaselineCorrector, PolynomialBaselineCorrector,
    BaselineCorrectorFactory, baseline_rubberband, baseline_polynomial
)

from .normalization import (
    MinMaxNormalizer, VectorNormalizer, AmidaINormalizer, NormalizerFactory,
    normalize_minmax, normalize_vector, normalize_amida_i
)

from .smoothing import (
    SavitzkyGolaySmoother, WaveletSmoother, LocalPolynomialSmoother, SmootherFactory,
    sg_filter, wavelet_denoising, local_polynomial
)

from .derivatives import (
    DerivativeCalculator, apply_derivative
)

from .truncation import (
    FTIRTruncator, FingerprintTruncator, FingerprintAmideTruncator,
    TruncatorFactory, create_truncator, get_available_truncation_methods
)

__all__ = [
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
    'apply_derivative',
    
    # Truncation
    'FTIRTruncator',
    'FingerprintTruncator',
    'FingerprintAmideTruncator',
    'TruncatorFactory',
    'create_truncator',
    'get_available_truncation_methods'
] 