"""
Module for optimization using Optuna for FTIR preprocessing pipelines
"""

import optuna
import numpy as np
import itertools
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from ..core.pipeline import FTIRPipeline, create_pipeline_from_order
from ..core.evaluator import PipelineEvaluator
import logging

logger = logging.getLogger(__name__)


class OptimizationMetadata(dict):
    """
    Dictionary with additional methods for optimization metadata
    """
    
    def __init__(self, metadata: Dict[str, Any]):
        """
        Initialize with metadata dictionary
        
        Args:
            metadata: Dictionary containing optimization metadata
        """
        super().__init__(metadata)
        
        for key, value in metadata.items():
            setattr(self, key, value)
    
    def to_json(self, filepath: str = "optimization_metadata.json"):
        """
        Save metadata to JSON file
        
        Args:
            filepath: Path to save the metadata file
            
        Returns:
            Path of the saved file
        """
        filepath = Path(filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get the raw metadata dictionary
        
        Returns:
            Metadata dictionary
        """
        return dict(self)
    
    def _flatten_dict(self, d: dict, parent_key: str = '', sep: str = '_') -> dict:
        """
        Flatten nested dictionary
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for recursion
            sep: Separator between keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", item))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _prepare_dataframe(self) -> pd.DataFrame:
        """
        Prepare DataFrame with trials as rows and metadata as constant columns
        
        Returns:
            DataFrame ready for export
        """
        if 'all_trials' not in self:
            raise ValueError("No trials data found in metadata")
        
        trials_df = pd.DataFrame(self['all_trials'])
        
        if 'params' in trials_df.columns:
            params_df = pd.json_normalize(trials_df['params'])
            params_df.columns = [f"param_{col}" for col in params_df.columns]
            trials_df = pd.concat([trials_df.drop('params', axis=1), params_df], axis=1)
        
        for section, data in self.items():
            if section != 'all_trials':
                if isinstance(data, dict):
                    flattened = self._flatten_dict(data, parent_key=section)
                    for key, value in flattened.items():
                        if isinstance(value, (list, tuple, np.ndarray)):
                            trials_df[key] = str(value)
                        else:
                            trials_df[key] = value
                else:
                    if isinstance(data, (list, tuple, np.ndarray)):
                        trials_df[section] = str(data)
                    else:
                        trials_df[section] = data
        
        return trials_df
    
    def to_csv(self, filepath: str = "optimization_metadata.csv"):
        """
        Save metadata to csv file with each trial as a row
        
        Args:
            filepath: Path to save the metadata file
            
        Returns:
            Path of the saved file
        """
        df = self._prepare_dataframe()
        df.to_csv(filepath, index=False)
        return filepath
    
    def _prepare_dataframe(self) -> pd.DataFrame:
        """
        Prepare DataFrame with trials as rows, customized for different CV types
        
        Returns:
            DataFrame ready for export
        """
        is_nested_cv = self.get('cross_validation', {}).get('type') == 'NestedCV'
        
        if is_nested_cv:
            return self._prepare_nested_cv_dataframe()
        else:
            return self._prepare_regular_cv_dataframe()
    
    def _prepare_nested_cv_dataframe(self) -> pd.DataFrame:
        """
        Prepare DataFrame with trials as rows, customized for Nested CV
        
        Returns:
            DataFrame ready for export
        """
        rows = []
        
        outer_folds = self.get('results', {}).get('outer_folds', [])
        
        for fold in outer_folds:
            outer_fold_id = fold.get('outer_fold_id', 0)
            outer_score = fold.get('outer_test_score', 0)
            
            inner_trials = fold.get('inner_trials', [])
            for trial in inner_trials:
                pipeline_str = self._pipeline_to_string(trial.get('pipeline', []))
                rows.append({
                    'outer_fold_id': outer_fold_id,
                    'inner_trial_id': trial.get('trial_id', 0),
                    'pipeline': pipeline_str,
                    'score': trial.get('mean_inner_score', 0),
                    'cv_type': 'inner'
                })
            
            best_pipeline_str = self._pipeline_to_string(fold.get('best_pipeline', []))
            rows.append({
                'outer_fold_id': outer_fold_id,
                'inner_trial_id': 'N/A',
                'pipeline': best_pipeline_str,
                'score': outer_score,
                'cv_type': 'outer'
            })
        
        return pd.DataFrame(rows)
    
    def _prepare_regular_cv_dataframe(self) -> pd.DataFrame:
        """
        Prepare DataFrame with trials as rows
        
        Returns:
            DataFrame ready for export
        """
        rows = []
        
        trials = self.get('results', {}).get('trials', [])
        
        for trial in trials:
            pipeline_str = self._pipeline_to_string(trial.get('pipeline', []))
            rows.append({
                'trial_id': trial.get('trial_id', 0),
                'pipeline': pipeline_str,
                'score': trial.get('mean_cv_score', 0)
            })
        
        return pd.DataFrame(rows)
    
    def _pipeline_to_string(self, pipeline_steps: list) -> str:
        """
        Convert pipeline to string for metadata
        
        Args:
            pipeline_steps: Pipeline's steps list
            
        Returns:
            String representing the pipeline
        """
        if not pipeline_steps:
            return "Empty Pipeline"
        
        return str(pipeline_steps)

    def to_excel(self, filepath: str = "optimization_metadata.xlsx"):
        """
        Save metadata to xlsx file with each trial as a row
        
        Args:
            filepath: Path to save the metadata file
            
        Returns:
            Path of the saved file
        """
        df = self._prepare_dataframe()
        df.to_excel(filepath, index=False)
        return filepath

    def to_frame(self) -> pd.DataFrame:
        """
        Return the optimization metadata as a pandas DataFrame.
        The structure adapts to NestedCV or regular CV automatically.
        """
        return self._prepare_dataframe()


class OptunaPipelineOptimizer:
    """
    Pipeline optimizer using Optuna
    """
    
    def __init__(self, X: np.ndarray, y: np.ndarray, wavenumbers: np.ndarray, 
                 groups: Optional[np.ndarray] = None, evaluator: Optional[PipelineEvaluator] = None,
                 metric: str = 'balanced_accuracy',
                 available_methods: Optional[Dict[str, List[str]]] = None):
        """
        Initializes the optimizer
        
        Args:
            X: Spectra matrix
            y: Labels vector
            wavenumbers: Wavenumbers array
            groups: Groups for cross-validation
            evaluator: Custom evaluator
            metric: Metric to be used for optimization
                - accuracy
                - balanced_accuracy (default, recommended for imbalanced data)
                - f1, f1_macro, f1_micro, f1_weighted
                - precision, precision_macro, precision_micro, precision_weighted
                - recall, recall_macro, recall_micro, recall_weighted
                - roc_auc, roc_auc_ovo, roc_auc_ovr
                - neg_log_loss
                - jaccard
                - mcc (Matthews Correlation Coefficient - excellent for imbalanced data)
                - kappa (Cohen's Kappa Score - measures agreement beyond chance)
                - specificity (True Negative Rate - important for medical diagnosis)
                - sensitivity (True Positive Rate - synonym for recall)
                - npv (Negative Predictive Value - important for screening)
                - ppv (Positive Predictive Value - synonym for precision)
            available_methods: Dictionary specifying which methods to test for each technique
                - Format: {
                    'truncation': ['fingerprint', 'fingerprint_amide'],
                    'baseline': ['none', 'rubberband', 'polynomial', 'whittaker', 'als', 'drpls', 'gcv_spline'],
                    'normalization': ['none', 'minmax', 'vector', 'amida_i', 'area'],
                    'smoothing': ['none', 'savgol', 'wavelet', 'local_poly', 'whittaker', 'moving_average', 'hanning'],
                    'derivative': ['none', 'savgol']
                }
        """
        self.X = X
        self.y = y
        self.wavenumbers = wavenumbers
        self.groups = groups
        self.evaluator = evaluator or PipelineEvaluator()
        self.metric = metric
        
        if available_methods is None:
            self.available_methods = {
                'truncation': ['fingerprint', 'fingerprint_amide'],
                'baseline': ['none', 'rubberband', 'polynomial', 'whittaker', 'als', 'drpls', 'gcv_spline'],
                'normalization': ['none', 'minmax', 'vector', 'amida_i', 'area'],
                'smoothing': ['none', 'savgol', 'wavelet', 'local_poly', 'whittaker', 'moving_average', 'hanning'],
                'derivative': ['none', 'savgol']
            }
        else:
            self.available_methods = available_methods
            
        self.study = None
        self.best_pipeline = None
        
    def create_objective_function(self, techniques: Optional[List[str]] = None):
        """
        Creates the objective function for optimization
        
        Args:
            techniques: List of available techniques
            
        Returns:
            Objective function
        """
        if techniques is None:
            techniques = ["truncation", "baseline", "normalization", "smoothing", "derivative"]
        
        def objective(trial):
            # Suppress only rampy overflow warnings to maintain optimization quality
            # while keeping other warnings visible for debugging
            import warnings
            warnings.filterwarnings('ignore', message='overflow encountered in exp', category=RuntimeWarning)
            
            all_orders = [",".join(p) for p in itertools.permutations(techniques)]
            order_str = trial.suggest_categorical("order", all_orders)
            order = tuple(order_str.split(","))
            
            # Truncation parameters
            truncation_method = trial.suggest_categorical("truncation", self.available_methods['truncation'])
            
            # Baseline parameters
            baseline_method = trial.suggest_categorical("baseline", self.available_methods['baseline'])
            baseline_params = {}
            if baseline_method == "polynomial":
                baseline_params['polynomial_order'] = trial.suggest_int("poly_order", 1, 5)
            elif baseline_method == "whittaker":
                baseline_params['lam'] = trial.suggest_float("whittaker_lambda", 1e5, 1e9, log=True)
            elif baseline_method == "als":
                baseline_params['lam'] = trial.suggest_float("als_lambda", 1e5, 1e9, log=True)
                baseline_params['p'] = trial.suggest_float("als_p", 0.001, 0.1, log=True)
            elif baseline_method == "arpls":
                baseline_params['lam'] = trial.suggest_float("arpls_lambda", 1e3, 1e7, log=True)
            elif baseline_method == "drpls":
                baseline_params['lam'] = trial.suggest_float("drpls_lambda", 1e3, 1e7, log=True)
            elif baseline_method == "gcv_spline":
                baseline_params['s'] = trial.suggest_float("gcv_spline_s", 0.001, 100.0, log=True)
            elif baseline_method == "gaussian_process":
                baseline_params['sigma'] = trial.suggest_float("gp_sigma", 0.1, 10.0, log=True)
            
            # Normalization parameters
            norm_method = trial.suggest_categorical("normalization", self.available_methods['normalization'])
            norm_params = {}
            if norm_method == "amida_i":
                norm_params['amida_range'] = (1600, 1700)
            elif norm_method == "vector":
                norm_params['norm'] = trial.suggest_categorical("vector_norm", ["l1", "l2", "max"])
            
            # Smoothing parameters
            smooth_method = trial.suggest_categorical("smoothing", self.available_methods['smoothing'])
            smooth_params = {}
            if smooth_method == "savgol":
                smooth_params['polyorder'] = trial.suggest_int("sg_polyorder", 1, 4)
                smooth_params['window_length'] = trial.suggest_int("sg_window_length", 5, 21, step=2)
            elif smooth_method == "wavelet":
                smooth_params['wavelet'] = trial.suggest_categorical("wavelet", ["db2", "db3"])
                smooth_params['level'] = 1
                smooth_params['mode'] = 'soft'
            elif smooth_method == "local_poly":
                smooth_params['bandwidth'] = trial.suggest_int("lp_bandwidth", 1, 6)
                smooth_params['iterations'] = trial.suggest_int("lp_iterations", 0, 3)
            elif smooth_method == "whittaker":
                smooth_params['Lambda'] = trial.suggest_float("smooth_whittaker_lambda", 1e5, 1e9, log=True)
            elif smooth_method == "gcv_spline":
                pass  # GCV spline uses automatic parameter optimization via cross-validation
            elif smooth_method in ["moving_average", "hanning", "hamming", "bartlett", "blackman"]:
                smooth_params['window_length'] = trial.suggest_int("window_length", 5, 21, step=2)
            
            # Derivative parameters
            derivative_order = trial.suggest_int("derivative", 0, 2)
            derivative_params = {}
            if derivative_order > 0:
                derivative_params['order'] = derivative_order
                derivative_params['window_length'] = 11
                derivative_params['polyorder'] = 2
            
            step_configs = {
                'truncation': {'method': truncation_method, 'parameters': {}},
                'baseline': {'method': baseline_method, 'parameters': baseline_params},
                'normalization': {'method': norm_method, 'parameters': norm_params},
                'smoothing': {'method': smooth_method, 'parameters': smooth_params},
                'derivative': {'method': 'savgol', 'parameters': derivative_params}
            }
            
            pipeline = create_pipeline_from_order(order, **step_configs)
            
            try:
                result = self.evaluator.evaluate_pipeline(
                    pipeline, self.X, self.y, self.groups, 
                    metric=self.metric,  
                    wavenumbers=self.wavenumbers
                )
                
                return result['scores'].mean()

                    
            except Exception as e:
                logger.error(f"Error in evaluation: {e}")
                return 0.0
        
        return objective
    
    def optimize(self, n_trials: int = 30, direction: str = "maximize", 
                 timeout: Optional[int] = None, verbose: bool = True, **kwargs) -> optuna.Study:
        """
        Executes the optimization
        
        Args:
            n_trials: Number of trials
            direction: Optimization direction ('maximize' or 'minimize')
            timeout: Time budget for the optimization
            verbose: Show progress information
            **kwargs: Additional parameters
            
        Returns:
            Optuna study (or nested CV results structured as study-like object)
        """
        if hasattr(self.evaluator, 'cv_method') and self.evaluator.cv_method == 'NestedCV':
            if verbose:
                print("Nested CV detected - executing nested cross-validation...")
            return self._execute_nested_cv(n_trials, direction, verbose, **kwargs)
        
        if verbose:
            print("Executing traditional optimization...")
        
        objective = self.create_objective_function()
        
        self.study = optuna.create_study(direction=direction)
        
        self.study.optimize(
            objective, 
            n_trials=n_trials, 
            timeout=timeout,
            **kwargs
        )
        
        self.best_pipeline = self._create_best_pipeline()
        
        return self.study
    
    def _execute_nested_cv(self, n_trials: int, direction: str, verbose: bool = True, **kwargs):
        """
        Executes nested cross-validation using the configured evaluator with NestedCV
        
        Args:
            n_trials: Number of trials (used for inner_trials if not specified)
            direction: Optimization direction
            verbose: Show progress
            
        Returns:
            Study-like object with nested CV results
        """
        
        if verbose:
            cv_params = self.evaluator.cv_params
            outer_folds = cv_params.get('outer_folds', 5)
            inner_folds = cv_params.get('inner_folds', 3)
            print(f"   • Outer folds: {outer_folds}")
            print(f"   • Inner folds: {inner_folds}")
            print(f"   • Trials per inner fold: {n_trials}")
            print(f"   • Total optimizations: {outer_folds} × {n_trials} = {outer_folds * n_trials}")
        
        from ..core.pipeline import PipelineBuilder
        dummy_pipeline = PipelineBuilder().add_baseline('none').build()
        
        try:
            nested_results = self.evaluator.evaluate_pipeline(
                pipeline=dummy_pipeline,
                X=self.X,
                y=self.y,
                groups=self.groups,
                metric=self.metric,
                wavenumbers=self.wavenumbers,
                inner_trials=n_trials  
            )
        except Exception as e:
            if verbose:
                print(f"Error during nested CV: {e}")
            raise
        
        self.study = self._create_nested_study_object(nested_results, direction)
        
        self.best_pipeline = self._create_representative_pipeline_from_nested(nested_results)
        
        return self.study
    
    def _create_nested_study_object(self, nested_results: Dict[str, Any], direction: str):
        """
        Create a study-like object for compatibility with the original interface (Optuna)

        Args:
            nested_results: Nested CV results
            direction: Optimization direction

        Returns:
            NestedStudy object
        """
        class NestedStudy:
            def __init__(self, nested_results, direction, parent_optimizer):
                self.nested_results = nested_results
                self.direction_name = direction
                self.study_name = f"nested_cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.parent_optimizer = parent_optimizer
                
                nested_details = nested_results['nested_cv_results']
                
                self.trials = []
                trial_number = 0
                
                for i, (fold_result, pipeline_summary) in enumerate(zip(
                    nested_details['inner_optimization_results'],
                    nested_details['best_pipelines_per_fold']
                )):
                    pipeline_details = None
                    fold_trials = nested_details['all_trials_by_fold'][i]['trials']
                    if fold_trials:
                        best_trial_in_fold = max(fold_trials, key=lambda t: t['inner_score'])
                        pipeline_details = best_trial_in_fold.get('pipeline_details')
                    
                    trial = type('Trial', (), {
                        'number': trial_number,
                        'value': fold_result['best_inner_score'],
                        'state': type('TrialState', (), {'name': 'COMPLETE'})(),
                        'params': parent_optimizer._extract_params_from_pipeline(pipeline_summary, pipeline_details),
                        'datetime_start': None,
                        'datetime_complete': None,
                        'duration': None
                    })()
                    self.trials.append(trial)
                    trial_number += 1
                
                best_idx = np.argmax([fold['outer_score'] for fold in nested_details['inner_optimization_results']])
                self.best_trial = self.trials[best_idx]
                self.best_value = nested_details['inner_optimization_results'][best_idx]['outer_score']
                self.best_params = self.best_trial.params
                
        return NestedStudy(nested_results, direction, self)
    
    def _extract_params_from_pipeline(self, pipeline_summary: Dict[str, Any], 
                                     pipeline_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract parameters from a pipeline summary to create synthetic params
        
        Args:
            pipeline_summary: Pipeline summary with steps
            pipeline_details: Optional detailed parameters per step
        
        Returns:
            Dictionary with parameters
        """
        steps = pipeline_summary.get('steps', [])
        params = {'order': ','.join(steps)}
        real_params = {}
        if pipeline_details and 'step_configs' in pipeline_details:
            step_configs = pipeline_details['step_configs']
            for step_type, config in step_configs.items():
                if step_type == 'derivative':
                    real_params['derivative'] = config.get('parameters', {}).get('order', 0)
                elif step_type == 'baseline':
                    real_params['baseline'] = config.get('method', 'none')
                elif step_type == 'normalization':
                    real_params['normalization'] = config.get('method', 'none')
                elif step_type == 'smoothing':
                    real_params['smoothing'] = config.get('method', 'none')
                elif step_type == 'truncation':
                    real_params['truncation'] = config.get('method', 'fingerprint_amide')
        
        for step in steps:
            if 'truncation' in step:
                method = step.split('_')[1] if '_' in step else 'fingerprint_amide'
                params['truncation'] = real_params.get('truncation', method)
            elif 'baseline' in step:
                method = step.split('_')[1] if '_' in step else 'none'
                params['baseline'] = real_params.get('baseline', method)
            elif 'normalization' in step:
                method = step.split('_')[1] if '_' in step else 'none'
                params['normalization'] = real_params.get('normalization', method)
            elif 'smoothing' in step:
                method = step.split('_')[1] if '_' in step else 'none'
                params['smoothing'] = real_params.get('smoothing', method)
            elif 'derivative' in step:
                params['derivative'] = real_params.get('derivative', 1)
        
        return params
    
    def _create_representative_pipeline_from_nested(self, nested_results: Dict[str, Any]) -> FTIRPipeline:
        """
        Create a representative pipeline from nested CV results using optimized parameters

        Args:
            nested_results: Nested CV results

        Returns:
            Representative pipeline
        """
        nested_details = nested_results['nested_cv_results']
        
        best_idx = np.argmax([fold['outer_score'] for fold in nested_details['inner_optimization_results']])
        best_pipeline_summary = nested_details['best_pipelines_per_fold'][best_idx]
        
        best_trial_params = None
        fold_trials = nested_details['all_trials_by_fold'][best_idx]['trials']
        if fold_trials:
            best_trial_in_fold = max(fold_trials, key=lambda t: t['inner_score'])
            best_trial_params = best_trial_in_fold.get('params', {})
        
        if not best_trial_params:
            raise ValueError("Optimized parameters not found in nested CV results")
        
        from ..core.pipeline import create_pipeline_from_order
        
        order = best_trial_params.get('order', '').split(',')
        
        step_configs = {}
        
        # Truncation
        truncation_method = best_trial_params.get('truncation', 'fingerprint')
        step_configs['truncation'] = {'method': truncation_method, 'parameters': {}}
        
        # Baseline
        baseline_method = best_trial_params.get('baseline', 'none')
        baseline_params = {}
        if baseline_method == 'polynomial':
            baseline_params['polynomial_order'] = best_trial_params.get('poly_order', 2)
        elif baseline_method == 'whittaker':
            baseline_params['lam'] = best_trial_params.get('whittaker_lambda', 1e2)
        elif baseline_method == 'als':
            baseline_params['lam'] = best_trial_params.get('als_lambda', 1e2)
            baseline_params['p'] = best_trial_params.get('als_p', 0.1)
        elif baseline_method == 'arpls':
            baseline_params['lam'] = best_trial_params.get('arpls_lambda', 1e4)
        elif baseline_method == 'drpls':
            baseline_params['lam'] = best_trial_params.get('drpls_lambda', 1e4)
        elif baseline_method == 'gcv_spline':
            baseline_params['s'] = best_trial_params.get('gcv_spline_s')
        elif baseline_method == 'gaussian_process':
            baseline_params['sigma'] = best_trial_params.get('gp_sigma')
        
        if baseline_method != 'none':
            step_configs['baseline'] = {'method': baseline_method, 'parameters': baseline_params}
        
        # Normalization
        norm_method = best_trial_params.get('normalization', 'none')
        norm_params = {}
        if norm_method == 'amida_i':
            norm_params['amida_range'] = (1600, 1700)
        elif norm_method == 'vector':
            norm_params['norm'] = best_trial_params.get('vector_norm', 'l2')
        
        if norm_method != 'none':
            step_configs['normalization'] = {'method': norm_method, 'parameters': norm_params}
        
        # Smoothing
        smooth_method = best_trial_params.get('smoothing', 'none')
        smooth_params = {}
        if smooth_method == 'savgol':
            smooth_params['polyorder'] = best_trial_params.get('sg_polyorder', 2)
            smooth_params['window_length'] = best_trial_params.get('sg_window_length', 11)
        elif smooth_method == 'wavelet':
            smooth_params['wavelet'] = best_trial_params.get('wavelet', 'db2')
            smooth_params['level'] = 1
            smooth_params['mode'] = 'soft'
        elif smooth_method == 'local_poly':
            smooth_params['bandwidth'] = best_trial_params.get('lp_bandwidth', 3)
            smooth_params['iterations'] = best_trial_params.get('lp_iterations', 0)
        elif smooth_method == 'whittaker':
            smooth_params['Lambda'] = best_trial_params.get('smooth_whittaker_lambda', 1e1)
        elif smooth_method in ['moving_average', 'hanning', 'hamming', 'bartlett', 'blackman']:
            smooth_params['window_length'] = best_trial_params.get('window_length', 11)
        
        if smooth_method != 'none':
            step_configs['smoothing'] = {'method': smooth_method, 'parameters': smooth_params}
        
        # Derivative
        derivative_order = best_trial_params.get('derivative', 0)
        if derivative_order > 0:
            derivative_params = {
                'order': derivative_order,
                'window_length': best_trial_params.get('derivative_window_length', 11),
                'polyorder': best_trial_params.get('derivative_polyorder', 2)
            }
            step_configs['derivative'] = {'method': 'savgol', 'parameters': derivative_params}
        else:
            step_configs['derivative'] = {'method': 'none', 'parameters': {}}
        
        return create_pipeline_from_order(order, **step_configs)
    
    def _create_best_pipeline(self) -> FTIRPipeline:
        """
        Creates the pipeline with the best parameters found
        
        Returns:
            Optimized pipeline
        """
        if self.study is None:
            raise ValueError("Optimization must be executed first")
        
        best_params = self.study.best_params
        
        order = tuple(best_params['order'].split(','))
        
        step_configs = {}
        
        # Truncation
        if 'truncation' in order:
            truncation_method = best_params['truncation']
            step_configs['truncation'] = {'method': truncation_method, 'parameters': {}}
        
        # Baseline
        if 'baseline' in order:
            baseline_method = best_params['baseline']
            baseline_params = {}
            if baseline_method == "polynomial":
                baseline_params['polynomial_order'] = best_params['poly_order']
            elif baseline_method == "whittaker":
                baseline_params['lam'] = best_params['whittaker_lambda']
            elif baseline_method == "als":
                baseline_params['lam'] = best_params['als_lambda']
                baseline_params['p'] = best_params['als_p']
            elif baseline_method == "arpls":
                baseline_params['lam'] = best_params['arpls_lambda']
            elif baseline_method == "drpls":
                baseline_params['lam'] = best_params['drpls_lambda']
            elif baseline_method == "gcv_spline":
                baseline_params['s'] = best_params['gcv_spline_s']
            elif baseline_method == "gaussian_process":
                baseline_params['sigma'] = best_params['gp_sigma']
            step_configs['baseline'] = {'method': baseline_method, 'parameters': baseline_params}
        
        # Normalization
        if 'normalization' in order:
            norm_method = best_params['normalization']
            norm_params = {}
            if norm_method == "amida_i":
                norm_params['amida_range'] = (1600, 1700)
            elif norm_method == "vector":
                norm_params['norm'] = best_params['vector_norm']
            step_configs['normalization'] = {'method': norm_method, 'parameters': norm_params}
        
        # Smoothing
        if 'smoothing' in order:
            smooth_method = best_params['smoothing']
            smooth_params = {}
            if smooth_method == "savgol":
                smooth_params['polyorder'] = best_params['sg_polyorder']
                smooth_params['window_length'] = best_params['sg_window_length']
            elif smooth_method == "wavelet":
                smooth_params['wavelet'] = best_params['wavelet']
                smooth_params['level'] = 1
                smooth_params['mode'] = 'soft'
            elif smooth_method == "local_poly":
                smooth_params['bandwidth'] = best_params['lp_bandwidth']
                smooth_params['iterations'] = best_params['lp_iterations']
            elif smooth_method == "whittaker":
                smooth_params['Lambda'] = best_params['smooth_whittaker_lambda']
            elif smooth_method == "gcv_spline":
                pass  # GCV spline uses automatic parameter optimization via cross-validation
            elif smooth_method in ["moving_average", "hanning", "hamming", "bartlett", "blackman"]:
                smooth_params['window_length'] = best_params['window_length']
            step_configs['smoothing'] = {'method': smooth_method, 'parameters': smooth_params}
        
        # Derivative
        if 'derivative' in order:
            derivative_order = best_params['derivative']
            if derivative_order > 0:
                derivative_params = {
                    'order': derivative_order,
                    'window_length': 11,
                    'polyorder': 2
                }
                step_configs['derivative'] = {'method': 'savgol', 'parameters': derivative_params}
            else:
                step_configs['derivative'] = {'method': 'none', 'parameters': {}}
        
        return create_pipeline_from_order(order, **step_configs)
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Returns an optimization summary
        
        Returns:
            Dictionary with optimization information
        """
        if self.study is None:
            return {"status": "Optimization not executed"}
        
        return {
            "best_value": self.study.best_value,
            "best_params": self.study.best_params,
            "n_trials": len(self.study.trials),
            "metric_used": self.metric
        }
    
    def get_metadata(self) -> 'OptimizationMetadata':
        """
        Get detailed optimization metadata in standardized JSON format
        
        Returns:
            OptimizationMetadata dictionary with standardized format
        """
        if self.study is None:
            raise ValueError("Optimization must be executed first")
        
        is_nested_cv = hasattr(self.study, 'nested_results')
        
        metadata = {
            "metadata": {
                "optimization_method": "Optuna",
                "objective_name": self.metric,
                "direction": "maximize",
                "random_seed": getattr(self.study.sampler, 'random_state', 42) if hasattr(self.study, 'sampler') else 42,
                "total_trials": len(self.study.trials),
                "completed_trials": len([t for t in self.study.trials if t.state.name == 'COMPLETE']),
                "failed_trials": len([t for t in self.study.trials if t.state.name == 'FAIL']),
                "pruned_trials": len([t for t in self.study.trials if t.state.name == 'PRUNED'])
            }
        }
        
        if is_nested_cv:
            nested_results = self.study.nested_results
            nested_details = nested_results['nested_cv_results']
            cv_config = nested_details['cv_config']
            
            metadata["cross_validation"] = {
                "type": "NestedCV",
                "outer_folds": cv_config['outer_folds'],
                "inner_folds": cv_config['inner_folds'],
                "inner_cv_type": cv_config['base_cv_method'],
                "shuffle": cv_config.get('shuffle', False),
                "stratified": cv_config['base_cv_method'] in ['StratifiedKFold', 'StratifiedGroupKFold'],
                "inner_trials_per_fold": cv_config.get('inner_trials', 0),
                "total_inner_trials": cv_config['outer_folds'] * cv_config.get('inner_trials', 0)
            }
            
            outer_folds = []
            for fold_data in nested_details['all_trials_by_fold']:
                fold_id = fold_data['outer_fold']
                outer_score = fold_data['outer_score']
                
                inner_trials = []
                for trial in fold_data['trials']:
                    if trial.get('inner_score') is not None:
                        pipeline_steps = self._extract_pipeline_steps(trial.get('pipeline_details', {}))
                        inner_trials.append({
                            "trial_id": trial.get('trial_number', 0) + 1,  # Padroniza para começar em 1
                            "pipeline": pipeline_steps,
                            "mean_inner_score": trial.get('inner_score', 0),
                            "execution_time_sec": trial.get('duration', 0)
                        })
                
                best_trial = max(fold_data['trials'], key=lambda t: t.get('inner_score', 0) if t.get('inner_score') is not None else -float('inf'))
                best_pipeline_steps = self._extract_pipeline_steps(best_trial.get('pipeline_details', {}))
                
                outer_folds.append({
                    "outer_fold_id": fold_id,
                    "inner_trials": inner_trials,
                    "best_trial_id": best_trial.get('trial_number', 0) + 1,
                    "best_pipeline": best_pipeline_steps,
                    "outer_test_score": outer_score,
                    "outer_execution_time_sec": sum([t.get('duration', 0) for t in fold_data['trials']])
                })
            
            metadata["results"] = {"outer_folds": outer_folds}
            best_outer_score = max([fold['outer_score'] for fold in nested_details['inner_optimization_results']])
            metadata["overall_best_score"] = best_outer_score
            metadata["best_pipeline"] = self.best_pipeline.steps
            
        else:
            cv_method = getattr(self.evaluator, 'cv_method', 'Unknown')
            cv_params = getattr(self.evaluator, 'cv_params', {})
            
            metadata["cross_validation"] = {
                "type": cv_method,
                "n_splits": cv_params.get('n_splits', 5),
                "shuffle": cv_params.get('shuffle', False),
                "stratified": cv_method in ['StratifiedKFold', 'StratifiedGroupKFold']
            }
            
            trials = []
            for trial in self.study.trials:
                if trial.value is not None:
                    pipeline_steps = self._extract_pipeline_steps_from_params(trial.params)
                    trials.append({
                        "trial_id": trial.number + 1,
                        "pipeline": pipeline_steps,
                        "mean_cv_score": trial.value,
                        "execution_time_sec": trial.duration.total_seconds() if trial.duration else 0
                    })
            
            metadata["results"] = {"trials": trials}
            
            best_pipeline_steps = self._extract_pipeline_steps_from_params(self.study.best_params)
            metadata["best_pipeline"] = best_pipeline_steps
        
        return OptimizationMetadata(metadata)
    
    def _extract_pipeline_steps(self, pipeline_details: dict) -> list:
        """
        Extracts the steps of the pipeline from the pipeline details
        
        Args:
            pipeline_details: Dictionary with pipeline details
            
        Returns:
            List of steps of the pipeline in the original format
        """
        if not pipeline_details:
            return [{"type": "unknown", "method": "unknown", "parameters": {}, "name": "unknown_pipeline"}]
        
        step_configs = pipeline_details.get('step_configs', {})
        if step_configs:
            steps = []
            order = pipeline_details.get('order', [])
            for step_type in order:
                if step_type in step_configs:
                    config = step_configs[step_type]
                    step = {
                        'type': step_type,
                        'method': config['method'],
                        'parameters': config.get('parameters', {}),
                        'name': f"{step_type}_{config['method']}"
                    }
                    steps.append(step)
            return steps
        
        pipeline_steps = pipeline_details.get('pipeline_steps', [])
        if pipeline_steps:
            steps = []
            for step_name in pipeline_steps:
                if '_' in step_name:
                    step_type, method = step_name.split('_', 1)
                    step = {
                        'type': step_type,
                        'method': method,
                        'parameters': {},
                        'name': step_name
                    }
                    steps.append(step)
            return steps
        
        return [{"type": "unknown", "method": "unknown", "parameters": {}, "name": "unknown_pipeline"}]
    
    def _extract_pipeline_steps_from_params(self, params: dict) -> list:
        """
        Extracts the steps of the pipeline from the trial parameters
        
        Args:
            params: Trial parameters
            
        Returns:
            List of steps of the pipeline in the original format
        """
        if not params:
            return [{"type": "unknown", "method": "unknown", "parameters": {}, "name": "unknown_pipeline"}]
        
        try:
            from ftir_framework.core.pipeline import create_pipeline_from_order
            
            order = params.get('order', '').split(',')
            
            step_configs = {}
            
            # Truncation
            truncation_method = params.get('truncation', 'fingerprint')
            step_configs['truncation'] = {'method': truncation_method, 'parameters': {}}
            
            # Baseline
            baseline_method = params.get('baseline', 'none')
            baseline_params = {}
            if baseline_method == 'polynomial':
                baseline_params['polynomial_order'] = params.get('poly_order', 2)
            elif baseline_method == 'whittaker':
                baseline_params['lam'] = params.get('whittaker_lambda', 1e2)
            elif baseline_method == 'als':
                baseline_params['lam'] = params.get('als_lambda', 1e2)
                baseline_params['p'] = params.get('als_p', 0.1)
            elif baseline_method == 'arpls':
                baseline_params['lam'] = params.get('arpls_lambda', 1e4)
            elif baseline_method == 'drpls':
                baseline_params['lam'] = params.get('drpls_lambda', 1e4)
            elif baseline_method == 'gcv_spline':
                baseline_params['s'] = params.get('gcv_spline_s')
            
            step_configs['baseline'] = {'method': baseline_method, 'parameters': baseline_params}
            
            # Normalization
            norm_method = params.get('normalization', 'none')
            norm_params = {}
            if norm_method == 'amida_i':
                norm_params['amida_range'] = (1600, 1700)
            elif norm_method == 'vector':
                norm_params['norm'] = params.get('vector_norm', 'l2')
            
            step_configs['normalization'] = {'method': norm_method, 'parameters': norm_params}
            
            # Smoothing
            smooth_method = params.get('smoothing', 'none')
            smooth_params = {}
            if smooth_method == 'savgol':
                smooth_params['polyorder'] = params.get('sg_polyorder', 2)
                smooth_params['window_length'] = params.get('sg_window_length', 11)
            elif smooth_method == 'wavelet':
                smooth_params['wavelet'] = params.get('wavelet', 'db2')
                smooth_params['level'] = 1
                smooth_params['mode'] = 'soft'
            elif smooth_method == 'local_poly':
                smooth_params['bandwidth'] = params.get('lp_bandwidth', 3)
                smooth_params['iterations'] = params.get('lp_iterations', 0)
            elif smooth_method == 'whittaker':
                smooth_params['Lambda'] = params.get('smooth_whittaker_lambda', 1e1)
            elif smooth_method in ['moving_average', 'hanning', 'hamming', 'bartlett', 'blackman']:
                smooth_params['window_length'] = params.get('window_length', 11)
            
            step_configs['smoothing'] = {'method': smooth_method, 'parameters': smooth_params}
            
            # Derivative
            derivative_order = params.get('derivative', 0)
            if derivative_order > 0:
                derivative_params = {
                    'order': derivative_order,
                    'window_length': 11,
                    'polyorder': 2
                }
                step_configs['derivative'] = {'method': 'savgol', 'parameters': derivative_params}
            else:
                step_configs['derivative'] = {'method': 'none', 'parameters': {}}
            
            pipeline = create_pipeline_from_order(order, **step_configs)
            
            return pipeline.steps
            
        except Exception as e:
            logger.warning(f"Error reconstructing pipeline from parameters: {e}")
            order = params.get('order', '').split(',')
            steps = []
            for step_type in order:
                if step_type:
                    step = {
                        'type': step_type,
                        'method': 'unknown',
                        'parameters': {},
                        'name': f"{step_type}_unknown"
                    }
                    steps.append(step)
            return steps if steps else [{"type": "unknown", "method": "unknown", "parameters": {}, "name": "unknown_pipeline"}]
    
    def _get_best_trial_from_fold(self, trials: list) -> dict:
        """
        Finds the best trial from a specific fold
        
        Args:
            trials: List of trials from a specific fold
            
        Returns:
            Dictionary with information about the best trial
        """
        if not trials:
            return {}
            
        best_trial = max(trials, key=lambda t: t.get('inner_score', 0) if t.get('inner_score') is not None else 0)
        
        return {
            'trial_number': best_trial.get('trial_number', -1),
            'inner_score': best_trial.get('inner_score', 0),
            'pipeline_details': best_trial.get('pipeline_details', {}),
            'params': best_trial.get('params', {}),
            'duration': best_trial.get('duration', 0)
        }
    
    def _get_score_range(self, trials: list) -> dict:
        """
        Calculates statistics of the scores of the trials
        
        Args:
            trials: List of trials
            
        Returns:
            Dictionary with statistics of the scores
        """
        scores = [t.get('inner_score', 0) for t in trials if t.get('inner_score') is not None]
        
        if not scores:
            return {'min': 0, 'max': 0, 'std': 0, 'range': 0}
        
        return {
            'min': min(scores),
            'max': max(scores),
            'std': float(np.std(scores)) if len(scores) > 1 else 0.0,
            'range': max(scores) - min(scores)
        }