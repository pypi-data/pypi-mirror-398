"""
Module for normalization techniques of FTIR spectra
"""

import numpy as np
from typing import Optional, Tuple
from abc import ABC, abstractmethod
import rampy as rp


class FTIRNormalizer(ABC):
    """
    Abstract class for FTIR normalizers
    """
    
    @abstractmethod
    def normalize(self, X: np.ndarray, wavenumbers: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Applies normalization
        
        Args:
            X: Spectra matrix (n_samples, n_features)
            wavenumbers: Wavenumbers array (optional)
            
        Returns:
            Matrix of normalized spectra
        """
        pass


class NoOpNormalizer(FTIRNormalizer):
    """
    Normalizer that makes no modifications (method 'none')
    """
    
    def __init__(self):
        self.name = "none"
    
    def normalize(self, X: np.ndarray, wavenumbers: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Does not modify the data
        
        Args:
            X: Spectra matrix
            wavenumbers: Not used
            
        Returns:
            Unchanged spectra matrix
        """
        return X.copy()


class MinMaxNormalizer(FTIRNormalizer):
    """
    Min-Max normalizer applied per spectrum
    """
    
    def __init__(self):
        self.name = "minmax"
    
    def normalize(self, X: np.ndarray, wavenumbers: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Applies Min-Max normalization per spectrum
        
        Args:
            X: Spectra matrix (n_samples, n_features) - intensities to normalize
            wavenumbers: Wavenumbers array (n_features,) - wavelength values
            
        Returns:
            Matrix of normalized spectra
        """
        
        # Transpose X to match rampy's expected format: (n_features, n_samples)
        # This makes each row a wavelength and each column a sample
        X_T = X.T  # Shape: (n_features, n_samples)
        X_norm_T = rp.normalise(y=X_T, method='minmax')
        # Transpose back to original format: (n_samples, n_features)
        return X_norm_T.T


class VectorNormalizer(FTIRNormalizer):
    """
    Vector normalizer
    """
    
    def __init__(self, norm: str = 'l2'):
        """
        Initializes the normalizer
        
        Args:
            norm: Norm type ('l1', 'l2', 'max')
        """
        self.norm = norm
        self.name = f"vector_{norm}"
    
    def normalize(self, X: np.ndarray, wavenumbers: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Applies vector normalization
        
        Args:
            X: Spectra matrix
            wavenumbers: Not used in this implementation
            
        Returns:
            Matrix of normalized spectra
        """
        if self.norm == 'l2':
            # This normalizes by maximum intensity, equivalent to L2 normalization
            X_T = X.T  # Shape: (n_features, n_samples)
            X_norm_T = rp.normalise(y=X_T, method='intensity')
            return X_norm_T.T
        else:
            return self._normalize_with_numpy(X)
    
    def _normalize_with_numpy(self, X):
        """Numpy implementation for L1 and max norms"""
        if X.ndim == 1:
            # Single spectrum
            return self._normalize_spectrum_numpy(X)
        else:
            # Multiple spectra
            X_norm = np.zeros_like(X)
            for i, spectrum in enumerate(X):
                X_norm[i] = self._normalize_spectrum_numpy(spectrum)
            return X_norm
    
    def _normalize_spectrum_numpy(self, spectrum):
        """Normalize single spectrum using numpy"""
        if self.norm == 'l1':
            # L1 norm (Manhattan distance)
            norm_value = np.sum(np.abs(spectrum))
            if norm_value > 0:
                return spectrum / norm_value
            else:
                return spectrum
                
        elif self.norm == 'max':
            # Max norm (infinity norm)
            norm_value = np.max(np.abs(spectrum))
            if norm_value > 0:
                return spectrum / norm_value
            else:
                return spectrum
        else:
            raise ValueError(f"Unsupported norm type: {self.norm}")


class AmidaINormalizer(FTIRNormalizer):
    """
    Normalizer based on the amide I band peak
    """
    
    def __init__(self, amida_range: Tuple[float, float] = (1600, 1700)):
        """
        Initializes the normalizer
        
        Args:
            amida_range: Wavenumber range for the amide I band
        """
        self.amida_range = amida_range
        self.name = f"amida_i_{amida_range[0]}_{amida_range[1]}"
    
    def normalize(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies normalization based on the amide I band peak
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of normalized spectra
        """
        if wavenumbers is None:
            raise ValueError("Wavenumbers are required for amide I normalization")
        
        def norm_spectrum(spectrum, wavs):
            amida_i_mask = ((wavs >= self.amida_range[0]) & (wavs <= self.amida_range[1]))
            amida_i_peak = np.max(np.abs(spectrum[amida_i_mask]))
            
            if amida_i_peak == 0:
                return spectrum
            return spectrum / amida_i_peak
        
        return np.array([norm_spectrum(s, wavenumbers) for s in X])


class AreaNormalizer(FTIRNormalizer):
    """
    Area-based normalizer
    """
    
    def __init__(self):
        self.name = "area"
    
    def normalize(self, X: np.ndarray, wavenumbers: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Applies area-based normalization
        
        Args:
            X: Spectra matrix (n_samples, n_features) - intensities to normalize
            wavenumbers: Wavenumbers array (n_features,) - wavelength values (required for area normalization)
            
        Returns:
            Matrix of normalized spectra
            
        Raises:
            ValueError: If wavenumbers are not provided (required for area normalization)
        """
        if wavenumbers is None:
            raise ValueError("Wavenumbers are required for area normalization")
        
        # Ensure wavenumbers are in ascending order for correct area calculation
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        # Transpose X to match rampy's expected format: (n_features, n_samples)
        X_T = X_reversed.T  # Shape: (n_features, n_samples)
        
        # Expand wavenumbers to match X_T shape: (n_features, n_samples)
        # Each column gets the same wavenumbers array
        wavenumbers_T = np.tile(wavenumbers_asc.reshape(-1, 1), (1, X_reversed.shape[0]))
        
        X_norm_T = rp.normalise(X_T, x=wavenumbers_T, method='area')
        
        # Transpose back to original format: (n_samples, n_features)
        X_norm = X_norm_T.T
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            X_norm = X_norm[:, ::-1]
        
        return X_norm


class NormalizerFactory:
    """
    Factory for creating normalizers
    """
    
    @staticmethod
    def create_normalizer(method: str, **kwargs) -> FTIRNormalizer:
        """
        Creates a normalizer based on the specified method
        
        Args:
            method: Normalization method ('minmax', 'vector', 'amida_i', 'area', 'none')
            **kwargs: Additional parameters for the normalizer
            
        Returns:
            Normalizer instance
        """
        if method == "minmax":
            return MinMaxNormalizer()
        elif method == "vector":
            norm = kwargs.get('norm', 'l2')
            return VectorNormalizer(norm=norm)
        elif method == "amida_i":
            amida_range = kwargs.get('amida_range', (1600, 1700))
            return AmidaINormalizer(amida_range=amida_range)
        elif method == "area":
            return AreaNormalizer()
        elif method == "none":
            # Returns a normalizer that does nothing
            return NoOpNormalizer()
        else:
            raise ValueError(f"Unsupported normalization method: {method}")


# Convenience functions for compatibility with existing code
def normalize_minmax(X: np.ndarray, wavenumbers: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Convenience function for Min-Max normalization
    
    Args:
        X: Spectra matrix
        wavenumbers: Not used
        
    Returns:
        Matrix of normalized spectra
    """
    normalizer = MinMaxNormalizer()
    return normalizer.normalize(X, wavenumbers)


def normalize_vector(X: np.ndarray, wavenumbers: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Convenience function for vector normalization
    
    Args:
        X: Spectra matrix
        wavenumbers: Not used
        
    Returns:
        Matrix of normalized spectra
    """
    normalizer = VectorNormalizer()
    return normalizer.normalize(X, wavenumbers)


def normalize_amida_i(X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
    """
    Convenience function for amide I normalization
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        
    Returns:
        Matrix of normalized spectra
    """
    normalizer = AmidaINormalizer()
    return normalizer.normalize(X, wavenumbers)


def normalize_area(X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
    """
    Convenience function for area normalization
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array (required for area calculation)
        
    Returns:
        Matrix of normalized spectra
    """
    normalizer = AreaNormalizer()
    return normalizer.normalize(X, wavenumbers) 