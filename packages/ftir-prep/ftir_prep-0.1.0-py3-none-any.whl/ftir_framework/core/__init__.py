"""
Módulo core do framework FTIR
"""

from .pipeline import FTIRPipeline, PipelineBuilder, create_pipeline_from_order
from .evaluator import PipelineEvaluator
from .explainer import FTIRExplainer

__all__ = [
    'FTIRPipeline',
    'PipelineBuilder',
    'create_pipeline_from_order',
    'PipelineEvaluator',
    'FTIRExplainer'
] 