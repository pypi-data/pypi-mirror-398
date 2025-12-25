"""
Module for loading and preparing FTIR data
"""

import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FTIRDataLoader:
    """
    Class for loading and preparing dat type FTIR data
    """
    
    def __init__(self, data_path: str, wavenumbers_path: str):
        """
        Initializes the data loader
        
        Args:
            data_path: Path to the dat type data file (required)
            wavenumbers_path: Path to the dat type wavenumbers file (required)
            
        Raises:
            ValueError: If data_path or wavenumbers_path are None, empty, or not .dat files
        """
        if not data_path:
            raise ValueError("data_path is required and cannot be None or empty")
        if not wavenumbers_path:
            raise ValueError("wavenumbers_path is required and cannot be None or empty")
            
        if not data_path.lower().endswith('.dat'):
            raise ValueError(f"Data file must be in .dat format. Got: {data_path}")
        if not wavenumbers_path.lower().endswith('.dat'):
            raise ValueError(f"Wavenumbers file must be in .dat format. Got: {wavenumbers_path}")
            
        self.data_path = data_path
        self.wavenumbers_path = wavenumbers_path
        self.X = None
        self.y = None
        self.wavenumbers = None
        self.groups = None
        
    def load_data(self, slice_size: int = 1, data_path: Optional[str] = None, wavenumbers_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Loads FTIR data
        
        Args:
            slice_size: Step size for slicing data (default: 1)
            data_path: Path to the data file (optional, must be .dat format)
            wavenumbers_path: Path to the wavenumbers file (optional, must be .dat format)
            
        Returns:
            Tuple containing X, y and wavenumbers
            
        Raises:
            ValueError: If paths are missing or files are not in .dat format
        """
        if data_path:
            self.data_path = data_path
        if wavenumbers_path:
            self.wavenumbers_path = wavenumbers_path
            
        if not self.data_path or not self.wavenumbers_path:
            raise ValueError("Paths for data and wavenumbers must be provided")
            
        if not self.data_path.lower().endswith('.dat'):
            raise ValueError(f"Data file must be in .dat format. Got: {self.data_path}")
        if not self.wavenumbers_path.lower().endswith('.dat'):
            raise ValueError(f"Wavenumbers file must be in .dat format. Got: {self.wavenumbers_path}")
            
        self.X, self.y = self._load_ftir_data(self.data_path)
        self.X = self.X[::slice_size]
        self.y = self.y[::slice_size]
        self.wavenumbers = np.loadtxt(self.wavenumbers_path)
        
        return self.X, self.y, self.wavenumbers
    
    def _load_ftir_data(self, filename: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Loads FTIR data from text file
        
        Args:
            filename: File name
            
        Returns:
            Tuple containing X and y
        """
        try:
            data = np.loadtxt(filename)
            X = data[:, :-1]
            y = data[:, -1].astype(int)
            return X, y
        except Exception as e:
            raise ValueError(f"Error loading data: {e}")
    
    def create_groups(self, instances_per_group: int = 3) -> np.ndarray:
        """
        Creates groups for group-based cross-validation
        
        Args:
            instances_per_group: Number of instances per group (default: 3)
            
        Returns:
            Array with group identifiers
        """
        if self.X is None:
            raise ValueError("Data must be loaded before creating groups")
            
        num_instances = self.X.shape[0]
        num_groups = num_instances // instances_per_group
        
        self.groups = np.repeat(np.arange(num_groups), instances_per_group)
        return self.groups
    
    
    def get_data_summary(self) -> dict:
        """
        Returns a summary of loaded data
        
        Returns:
            Dictionary with data information
        """
        if self.X is None:
            return {"status": "No data loaded"}
            
        return {
            "n_samples": self.X.shape[0],
            "n_features": self.X.shape[1],
            "n_classes": len(np.unique(self.y)) if self.y is not None else 0,
            "wavelength_range": (float(self.wavenumbers.min()), float(self.wavenumbers.max())) if self.wavenumbers is not None else None,
            "groups_created": self.groups is not None
        }
    
    def save_data(self, output_path: str, format: str = 'csv'):
        """
        Saves processed data
        
        Args:
            output_path: Output path
            format: Output format ('numpy', 'csv', 'txt')
        """
        if self.X is None:
            raise ValueError("No data to save")
            
        output_path = Path(output_path)
        
        if format == 'csv':
            df = pd.DataFrame(self.X)
            df['target'] = self.y
            df.to_csv(output_path, index=False)
        elif format == 'txt':
            np.savetxt(output_path, np.column_stack([self.X, self.y]))
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        logger.info(f"Data saved to: {output_path}")