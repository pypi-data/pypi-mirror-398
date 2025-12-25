"""
Module for baseline correction techniques in FTIR spectra
"""

import numpy as np
import rampy as rp
from abc import ABC, abstractmethod


class BaselineCorrector(ABC):
    """
    Abstract class for baseline correctors
    """
    
    @abstractmethod
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction
        
        Args:
            X: Spectra matrix (n_samples, n_features)
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        pass


class NoOpBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector that makes no modifications (method 'none')
    """
    
    def __init__(self):
        self.name = "none"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Does not modify the data
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Unchanged spectra matrix
        """
        return X.copy()


class RubberbandBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using rubberband method
    """
    
    def __init__(self):
        self.name = "rubberband"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using rubberband
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        corrected = []
        
        for spectrum in X:
            corrected_signal, _ = rp.baseline(wavenumbers, spectrum, method="rubberband")
            corrected.append(np.squeeze(corrected_signal))
            
        return np.array(corrected)


class PolynomialBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using polynomial method
    """
    
    def __init__(self, polynomial_order: int = 2):
        """
        Initializes the corrector
        
        Args:
            polynomial_order: Polynomial order (default: 2)
        """
        self.polynomial_order = polynomial_order
        self.name = f"polynomial_order_{polynomial_order}"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using polynomial
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        corrected = []
        
        for spectrum in X:
            corrected_signal, baseline = rp.baseline(
                wavenumbers, 
                spectrum, 
                method="poly", 
                polynomial_order=self.polynomial_order
            )
            corrected.append(np.squeeze(corrected_signal))
            
        return np.array(corrected)


class WhittakerBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using Whittaker smoothing method
    """
    
    def __init__(self, lam: float = 1e5):
        """
        Initializes the corrector
        
        Args:
            lam: Smoothness parameter (default: 1e5)
        """
        self.lam = lam
        self.name = f"whittaker_lam_{lam}"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using Whittaker smoothing
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        # Ensure wavenumbers are in ascending order for correct baseline calculation
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        corrected = []
        
        for spectrum in X_reversed:
            corrected_signal, _ = rp.baseline(
                wavenumbers_asc, 
                spectrum, 
                method="whittaker", 
                lam=self.lam
            )
            corrected.append(np.squeeze(corrected_signal))
        
        corrected_array = np.array(corrected)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            corrected_array = corrected_array[:, ::-1]
            
        return corrected_array


class ALSBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using Asymmetric Least Squares (ALS) method
    """
    
    def __init__(self, lam: float = 1e5, p: float = 0.01, niter: int = 10):
        """
        Initializes the corrector
        
        Args:
            lam: Smoothness parameter (default: 1e5)
            p: Weighting parameter, between 0.001 and 0.1 (default: 0.01)
            niter: Number of iterations (default: 10)
        """
        self.lam = lam
        self.p = p
        self.niter = niter
        self.name = f"als_lam_{lam}_p_{p}_niter_{niter}"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using ALS
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        # Ensure wavenumbers are in ascending order for correct baseline calculation
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        corrected = []
        
        for spectrum in X_reversed:
            corrected_signal, _ = rp.baseline(
                wavenumbers_asc, 
                spectrum, 
                method="als", 
                lam=self.lam,
                p=self.p,
                niter=self.niter
            )
            corrected.append(np.squeeze(corrected_signal))
        
        corrected_array = np.array(corrected)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            corrected_array = corrected_array[:, ::-1]
            
        return corrected_array


class ArPLSBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using Asymmetrically Reweighted Penalized Least Squares (arPLS) method
    """
    
    def __init__(self, lam: float = 1e5, ratio: float = 0.01):
        """
        Initializes the corrector
        
        Args:
            lam: Smoothness parameter (default: 1e5)
            ratio: Convergence ratio parameter (default: 0.01)
        """
        self.lam = lam
        self.ratio = ratio
        self.name = f"arpls_lam_{lam}_ratio_{ratio}"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using arPLS
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        # Ensure wavenumbers are in ascending order for correct baseline calculation
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        corrected = []
        
        for spectrum in X_reversed:
            corrected_signal, _ = rp.baseline(
                wavenumbers_asc, 
                spectrum,   
                method="arPLS", 
                lam=self.lam,
                ratio=self.ratio
            )
            corrected.append(np.squeeze(corrected_signal))
        
        corrected_array = np.array(corrected)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            corrected_array = corrected_array[:, ::-1]
            
        return corrected_array


class DrPLSBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using Doubly Reweighted Penalized Least Squares (drPLS) method
    """
    
    def __init__(self, niter: int = 100, lam: float = 1e5, eta: float = 0.5, ratio: float = 0.001):
        """
        Initializes the corrector
        
        Args:
            niter: Number of iterations (default: 100)
            lam: Smoothness parameter (default: 1e5)
            eta: Roughness parameter, between 0 and 1 (default: 0.5)
            ratio: Convergence ratio parameter (default: 0.001)
        """
        self.niter = niter
        self.lam = lam
        self.eta = eta
        self.ratio = ratio
        self.name = f"drpls_niter_{niter}_lam_{lam}_eta_{eta}_ratio_{ratio}"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using drPLS
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        # Ensure wavenumbers are in ascending order for correct baseline calculation
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        corrected = []
        
        for spectrum in X_reversed:
            corrected_signal, _ = rp.baseline(
                wavenumbers_asc, 
                spectrum, 
                method="drPLS", 
                niter=self.niter,
                lam=self.lam,
                eta=self.eta,
                ratio=self.ratio
            )
            corrected.append(np.squeeze(corrected_signal))
        
        corrected_array = np.array(corrected)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            corrected_array = corrected_array[:, ::-1]
            
        return corrected_array


class GCVSplineBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using Generalized Cross-Validated Spline (GCVSpline) method
    """
    
    def __init__(self, s: float = 2.0):
        """
        Initializes the corrector
        
        Args:
            s: Spline smoothing coefficient (default: 2.0)
        """
        self.s = s
        self.name = f"gcvspline_s_{s}"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using GCVSpline
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        # Ensure wavenumbers are in ascending order for correct baseline calculation
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        corrected = []
        
        for spectrum in X_reversed:
            corrected_signal, _ = rp.baseline(
                wavenumbers_asc, 
                spectrum, 
                method="gcvspline", 
                s=self.s
            )
            corrected.append(np.squeeze(corrected_signal))
        
        corrected_array = np.array(corrected)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            corrected_array = corrected_array[:, ::-1]
            
        return corrected_array


class GaussianProcessBaselineCorrector(BaselineCorrector):
    """
    Baseline corrector using Gaussian Process method with rational quadratic kernel
    """
    
    def __init__(self):
        """
        Initializes the corrector
        """
        self.name = "gaussian_process"
    
    def correct(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies baseline correction using Gaussian Process
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of corrected spectra
        """
        # Ensure wavenumbers are in ascending order for correct baseline calculation
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        corrected = []
        
        for spectrum in X_reversed:
            corrected_signal, _ = rp.baseline(
                wavenumbers_asc, 
                spectrum, 
                method="GP"
            )
            corrected.append(np.squeeze(corrected_signal))
        
        corrected_array = np.array(corrected)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            corrected_array = corrected_array[:, ::-1]
            
        return corrected_array


