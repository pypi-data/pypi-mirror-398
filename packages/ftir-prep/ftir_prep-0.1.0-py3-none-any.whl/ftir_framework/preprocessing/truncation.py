"""
Module for wavelength truncation techniques in FTIR spectra
"""

import numpy as np
from typing import List, Tuple
from abc import ABC, abstractmethod


class FTIRTruncator(ABC):
    """
    Abstract class for FTIR wavelength truncators
    """
    
    @abstractmethod
    def truncate(self, X: np.ndarray, wavenumbers: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies wavelength truncation
        
        Args:
            X: Spectra matrix (n_samples, n_features)
            wavenumbers: Wavenumbers array
            
        Returns:
            Tuple containing truncated spectra matrix and truncated wavenumbers array
        """
        pass


class FingerprintTruncator(FTIRTruncator):
    """
    Truncator that keeps only the fingerprint region (900-1800 cm⁻¹)
    """
    
    def __init__(self):
        self.name = "fingerprint"
        self.ranges = [(900, 1800)]
    
    def truncate(self, X: np.ndarray, wavenumbers: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Truncates data to fingerprint region only
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Tuple containing truncated spectra matrix and truncated wavenumbers array
        """
        mask = np.zeros(len(wavenumbers), dtype=bool)
        
        for min_wav, max_wav in self.ranges:
            mask |= ((wavenumbers >= min_wav) & (wavenumbers <= max_wav))
        
        X_truncated = X[:, mask]
        wavenumbers_truncated = wavenumbers[mask]
        
        return X_truncated, wavenumbers_truncated


class FingerprintAmideTruncator(FTIRTruncator):
    """
    Truncator that keeps fingerprint region (900-1800 cm⁻¹) and amide region (2800-3050 cm⁻¹)
    """
    
    def __init__(self):
        self.name = "fingerprint_amide"
        self.ranges = [(900, 1800), (2800, 3050)]
    
    def truncate(self, X: np.ndarray, wavenumbers: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Truncates data to fingerprint and amide regions
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Tuple containing truncated spectra matrix and truncated wavenumbers array
        """
        mask = np.zeros(len(wavenumbers), dtype=bool)
        
        for min_wav, max_wav in self.ranges:
            mask |= ((wavenumbers >= min_wav) & (wavenumbers <= max_wav))
        
        X_truncated = X[:, mask]
        wavenumbers_truncated = wavenumbers[mask]
        
        return X_truncated, wavenumbers_truncated


def create_truncator(method: str) -> FTIRTruncator:
    """
    Factory function to create truncator instances
    
    Args:
        method: Truncation method name
            - 'fingerprint': Keep only fingerprint region (900-1800 cm⁻¹)
            - 'fingerprint_amide': Keep fingerprint and amide regions (900-1800, 2800-3050 cm⁻¹)
    
    Returns:
        FTIRTruncator instance
        
    Raises:
        ValueError: If method is not supported
    """
    if method == 'fingerprint':
        return FingerprintTruncator()
    elif method == 'fingerprint_amide':
        return FingerprintAmideTruncator()
    else:
        available_methods = ['fingerprint', 'fingerprint_amide']
        raise ValueError(
            f"Truncation method '{method}' is not supported. "
            f"Available methods: {', '.join(available_methods)}"
        )


class TruncatorFactory:
    """
    Factory class for creating truncator instances
    """
    
    @staticmethod
    def create_truncator(method: str, **kwargs) -> FTIRTruncator:
        """
        Factory method to create truncator instances
        
        Args:
            method: Truncation method name
            **kwargs: Additional parameters (not used for truncation)
        
        Returns:
            FTIRTruncator instance
            
        Raises:
            ValueError: If method is not supported
        """
        if method == 'fingerprint':
            return FingerprintTruncator()
        elif method == 'fingerprint_amide':
            return FingerprintAmideTruncator()
        else:
            available_methods = ['fingerprint', 'fingerprint_amide']
            raise ValueError(
                f"Truncation method '{method}' is not supported. "
                f"Available methods: {', '.join(available_methods)}"
            )


def get_available_truncation_methods() -> List[str]:
    """
    Get list of available truncation methods
    
    Returns:
        List of available truncation method names
    """
    return ['fingerprint', 'fingerprint_amide']
