"""
Module for smoothing techniques of FTIR spectra
"""

import numpy as np
import rampy as rp
import pywt
from statsmodels.nonparametric.smoothers_lowess import lowess
from typing import Optional
from abc import ABC, abstractmethod


class Smoother(ABC):
    """
    Abstract class for smoothers
    """
    
    @abstractmethod
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies smoothing
        
        Args:
            X: Spectra matrix (n_samples, n_features)
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        pass


class SavitzkyGolaySmoother(Smoother):
    """
    Savitzky-Golay smoother
    """
    
    def __init__(self, window_length: int = 11, polyorder: int = 2, deriv: int = 0):
        """
        Initializes the smoother
        
        Args:
            window_length: Window length (must be odd)
            polyorder: Polynomial order
            deriv: Derivative order
        """
        self.window_length = window_length
        self.polyorder = polyorder
        self.deriv = deriv
        self.name = f"savgol_w{window_length}_p{polyorder}_d{deriv}"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies Savitzky-Golay smoothing
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        # Ensure wavenumbers are in ascending order for correct smoothing
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        filtered = []
        
        for spectrum in X_reversed:
            filtered_spectrum = rp.smooth(
                wavenumbers_asc, 
                spectrum, 
                method="savgol",
                window_length=self.window_length, 
                polyorder=self.polyorder, 
                deriv=self.deriv
            )
            filtered.append(filtered_spectrum)
        
        filtered_array = np.array(filtered)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            filtered_array = filtered_array[:, ::-1]
            
        return filtered_array


class WaveletSmoother(Smoother):
    """
    Wavelet-based smoother
    """
    
    def __init__(self, wavelet: str = 'db4', level: int = 1, mode: str = 'soft'):
        """
        Initializes the smoother
        
        Args:
            wavelet: Wavelet type ('db2', 'db3', 'db4', etc.)
            level: Decomposition level
            mode: Thresholding mode ('soft', 'hard')
        """
        self.wavelet = wavelet
        self.level = level
        self.mode = mode
        self.name = f"wavelet_{wavelet}_l{level}_{mode}"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies wavelet smoothing
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        denoised = []
        
        for spectrum in X:
            coeffs = pywt.wavedec(spectrum, self.wavelet, level=self.level)
            sigma = np.median(np.abs(coeffs[-self.level])) / 0.6745
            uthresh = sigma * np.sqrt(2 * np.log(len(spectrum)))
            coeffs_thresh = [pywt.threshold(c, value=uthresh, mode=self.mode) for c in coeffs]
            rec = pywt.waverec(coeffs_thresh, self.wavelet)
            denoised.append(rec[:len(spectrum)]) 
            
        return np.array(denoised)


class LocalPolynomialSmoother(Smoother):
    """
    Local polynomial smoother (LOWESS)
    """
    
    def __init__(self, bandwidth: int = 3, iterations: int = 0):
        """
        Initializes the smoother
        
        Args:
            bandwidth: Bandwidth (1-6)
            iterations: Number of iterations
        """
        self.bandwidth = bandwidth
        self.iterations = iterations
        self.name = f"local_poly_b{bandwidth}_i{iterations}"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies local polynomial smoothing
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        smoothed = []
        frac = self.bandwidth / (wavenumbers.max() - wavenumbers.min())
        
        for spectrum in X:
            smoothed_spec = lowess(
                spectrum, 
                wavenumbers, 
                frac=frac, 
                it=self.iterations, 
                return_sorted=False
            )
            smoothed.append(smoothed_spec)
            
        return np.array(smoothed)


class WhittakerSmoother(Smoother):
    """
    Whittaker smoother
    """
    
    def __init__(self, Lambda: float = 1e5, d: int = 2):
        """
        Initializes the smoother
        
        Args:
            Lambda: Smoothing parameter (higher = smoother)
            d: Difference order
        """
        self.Lambda = Lambda
        self.d = d
        self.name = f"whittaker_lambda_{Lambda}_d_{d}"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies Whittaker smoothing using rampy
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        # Ensure wavenumbers are in ascending order for correct smoothing
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        filtered = []
        
        for spectrum in X_reversed:
            filtered_spectrum = rp.smooth(
                wavenumbers_asc, 
                spectrum, 
                method="whittaker",
                Lambda=self.Lambda,
                d=self.d
            )
            filtered.append(filtered_spectrum)
        
        filtered_array = np.array(filtered)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            filtered_array = filtered_array[:, ::-1]
            
        return filtered_array


