"""
Main FTIR preprocessing pipeline
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from ..preprocessing.baseline import BaselineCorrectorFactory
from ..preprocessing.normalization import NormalizerFactory
from ..preprocessing.smoothing import SmootherFactory
from ..preprocessing.derivatives import DerivativeCalculator
from ..preprocessing.truncation import TruncatorFactory


class FTIRPipeline:
    """
    Main pipeline for preprocessing FTIR spectra
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the pipeline
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.steps = []
        self.processed_data = None
        self.processing_history = []
        
    def add_step(self, step_type: str, method: str, **kwargs):
        """
        Adds a step to the pipeline
        
        Args:
            step_type: Step type ('baseline', 'normalization', 'smoothing', 'derivative', 'truncation')
            method: Specific method
            **kwargs: Additional parameters
        """
        step = {
            'type': step_type,
            'method': method,
            'parameters': kwargs,
            'name': f"{step_type}_{method}"
        }
        self.steps.append(step)
        
    def set_steps_from_order(self, order: List[str], **step_configs):
        """
        Defines steps based on a specific order
        
        Args:
            order: List with step order
            **step_configs: Configurations for each step type
        """
        self.steps = []
        
        for step_type in order:
            if step_type in step_configs:
                config = step_configs[step_type]
                self.add_step(step_type, config['method'], **config.get('parameters', {}))
            else:
                # Adds with default configuration
                self.add_step(step_type, 'none')
    
    def process(self, X: np.ndarray, wavenumbers: np.ndarray):
        """
        Executes the complete pipeline
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            
        Returns:
            If assigned to single variable: Matrix of processed spectra
            If assigned to two variables: Tuple of (processed spectra, processed wavenumbers)
        """
        X_proc = X.copy()
        wavenumbers_proc = wavenumbers.copy()
        
        for i, step in enumerate(self.steps):
            try:
                if step['type'] == 'truncation':
                    X_proc, wavenumbers_proc = self._apply_step(X_proc, wavenumbers_proc, step)
                else:
                    X_proc = self._apply_step(X_proc, wavenumbers_proc, step)
                self.processing_history.append({
                    'step': i,
                    'step_info': step,
                    'data_shape': X_proc.shape,
                    'status': 'success'
                })
            except Exception as e:
                self.processing_history.append({
                    'step': i,
                    'step_info': step,
                    'error': str(e),
                    'status': 'error'
                })
                raise RuntimeError(f"Error in step {i} ({step['name']}): {e}")
        
        self.processed_data = X_proc
        return X_proc, wavenumbers_proc
    
    def _apply_step(self, X: np.ndarray, wavenumbers: np.ndarray, step: Dict[str, Any]):
        """
        Applies a specific step
        
        Args:
            X: Spectra matrix
            wavenumbers: Wavenumbers array
            step: Step configuration
            
        Returns:
            Matrix of processed spectra
        """
        step_type = step['type']
        method = step['method']
        params = step.get('parameters', {})
        
        if method == 'none':
            return X
        
        if step_type == 'baseline':
            corrector = BaselineCorrectorFactory.create_corrector(method, **params)
            return corrector.correct(X, wavenumbers)
            
        elif step_type == 'normalization':
            normalizer = NormalizerFactory.create_normalizer(method, **params)
            return normalizer.normalize(X, wavenumbers)
            
        elif step_type == 'smoothing':
            smoother = SmootherFactory.create_smoother(method, **params)
            return smoother.smooth(X, wavenumbers)
            
        elif step_type == 'derivative':
            if params.get('order', 0) > 0:
                calculator = DerivativeCalculator(
                    window_length=params.get('window_length', 11),
                    polyorder=params.get('polyorder', 2)
                )
                return calculator.calculate_derivative(X, wavenumbers, params.get('order', 1))
            return X
            
        elif step_type == 'truncation':
            truncator = TruncatorFactory.create_truncator(method)
            return truncator.truncate(X, wavenumbers)
            
        else:
            raise ValueError(f"Unsupported step type: {step_type}")
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """
        Returns a pipeline summary
        
        Returns:
            Dictionary with pipeline information
        """
        return {
            'n_steps': len(self.steps),
            'steps': [step['name'] for step in self.steps],
            'processing_history': self.processing_history,
            'data_processed': self.processed_data is not None
        }
    
    def reset(self):
        """Resets the pipeline"""
        self.steps = []
        self.processed_data = None
        self.processing_history = []
    
    def save_pipeline(self, filepath: str):
        """
        Saves the pipeline configuration
        
        Args:
            filepath: Path to save
        """
        import json
        pipeline_config = {
            'steps': self.steps,
            'config': self.config
        }
        
        with open(filepath, 'w') as f:
            json.dump(pipeline_config, f, indent=2)
    
    @classmethod
    def load_pipeline(cls, filepath: str):
        """
        Loads a saved pipeline
        
        Args:
            filepath: File path
            
        Returns:
            Loaded pipeline instance
        """
        import json
        
        with open(filepath, 'r') as f:
            pipeline_config = json.load(f)
        
        pipeline = cls(config=pipeline_config.get('config', {}))
        pipeline.steps = pipeline_config.get('steps', [])
        
        return pipeline


class PipelineBuilder:
    """
    Pipeline builder using Builder pattern
    """
    
    def __init__(self):
        self.pipeline = FTIRPipeline()
    
    def add_baseline(self, method: str = 'none', **kwargs):
        """Adds baseline step"""
        self.pipeline.add_step('baseline', method, **kwargs)
        return self
    
    def add_normalization(self, method: str = 'none', **kwargs):
        """Adds normalization step"""
        self.pipeline.add_step('normalization', method, **kwargs)
        return self
    
    def add_smoothing(self, method: str = 'none', **kwargs):
        """Adds smoothing step"""
        self.pipeline.add_step('smoothing', method, **kwargs)
        return self
    
    def add_derivative(self, method: str = 'none', order: int = 0, **kwargs):
        """Adds derivative step"""
        self.pipeline.add_step('derivative', method, order=order, **kwargs)
        return self
    
    def add_truncation(self, method: str = 'fingerprint', **kwargs):
        """Adds truncation step"""
        self.pipeline.add_step('truncation', method, **kwargs)
        return self
    
    def build(self) -> FTIRPipeline:
        """Builds and returns the pipeline"""
        return self.pipeline


# Convenience function to create pipeline from order
def create_pipeline_from_order(order: List[str], **step_configs) -> FTIRPipeline:
    """
    Creates a pipeline from a specific order
    
    Args:
        order: List with step order
        **step_configs: Configurations for each step type
        
    Returns:
        Configured pipeline
    """
    pipeline = FTIRPipeline()
    pipeline.set_steps_from_order(order, **step_configs)
    return pipeline 