class BaselineCorrectorFactory:
    """
    Factory for creating baseline correctors
    """
    
    @staticmethod
    def create_corrector(method: str, **kwargs) -> BaselineCorrector:
        """
        Creates a baseline corrector based on the specified method
        
        Args:
            method: Correction method ('rubberband', 'polynomial', 'whittaker', 'als', 'arpls', 'drpls', 'gcv_spline', 'gaussian_process', 'none')
            **kwargs: Additional parameters for the corrector
            
        Returns:
            Corrector instance
        """
        if method == "rubberband":
            return RubberbandBaselineCorrector()
        elif method == "polynomial":
            order = kwargs.get('polynomial_order', 2)
            return PolynomialBaselineCorrector(polynomial_order=order)
        elif method == "whittaker":
            lam = kwargs.get('lam', 1e5)
            return WhittakerBaselineCorrector(lam=lam)
        elif method == "als":
            lam = kwargs.get('lam', 1e5)
            p = kwargs.get('p', 0.01)
            niter = kwargs.get('niter', 10)
            return ALSBaselineCorrector(lam=lam, p=p, niter=niter)
        elif method == "arpls":
            lam = kwargs.get('lam', 1e5)
            ratio = kwargs.get('ratio', 0.01)
            return ArPLSBaselineCorrector(lam=lam, ratio=ratio)
        elif method == "drpls":
            niter = kwargs.get('niter', 100)
            lam = kwargs.get('lam', 1e5)
            eta = kwargs.get('eta', 0.5)
            ratio = kwargs.get('ratio', 0.001)
            return DrPLSBaselineCorrector(niter=niter, lam=lam, eta=eta, ratio=ratio)
        elif method == "gcv_spline":
            s = kwargs.get('s', 2.0)
            return GCVSplineBaselineCorrector(s=s)
        elif method == "gaussian_process":
            return GaussianProcessBaselineCorrector()
        elif method == "none":
            return NoOpBaselineCorrector()
        else:
            raise ValueError(f"Unsupported baseline method: {method}")


# Convenience functions for compatibility with existing code
def baseline_rubberband(X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
    """
    Convenience function for rubberband baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = RubberbandBaselineCorrector()
    return corrector.correct(X, wavenumbers)


def baseline_polynomial(X: np.ndarray, wavenumbers: np.ndarray, order: int = 2) -> np.ndarray:
    """
    Convenience function for polynomial baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        order: Polynomial order
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = PolynomialBaselineCorrector(polynomial_order=order)
    return corrector.correct(X, wavenumbers)


def baseline_whittaker(X: np.ndarray, wavenumbers: np.ndarray, lam: float = 1e5) -> np.ndarray:
    """
    Convenience function for Whittaker baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        lam: Smoothness parameter
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = WhittakerBaselineCorrector(lam=lam)
    return corrector.correct(X, wavenumbers)


def baseline_als(X: np.ndarray, wavenumbers: np.ndarray, lam: float = 1e5, p: float = 0.01, niter: int = 10) -> np.ndarray:
    """
    Convenience function for ALS baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        lam: Smoothness parameter
        p: Weighting parameter
        niter: Number of iterations
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = ALSBaselineCorrector(lam=lam, p=p, niter=niter)
    return corrector.correct(X, wavenumbers)


def baseline_arpls(X: np.ndarray, wavenumbers: np.ndarray, lam: float = 1e5, ratio: float = 0.01) -> np.ndarray:
    """
    Convenience function for arPLS baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        lam: Smoothness parameter
        ratio: Convergence ratio parameter
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = ArPLSBaselineCorrector(lam=lam, ratio=ratio)
    return corrector.correct(X, wavenumbers)


def baseline_drpls(X: np.ndarray, wavenumbers: np.ndarray, niter: int = 100, lam: float = 1e5, eta: float = 0.5, ratio: float = 0.001) -> np.ndarray:
    """
    Convenience function for drPLS baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        niter: Number of iterations
        lam: Smoothness parameter
        eta: Roughness parameter
        ratio: Convergence ratio parameter
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = DrPLSBaselineCorrector(niter=niter, lam=lam, eta=eta, ratio=ratio)
    return corrector.correct(X, wavenumbers)


def baseline_gcvspline(X: np.ndarray, wavenumbers: np.ndarray, s: float = 2.0) -> np.ndarray:
    """
    Convenience function for GCVSpline baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        s: Spline smoothing coefficient
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = GCVSplineBaselineCorrector(s=s)
    return corrector.correct(X, wavenumbers)


def baseline_gaussian_process(X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
    """
    Convenience function for Gaussian Process baseline correction
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        
    Returns:
        Matrix of corrected spectra
    """
    corrector = GaussianProcessBaselineCorrector()
    return corrector.correct(X, wavenumbers) 