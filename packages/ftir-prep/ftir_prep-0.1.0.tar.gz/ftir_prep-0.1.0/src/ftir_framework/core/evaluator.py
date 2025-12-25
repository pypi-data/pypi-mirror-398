"""
Module for evaluating FTIR preprocessing pipelines
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, GroupKFold, StratifiedKFold, StratifiedGroupKFold
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, balanced_accuracy_score,
    f1_score, precision_score, recall_score, roc_auc_score, log_loss, jaccard_score,
    matthews_corrcoef, cohen_kappa_score
)
from sklearn.base import BaseEstimator, clone
from typing import Dict, Any, Optional, Tuple
from ..core.pipeline import FTIRPipeline
import logging

logger = logging.getLogger(__name__)

class NestedCV(BaseEstimator):
    """
    Class to support nested cross-validation
    """    
    def __init__(self, base_cv_method='StratifiedGroupKFold', outer_folds=5, 
                 inner_folds=3, shuffle=False, random_state=None):
        """
        Initializes the nested cross-validation object
        
        Args:
            base_cv_method: Base cross-validation method (StratifiedGroupKFold, GroupKFold, StratifiedKFold)
            outer_folds: Number of outer cross-validation splits
            inner_folds: Number of inner cross-validation splits
            shuffle: Whether to shuffle the data (true or false)
            random_state: Random state
        """
        self.base_cv_method = base_cv_method
        self.outer_folds = outer_folds
        self.inner_folds = inner_folds
        self.shuffle = shuffle
        self.random_state = random_state
        self.n_splits = outer_folds
        
    def split(self, X, y=None, groups=None):
        """
        Interface sklearn: generates outer cross-validation splits
        
        Args:
            X: Spectra matrix
            y: Labels vector
            groups: Groups for cross-validation
            
        Returns:
            Train and test indices
        """
        cv = self._create_base_cv(self.outer_folds)
        for train_idx, test_idx in cv.split(X, y, groups):
            yield train_idx, test_idx
    
    def get_n_splits(self, X=None, y=None, groups=None):
        """
        Interface sklearn: returns the number of outer cross-validation splits
            
        Returns:
            Number of outer cross-validation splits
        """
        return self.n_splits
        
    def _create_base_cv(self, n_splits):
        """
        Creates the base cross-validation object
        
        Args:
            n_splits: Number of cross-validation splits
            
        Returns:
            Base cross-validation object
        """
        if self.base_cv_method == 'StratifiedGroupKFold':
            random_state = self.random_state if self.shuffle else None
            return StratifiedGroupKFold(n_splits=n_splits, shuffle=self.shuffle, random_state=random_state)
        elif self.base_cv_method == 'GroupKFold':
            return GroupKFold(n_splits=n_splits)
        elif self.base_cv_method == 'StratifiedKFold':
            random_state = self.random_state if self.shuffle else None
            return StratifiedKFold(n_splits=n_splits, shuffle=self.shuffle, random_state=random_state)
        else:
            raise ValueError(f"CV method not supported: {self.base_cv_method}")


class PipelineEvaluator:
    """
    Evaluator of preprocessing pipelines with stratified group cross-validation
    """
    
    def __init__(self, classifier=None, cv_method='StratifiedGroupKFold', cv_params=None):
        """
        Initializes the evaluator
        
        Args:
            classifier: Classifier to be used (default: RandomForest)
            cv_method: Cross-validation method (StratifiedGroupKFold, GroupKFold, StratifiedKFold)
            cv_params: Parameters for cross-validation
        """
        if classifier is not None:
            self.classifier = classifier
        else:
            self._classifier_factory = lambda: RandomForestClassifier(
                n_estimators=100, 
                random_state=42,
                class_weight='balanced'
            )
            self.classifier = None
            
        self.cv_method = cv_method
        self.cv_params = cv_params or {}
        self.evaluation_results = {}
    
    def _get_classifier(self):
        """
        Gets the classifier, creating it if necessary (lazy loading)
        """
        if self.classifier is None:
            self.classifier = self._classifier_factory()
        return self.classifier
        
    def evaluate_pipeline(self, pipeline: FTIRPipeline, X: np.ndarray, y: np.ndarray, 
                         groups: Optional[np.ndarray] = None, metric: str = 'balanced_accuracy', **kwargs) -> Dict[str, Any]:
        """
        Evaluates a specific pipeline
        
        Args:
            pipeline: Pipeline to be evaluated
            X: Spectra matrix
            y: Labels vector
            groups: Groups for cross-validation (data from same patient)
            metric: Metric to be used for evaluation
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
            
        Returns:
            Dictionary with evaluation results
        """

        if groups is None and self.cv_method in ['StratifiedGroupKFold', 'GroupKFold']:
            raise ValueError("Groups are required for stratified group cross-validation")
        
        if groups is not None:
            self._validate_group_labels(y, groups)
        
        cv = self._setup_cross_validation(groups, y)
        
        if self.cv_method == 'NestedCV':
            inner_trials = kwargs.pop('inner_trials', 20)  # Remove dos kwargs para evitar duplicação
            return self._evaluate_with_nested_cv(X, y, groups, cv, metric, inner_trials, **kwargs)
        
        X_processed, _ = pipeline.process(X, kwargs.get('wavenumbers'))
        
        scores = cross_val_score(
            self._get_classifier(), 
            X_processed, 
            y, 
            cv=cv, 
            scoring=metric, 
            groups=groups
        )
        
        results = {
            'metric': metric,
            'mean_score': scores.mean(),
            'std_score': scores.std(),
            'scores': scores,
            'pipeline_summary': pipeline.get_pipeline_summary(),
            'data_shape': X_processed.shape,
            'cv_method': self.cv_method,
            'n_folds': len(scores),
            'class_distribution': self._get_class_distribution(y, groups)
        }
        
        pipeline_name = f"pipeline_{len(self.evaluation_results)}"
        self.evaluation_results[pipeline_name] = results
        
        return results

    def _evaluate_with_nested_cv(self, X: np.ndarray, y: np.ndarray, groups: Optional[np.ndarray], 
                                cv: NestedCV, metric: str, inner_trials: int, **kwargs) -> Dict[str, Any]:
        """
        Evaluates the pipeline with nested cross-validation
        
        Args:
            X: Spectra matrix
            y: Labels vector
            groups: Groups for cross-validation
            cv: Nested cross-validation object
            metric: Metric to be used for evaluation
            inner_trials: Number of trials for inner cross-validation
            
        Returns:
            Dictionary with evaluation results
        """
        wavenumbers = kwargs.get('wavenumbers')
        if wavenumbers is None:
            raise ValueError("wavenumbers is required for NestedCV")
            
        from ..optimization.optuna_optimizer import OptunaPipelineOptimizer
        
        outer_scores = []
        best_pipelines_per_fold = []
        inner_optimization_results = []
        all_trials_by_fold = [] 
        
        fold_idx = 0
        for train_idx, test_idx in cv.split(X, y, groups):
            fold_idx += 1
            logger.info(f"NestedCV Fold {fold_idx}/{cv.n_splits} - Optimizing pipeline...")
            logger.info(f"   Train samples: {len(train_idx)}, Test samples: {len(test_idx)}")
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            groups_train = groups[train_idx] if groups is not None else None
            
            logger.info(f"   X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
            logger.info(f"   X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
            
            if X_train.shape[0] != len(y_train):
                raise ValueError(f"Inconsistency in training data: X_train.shape[0]={X_train.shape[0]}, len(y_train)={len(y_train)}")
            if X_test.shape[0] != len(y_test):
                raise ValueError(f"Inconsistency in test data: X_test.shape[0]={X_test.shape[0]}, len(y_test)={len(y_test)}")
            if groups_train is not None and len(groups_train) != len(y_train):
                raise ValueError(f"Inconsistency in training groups: len(groups_train)={len(groups_train)}, len(y_train)={len(y_train)}")
            
            inner_classifier = clone(self._get_classifier())
            inner_evaluator = PipelineEvaluator(
                classifier=inner_classifier,
                cv_method=cv.base_cv_method,
                cv_params={'n_splits': cv.inner_folds, 'shuffle': cv.shuffle, 'random_state': cv.random_state}
            )
            
            optimizer = OptunaPipelineOptimizer(
                X_train, y_train, wavenumbers, groups_train,
                evaluator=inner_evaluator,
                metric=metric
            )
            
            study = optimizer.optimize(n_trials=inner_trials, verbose=False)
            best_pipeline = optimizer.best_pipeline
            
            X_train_processed, _ = best_pipeline.process(X_train, wavenumbers)
            X_test_processed, _ = best_pipeline.process(X_test, wavenumbers)
            
            final_classifier = clone(self._get_classifier())
            final_classifier.fit(X_train_processed, y_train)
            
            y_pred = final_classifier.predict(X_test_processed)
            
            if metric == 'balanced_accuracy':
                score = balanced_accuracy_score(y_test, y_pred)
            elif metric == 'accuracy':
                score = accuracy_score(y_test, y_pred)
            elif metric.startswith('f1'):
                # f1, f1_macro, f1_micro, f1_weighted
                average = metric.split('_')[1] if '_' in metric else 'macro'
                score = f1_score(y_test, y_pred, average=average, zero_division=0)
            elif metric.startswith('precision'):
                # precision, precision_macro, precision_micro, precision_weighted
                average = metric.split('_')[1] if '_' in metric else 'macro'
                score = precision_score(y_test, y_pred, average=average, zero_division=0)
            elif metric.startswith('recall'):
                # recall, recall_macro, recall_micro, recall_weighted
                average = metric.split('_')[1] if '_' in metric else 'macro'
                score = recall_score(y_test, y_pred, average=average, zero_division=0)
            elif metric.startswith('roc_auc'):
                # roc_auc, roc_auc_ovo, roc_auc_ovr
                multi_class = metric.split('_')[2] if len(metric.split('_')) > 2 else 'ovr'
                try:
                    y_proba = final_classifier.predict_proba(X_test_processed)
                    score = roc_auc_score(y_test, y_proba, multi_class=multi_class)
                except ValueError:
                    score = 0.0
            elif metric == 'neg_log_loss':
                try:
                    y_proba = final_classifier.predict_proba(X_test_processed)
                    score = -log_loss(y_test, y_proba)
                except ValueError:
                    score = 0.0
            elif metric == 'jaccard':
                score = jaccard_score(y_test, y_pred, average='macro', zero_division=0)
            elif metric == 'mcc':
                score = matthews_corrcoef(y_test, y_pred)
            elif metric == 'kappa':
                score = cohen_kappa_score(y_test, y_pred)
            elif metric == 'specificity':
                cm = confusion_matrix(y_test, y_pred)
                if cm.shape[0] == 2:  # Binary classification
                    tn, fp, fn, tp = cm.ravel()
                    score = tn / (tn + fp) if (tn + fp) > 0 else 0.0
                else:  # Multi-class classification
                    specificities = []
                    for i in range(cm.shape[0]):
                        tn = np.sum(cm) - (np.sum(cm[i, :]) + np.sum(cm[:, i]) - cm[i, i])
                        fp = np.sum(cm[:, i]) - cm[i, i]
                        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
                        specificities.append(specificity)
                    score = np.mean(specificities)
            elif metric == 'sensitivity':
                average = 'macro'  
                score = recall_score(y_test, y_pred, average=average, zero_division=0)
            elif metric == 'npv':
                # Negative Predictive Value
                cm = confusion_matrix(y_test, y_pred)
                if cm.shape[0] == 2:  # Binary classification
                    tn, fp, fn, tp = cm.ravel()
                    score = tn / (tn + fn) if (tn + fn) > 0 else 0.0
                else:  # Multi-class classification
                    npvs = []
                    for i in range(cm.shape[0]):
                        tn = np.sum(cm) - (np.sum(cm[i, :]) + np.sum(cm[:, i]) - cm[i, i])
                        fn = np.sum(cm[i, :]) - cm[i, i]
                        npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
                        npvs.append(npv)
                    score = np.mean(npvs)
            elif metric == 'ppv':
                # Positive Predictive Value
                average = 'macro'  # Default for multi-class
                score = precision_score(y_test, y_pred, average=average, zero_division=0)
            else:
                available_metrics = [
                    'accuracy', 'balanced_accuracy', 'f1', 'f1_macro', 'f1_micro', 'f1_weighted',
                    'precision', 'precision_macro', 'precision_micro', 'precision_weighted',
                    'recall', 'recall_macro', 'recall_micro', 'recall_weighted',
                    'roc_auc', 'roc_auc_ovo', 'roc_auc_ovr', 'neg_log_loss', 'jaccard',
                    'mcc', 'kappa', 'specificity', 'sensitivity', 'npv', 'ppv'
                ]
                raise ValueError(
                    f"Metric '{metric}' is not implemented. "
                    f"Available metrics: {', '.join(available_metrics)}. "
                    f"Please use one of the supported metrics."
                )
            
            outer_scores.append(score)
            best_pipelines_per_fold.append(best_pipeline.get_pipeline_summary())
            
            fold_info = {
                'outer_fold': fold_idx,
                'outer_score': score,
                'best_inner_score': study.best_value,
                'n_trials': len(study.trials),
                'best_pipeline_steps': best_pipeline.get_pipeline_summary()['steps']
            }
            inner_optimization_results.append(fold_info)
            
            fold_trials = []
            for trial in study.trials:
                pipeline_details = self._reconstruct_pipeline_from_params(trial.params) if trial.params else None
                
                trial_info = {
                    'outer_fold': fold_idx,
                    'trial_number': trial.number,
                    'inner_score': trial.value,
                    'params': trial.params,
                    'pipeline_details': pipeline_details,  # Detalhes do pipeline construído
                    'state': trial.state.name if hasattr(trial.state, 'name') else str(trial.state),
                    'duration': trial.duration.total_seconds() if hasattr(trial, 'duration') and trial.duration else None
                }
                fold_trials.append(trial_info)
            
            all_trials_by_fold.append({
                'outer_fold': fold_idx,
                'outer_score': score,
                'trials': fold_trials
            })
            
            logger.info(f"   Fold {fold_idx}: {score:.3f} (pipeline: {' → '.join(best_pipeline.get_pipeline_summary()['steps'])})")
        
        outer_scores = np.array(outer_scores)
        
        results = {
            'metric': metric,
            'mean_score': outer_scores.mean(),
            'std_score': outer_scores.std(),
            'scores': outer_scores,
            'cv_method': self.cv_method,
            'n_folds': len(outer_scores),
            'class_distribution': self._get_class_distribution(y, groups),
            'data_shape': X.shape,
            'nested_cv_results': {
                'outer_scores': outer_scores,
                'best_pipelines_per_fold': best_pipelines_per_fold,
                'inner_optimization_results': inner_optimization_results,
                'all_trials_by_fold': all_trials_by_fold, 
                'cv_config': {
                    'outer_folds': cv.outer_folds,
                    'inner_folds': cv.inner_folds,
                    'inner_trials': inner_trials, 
                    'base_cv_method': cv.base_cv_method
                }
            }
        }
        
        pipeline_name = f"nested_cv_{len(self.evaluation_results)}"
        self.evaluation_results[pipeline_name] = results
        
        return results
    
    def _validate_group_labels(self, y: np.ndarray, groups: np.ndarray):
        """
        Validates if data from same group have same label
        
        Args:
            y: Labels vector
            groups: Groups vector
        """
        unique_groups = np.unique(groups)
        
        for group in unique_groups:
            group_mask = groups == group
            group_labels = y[group_mask]
            
            if len(np.unique(group_labels)) > 1:
                raise ValueError(
                    f"Data from group {group} have different labels: {np.unique(group_labels)}. "
                    "All data from the same group must have the same label."
                )
    
    def _setup_cross_validation(self, groups: Optional[np.ndarray], y: np.ndarray):
        """
        Configures the cross-validation method
        
        Args:
            groups: Groups for cross-validation (optional)
            y: Labels for stratification
            
        Returns:
            Configured cross-validation object
        """
        if self.cv_method == 'NestedCV':
            base_cv_method = self.cv_params.get('base_cv_method', 'StratifiedGroupKFold')
            outer_folds = self.cv_params.get('outer_folds', 5)
            inner_folds = self.cv_params.get('inner_folds', 3)
            shuffle = self.cv_params.get('shuffle', False)
            random_state = self.cv_params.get('random_state', 42)
            
            if shuffle and shuffle != False:
                logger.warning("WARNING: Shuffling enabled in NestedCV!")
            else:
                random_state = None
                
            if groups is not None:
                n_groups = len(np.unique(groups))
                outer_folds = min(outer_folds, n_groups)
                inner_folds = min(inner_folds, n_groups)
            
            return NestedCV(
                base_cv_method=base_cv_method,
                outer_folds=outer_folds,
                inner_folds=inner_folds,
                shuffle=shuffle,
                random_state=random_state
            )
        elif self.cv_method == 'StratifiedGroupKFold':
            if groups is None:
                raise ValueError("Groups are required for StratifiedGroupKFold")
            n_splits = self.cv_params.get('n_splits', 5)
            shuffle = self.cv_params.get('shuffle', False) 
            random_state = self.cv_params.get('random_state', 42)
            
            if shuffle:
                logger.warning("WARNING: Shuffling enabled!")
            else:
                random_state = None
            
            n_groups = len(np.unique(groups))
            n_splits = min(n_splits, n_groups)
            
            return StratifiedGroupKFold(
                n_splits=n_splits, 
                shuffle=shuffle, 
                random_state=random_state
            )
        elif self.cv_method == 'GroupKFold':
            if groups is None:
                raise ValueError("Groups are required for GroupKFold")
            n_splits = self.cv_params.get('n_splits', 5)
            n_groups = len(np.unique(groups))
            n_splits = min(n_splits, n_groups)
            return GroupKFold(n_splits=n_splits)
        elif self.cv_method == 'StratifiedKFold':
            n_splits = self.cv_params.get('n_splits', 5)
            shuffle = self.cv_params.get('shuffle', False) 
            random_state = self.cv_params.get('random_state', 42)
            
            if shuffle:
                logger.warning("WARNING: StratifiedKFold with shuffling!")
            else:
                random_state = None
            
            return StratifiedKFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
        else:
            raise ValueError(f"Unsupported cross-validation method: {self.cv_method}")
    
    def _get_class_distribution(self, y: np.ndarray, groups: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Calculates class distribution per group (if groups provided) or overall
        
        Args:
            y: Labels vector
            groups: Groups vector (optional)
            
        Returns:
            Dictionary with information about class distribution
        """
        if groups is not None:
            unique_groups = np.unique(groups)
            group_labels = {}
            
            for group in unique_groups:
                group_mask = groups == group
                group_labels[group] = y[group_mask][0]
            
            class_counts = {}
            for label in group_labels.values():
                class_counts[label] = class_counts.get(label, 0) + 1
            
            return {
                'total_groups': len(unique_groups),
                'class_counts': class_counts
            }
        else:
            unique_labels, counts = np.unique(y, return_counts=True)
            class_counts = dict(zip(unique_labels, counts))
            
            return {
                'total_samples': len(y),
                'class_counts': class_counts
            }
    
    def compare_pipelines(self, pipelines: Dict[str, FTIRPipeline], X: np.ndarray, 
                         y: np.ndarray, groups: Optional[np.ndarray] = None, 
                         **kwargs) -> Dict[str, Any]:
        """
        Compares multiple pipelines
        
        Args:
            pipelines: Dictionary with named pipelines
            X: Spectra matrix
            y: Labels vector
            groups: Groups for cross-validation
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with comparative results
        """
        comparison_results = {}
        
        for name, pipeline in pipelines.items():
            logger.info(f"Evaluating pipeline: {name}")
            results = self.evaluate_pipeline(pipeline, X, y, groups, **kwargs)
            comparison_results[name] = results
        
        best_name, best_results = self._get_best_pipeline(comparison_results)
        comparison_results['best_pipeline_name'] = best_name
        comparison_results['best_results'] = best_results['mean_score']

        return comparison_results
    
    def _get_best_pipeline(self, comparison_results: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Identifies the best pipeline based on mean accuracy
        
        Args:
            comparison_results: Comparison results
            
        Returns:
            Tuple with name and results of best pipeline
        """
        if 'best_name' in comparison_results:
            return comparison_results['best_name'], comparison_results['best_results']
        
        best_name = max(comparison_results.keys(), 
                       key=lambda x: comparison_results[x]['mean_score'])
        return best_name, comparison_results[best_name]
    
    def _reconstruct_pipeline_from_params(self, params: dict) -> dict:
        """
        Reconstructs pipeline information from Optuna trial parameters
        
        Args:
            params: Optuna trial parameters
            
        Returns:
            Dictionary with detailed pipeline information
        """
        try:
            from ftir_framework.core.pipeline import create_pipeline_from_order
            
            order = params.get('order', '').split(',')
            
            step_configs = {}
            
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
                smooth_params['iterations'] = 0
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
            pipeline_summary = pipeline.get_pipeline_summary()
            
            return {
                'order': order,
                'step_configs': step_configs,
                'pipeline_steps': pipeline_summary.get('steps', []),
                'n_steps': pipeline_summary.get('n_steps', 0),
                'pipeline_description': ' → '.join(pipeline_summary.get('steps', []))
            }
            
        except Exception as e:
            logger.warning(f"Error reconstructing pipeline from parameters: {e}")
            return {
                'order': params.get('order', '').split(','),
                'step_configs': {},
                'pipeline_steps': [],
                'n_steps': 0,
                'pipeline_description': 'Error in reconstruction',
                'error': str(e)
            }