class GCVSplineSmoother(Smoother):
    """
    GCV Spline smoother using rampy with automatic parameter optimization via cross-validation
    """
    
    def __init__(self):
        """
        Initializes the smoother
        
        Note:
            The smoothing parameter is automatically optimized via Generalized Cross-Validation
        """
        self.name = "gcv_spline"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies GCV Spline smoothing using rampy
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        # Ensure wavenumbers are in ascending order for correct smoothing
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        filtered = []
        
        for spectrum in X_reversed:
            filtered_spectrum = rp.smooth(
                wavenumbers_asc, 
                spectrum, 
                method="GCVSmoothedNSpline"
            )
            filtered.append(filtered_spectrum)
        
        filtered_array = np.array(filtered)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            filtered_array = filtered_array[:, ::-1]
            
        return filtered_array


class MovingAverageSmoother(Smoother):
    """
    Moving average smoother using rampy
    """
    
    def __init__(self, window_length: int = 5):
        """
        Initializes the smoother
        
        Args:
            window_length: Length of moving average window
        """
        self.window_length = window_length
        self.name = f"moving_average_w{window_length}"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies moving average smoothing using rampy
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        # Ensure wavenumbers are in ascending order for correct smoothing
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        filtered = []
        
        for spectrum in X_reversed:
            filtered_spectrum = rp.smooth(
                wavenumbers_asc, 
                spectrum, 
                method="flat",
                window_length=self.window_length
            )
            filtered.append(filtered_spectrum)
        
        filtered_array = np.array(filtered)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            filtered_array = filtered_array[:, ::-1]
            
        return filtered_array


