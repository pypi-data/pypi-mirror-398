"""
Module for calculating derivatives of FTIR spectra
"""

import numpy as np
from typing import Optional
from .smoothing import SavitzkyGolaySmoother


class DerivativeCalculator:
    """
    Derivative calculator using Savitzky-Golay filter
    """
    
    def __init__(self, window_length: int = 11, polyorder: int = 2):
        """
        Initializes the calculator
        
        Args:
            window_length: Window length (must be odd)
            polyorder: Polynomial order
        """
        self.window_length = window_length
        self.polyorder = polyorder
    
    def calculate_derivative(self, X: np.ndarray, wavenumbers: np.ndarray, 
                           order: int = 1) -> np.ndarray:
        """
        Calculates the derivative of specified order
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            order: Derivative order (0, 1, 2)
            
        Returns:
            Matrix of derived spectra
        """
        if order == 0:
            return X
        
        if order < 0 or order > 2:
            raise ValueError("Derivative order must be 0, 1 or 2")
        
        smoother = SavitzkyGolaySmoother(
            window_length=self.window_length,
            polyorder=self.polyorder,
            deriv=order
        )
        
        return smoother.smooth(X, wavenumbers)
    
    def first_derivative(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Calculates the first derivative
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of first derivatives
        """
        return self.calculate_derivative(X, wavenumbers, order=1)
    
    def second_derivative(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Calculates the second derivative
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of second derivatives
        """
        return self.calculate_derivative(X, wavenumbers, order=2)


# Convenience function for compatibility with existing code
def apply_derivative(X: np.ndarray, wavenumbers: np.ndarray, 
                    order: int = 1, window_length: int = 11, 
                    polyorder: int = 2) -> np.ndarray:
    """
    Convenience function for applying derivatives
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        order: Derivative order
        window_length: Window length
        polyorder: Polynomial order
        
    Returns:
        Matrix of derived spectra
    """
    calculator = DerivativeCalculator(window_length, polyorder)
    return calculator.calculate_derivative(X, wavenumbers, order) 