class HanningSmoother(Smoother):
    """
    Hanning window smoother
    """
    
    def __init__(self, window_length: int = 5):
        """
        Initializes the smoother
        
        Args:
            window_length: Length of Hanning window
        """
        self.window_length = window_length
        self.name = f"hanning_w{window_length}"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Applies Hanning window smoothing
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Matrix of smoothed spectra
        """
        # Ensure wavenumbers are in ascending order for correct smoothing
        # FTIR data often has wavenumbers in descending order (high to low)
        if wavenumbers[0] > wavenumbers[-1]:
            # Wavenumbers are in descending order, need to reverse both arrays
            wavenumbers_asc = wavenumbers[::-1]
            X_reversed = X[:, ::-1]
        else:
            # Wavenumbers are already in ascending order
            wavenumbers_asc = wavenumbers
            X_reversed = X
        
        filtered = []
        
        for spectrum in X_reversed:
            filtered_spectrum = rp.smooth(
                wavenumbers_asc, 
                spectrum, 
                method="hanning",
                window_length=self.window_length
            )
            filtered.append(filtered_spectrum)
        
        filtered_array = np.array(filtered)
        
        # If we reversed the data, reverse it back to maintain original order
        if wavenumbers[0] > wavenumbers[-1]:
            filtered_array = filtered_array[:, ::-1]
            
        return filtered_array


class NoOpSmoother(Smoother):
    """
    Smoother that makes no modifications (method 'none')
    """
    
    def __init__(self):
        self.name = "none"
    
    def smooth(self, X: np.ndarray, wavenumbers: np.ndarray) -> np.ndarray:
        """
        Does not modify the data
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            Unchanged spectra matrix
        """
        return X.copy()


class SmootherFactory:
    """
    Factory for creating smoothers
    """
    
    @staticmethod
    def create_smoother(method: str, **kwargs) -> Smoother:
        """
        Creates a smoother based on the specified method
        
        Args:
            method: Smoothing method ('savgol', 'wavelet', 'local_poly', 'whittaker', 'gcv_spline', 'moving_average', 'hanning', 'none')
            **kwargs: Additional parameters for the smoother (gcv_spline uses automatic parameter optimization)
            
        Returns:
            Smoother instance
        """
        if method == "savgol":
            window_length = kwargs.get('window_length', 11)
            polyorder = kwargs.get('polyorder', 2)
            deriv = kwargs.get('deriv', 0)
            return SavitzkyGolaySmoother(window_length, polyorder, deriv)
        elif method == "wavelet":
            wavelet = kwargs.get('wavelet', 'db4')
            level = kwargs.get('level', 1)
            mode = kwargs.get('mode', 'soft')
            return WaveletSmoother(wavelet, level, mode)
        elif method == "local_poly":
            bandwidth = kwargs.get('bandwidth', 3)
            iterations = kwargs.get('iterations', 0)
            return LocalPolynomialSmoother(bandwidth, iterations)
        elif method == "whittaker":
            Lambda = kwargs.get('Lambda', 1e5)
            d = kwargs.get('d', 2)
            return WhittakerSmoother(Lambda, d)
        elif method == "gcv_spline":
            return GCVSplineSmoother()
        elif method == "moving_average":
            window_length = kwargs.get('window_length', 5)
            return MovingAverageSmoother(window_length)
        elif method == "hanning":
            window_length = kwargs.get('window_length', 5)
            return HanningSmoother(window_length)
        elif method == "none":
            return NoOpSmoother()
        else:
            raise ValueError(f"Unsupported smoothing method: {method}")


# Convenience functions for compatibility with existing code
def sg_filter(X: np.ndarray, wavenumbers: np.ndarray, window_length: int = 11, 
              polyorder: int = 2, deriv: int = 0) -> np.ndarray:
    """
    Convenience function for Savitzky-Golay filter
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        window_length: Window length
        polyorder: Polynomial order
        deriv: Derivative order
        
    Returns:
        Matrix of filtered spectra
    """
    smoother = SavitzkyGolaySmoother(window_length, polyorder, deriv)
    return smoother.smooth(X, wavenumbers)


def wavelet_denoising(X: np.ndarray, wavenumbers: Optional[np.ndarray] = None, 
                      wavelet: str = 'db4', level: int = 1, mode: str = 'soft') -> np.ndarray:
    """
    Convenience function for wavelet denoising
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array (not used)
        wavelet: Wavelet type
        level: Decomposition level
        mode: Thresholding mode
        
    Returns:
        Matrix of denoised spectra
    """
    smoother = WaveletSmoother(wavelet, level, mode)
    return smoother.smooth(X, wavenumbers)


def local_polynomial(X: np.ndarray, wavenumbers: np.ndarray, bandwidth: int = 3, 
                     iterations: int = 0) -> np.ndarray:
    """
    Convenience function for local polynomial smoothing
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        bandwidth: Bandwidth
        iterations: Number of iterations
        
    Returns:
        Matrix of smoothed spectra
    """
    smoother = LocalPolynomialSmoother(bandwidth, iterations)
    return smoother.smooth(X, wavenumbers)


def whittaker_smooth(X: np.ndarray, wavenumbers: np.ndarray, Lambda: float = 1e5, d: int = 2) -> np.ndarray:
    """
    Convenience function for Whittaker smoothing
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        Lambda: Smoothing parameter (higher = smoother)
        d: Difference order
        
    Returns:
        Matrix of smoothed spectra
    """
    smoother = WhittakerSmoother(Lambda, d)
    return smoother.smooth(X, wavenumbers)


def gcv_spline_smooth(X: np.ndarray, wavenumbers: np.ndarray, s: float = 2.0) -> np.ndarray:
    """
    Convenience function for GCV Spline smoothing
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        s: Smoothing parameter
        
    Returns:
        Matrix of smoothed spectra
    """
    smoother = GCVSplineSmoother(s)
    return smoother.smooth(X, wavenumbers)


def moving_average_smooth(X: np.ndarray, wavenumbers: np.ndarray, window_length: int = 5) -> np.ndarray:
    """
    Convenience function for moving average smoothing
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        window_length: Length of moving average window
        
    Returns:
        Matrix of smoothed spectra
    """
    smoother = MovingAverageSmoother(window_length)
    return smoother.smooth(X, wavenumbers)


def hanning_smooth(X: np.ndarray, wavenumbers: np.ndarray, window_length: int = 5) -> np.ndarray:
    """
    Convenience function for Hanning window smoothing
    
    Args:
        X: Spectra matrix
        wavenumbers: Wavenumbers array
        window_length: Length of Hanning window
        
    Returns:
        Matrix of smoothed spectra
    """
    smoother = HanningSmoother(window_length)
    return smoother.smooth(X, wavenumbers) 