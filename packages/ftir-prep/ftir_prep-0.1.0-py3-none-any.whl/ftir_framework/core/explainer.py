"""
Module for FTIR model explainability using SHAP
"""

import numpy as np
from sklearn.model_selection import train_test_split, GroupKFold, StratifiedGroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score, confusion_matrix
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import warnings
import shap
import logging

logger = logging.getLogger(__name__)

# Suppress specific warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning, module='shap')
warnings.filterwarnings('ignore', message='.*NumPy global RNG.*')

class FTIRExplainer:
    """
    Class for FTIR model explainability analysis using SHAP
    """
    
    def __init__(self, classifier: Optional[Any] = None):
        """
        Initializes the explainer
        
        Args:
            classifier: Classifier to be used (default: RandomForest)
        """
        
        self.classifier = classifier or RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'
        )
        
    def explain_model(self, 
                     X_processed: np.ndarray, 
                     y: np.ndarray,
                     groups: Optional[np.ndarray] = None,
                     split_method: str = 'stratified',
                     test_size: float = 0.2,
                     random_state: int = 42,
                     feature_names: Optional[List[str]] = None,
                     output_dir: str = "shap_analysis") -> Dict[str, Any]:
        """
        Executes SHAP explainability analysis and generates feature importance
        
        Args:
            X_processed: Already processed data (n_samples, n_features)
            y: Labels vector
            groups: Groups for group-based split (optional)
            split_method: Data split method:
                - 'stratified': Simple stratified split
                - 'group': Group-based split (requires groups)
                - 'stratified_group': Stratified group split (requires groups)
            test_size: Proportion of data for testing (default: 0.2)
            random_state: Seed for reproducibility
            feature_names: Feature names (e.g., wavenumbers)
            output_dir: Directory to save files
            
        Returns:
            Dictionary with analysis results including paths to:
            - feature_importance.csv: Global feature importance rankings
            - top_15_features.png: Visualization of most important features
        """
        
        self._validate_params(X_processed, y, groups, split_method)
        
        X_train, X_test, y_train, y_test = self._split_data(
            X_processed, y, groups, split_method, test_size, random_state
        )
        
        logger.info(f"🔧 Training model with {len(X_train)} samples...")
        trained_model = self.classifier.fit(X_train, y_train)
        
        logger.info("📈 Evaluating model performance...")
        y_pred = trained_model.predict(X_test)
        
        test_balanced_accuracy = balanced_accuracy_score(y_test, y_pred)
        test_f1_macro = f1_score(y_test, y_pred, average='macro')
        
        cm = confusion_matrix(y_test, y_pred)
        
        if cm.shape[0] > 2:
            specificities = []
            for i in range(cm.shape[0]):
                tn = np.sum(cm) - (np.sum(cm[i, :]) + np.sum(cm[:, i]) - cm[i, i])
                fp = np.sum(cm[:, i]) - cm[i, i]
                specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
                specificities.append(specificity)
            test_specificity = np.mean(specificities)
        else:
            tn, fp, fn, tp = cm.ravel()
            test_specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        performance_metrics = {
            'test_balanced_accuracy': test_balanced_accuracy,
            'test_f1_macro': test_f1_macro,
            'test_specificity': test_specificity
        }
        
        logger.info(f"   Test Balanced Accuracy: {test_balanced_accuracy:.4f}")
        logger.info(f"   Test F1-Score (macro): {test_f1_macro:.4f}")
        logger.info(f"   Test Specificity: {test_specificity:.4f}")
        
        feature_names = self._prepare_feature_names(feature_names, X_processed.shape[1])
        
        logger.info("🔍 Creating SHAP explainer...")
        explainer = self._create_shap_explainer(trained_model, X_train)
        
        logger.info("📊 Computing SHAP values...")
        shap_values = explainer(X_test)
        
        n_classes = len(np.unique(y))
        if hasattr(shap_values, 'values'):
            shap_shape = shap_values.values.shape
        else:
            shap_shape = shap_values.shape
        
        if len(shap_shape) > 2:
            logger.info(f"   Detected multi-class problem: {n_classes} classes, SHAP shape: {shap_shape}")
        else:
            logger.info(f"   Detected binary/regression problem, SHAP shape: {shap_shape}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            'split_method': split_method,
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'n_features': X_processed.shape[1],
            'test_size_actual': len(X_test) / len(X_processed),
            'output_dir': str(output_path),
            'feature_names': feature_names,
            **performance_metrics 
        }
        
        logger.info("💾 Saving feature importance data...")
        csv_results = self._save_csv_data(
            shap_values, X_test, y_test, len(y_train), trained_model,
            feature_names, output_path
        )
        results.update(csv_results)
        
        if 'importance_csv' in csv_results:
            logger.info("🎨 Generating top features plot...")
            top_plot_path = self.plot_top_features(
                csv_results['importance_csv'],
                n_features=15,
                output_path=output_path / "top_15_features.png"
            )
            results['top_features_plot'] = top_plot_path
            logger.info(f"   Top features plot saved to: {top_plot_path}")
        
        logger.info(f"✅ SHAP analysis completed!")
        logger.info(f"   📁 Files saved to: {output_path}")
        
        return results
    
    def _validate_params(self, X_processed: np.ndarray, y: np.ndarray,
                        groups: Optional[np.ndarray], split_method: str):
        """Validates input parameters"""
        if X_processed.shape[0] != len(y):
            raise ValueError("X_processed and y must have the same number of samples")
        
        if split_method in ['group', 'stratified_group'] and groups is None:
            raise ValueError(f"Split method '{split_method}' requires 'groups' parameter")
        
        if groups is not None and len(groups) != len(y):
            raise ValueError("groups must have the same size as y")
        
        valid_methods = ['stratified', 'group', 'stratified_group']
        if split_method not in valid_methods:
            raise ValueError(f"split_method must be one of {valid_methods}, "
                           f"received: {split_method}")
    
    def _split_data(self, X: np.ndarray, y: np.ndarray,
                   groups: Optional[np.ndarray], split_method: str,
                   test_size: float, random_state: int):
        """Executes data split based on specified method"""
        
        if split_method == 'stratified':
            return train_test_split(
                X, y, test_size=test_size, random_state=random_state,
                stratify=y
            )
        
        elif split_method == 'group':
            n_splits = max(2, int(1 / test_size))
            gkf = GroupKFold(n_splits=n_splits)
            train_idx, test_idx = next(gkf.split(X, y, groups))
            return X[train_idx], X[test_idx], y[train_idx], y[test_idx]
        
        elif split_method == 'stratified_group':
            return self._stratified_group_split(X, y, groups, test_size, random_state)
    
    def _stratified_group_split(self, X: np.ndarray, y: np.ndarray,
                                       groups: np.ndarray, test_size: float, random_state: int):
        """Implements stratified group split"""

        n_splits = max(2, int(1 / test_size))
        
        sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=False)
        
        train_idx, test_idx = next(sgkf.split(X, y, groups))
        
        return X[train_idx], X[test_idx], y[train_idx], y[test_idx]
    
    def _prepare_feature_names(self, feature_names: Optional[List[str]], n_features: int) -> List[str]:
        """Prepares feature names"""
        if feature_names is None:
            return [f"feature_{i}" for i in range(n_features)]
        elif len(feature_names) != n_features:
            logger.warning(f"⚠️  Number of feature_names ({len(feature_names)}) does not match "
                  f"number of features ({n_features}). Using generic names.")
            return [f"feature_{i}" for i in range(n_features)]
        else:
            return feature_names
    
    def _create_shap_explainer(self, model, X_train):
        """Creates optimized SHAP explainer"""
        try:
            # TreeExplainer for tree-based models (faster)
            if hasattr(model, 'predict_proba') and hasattr(model, 'estimators_'):
                return shap.TreeExplainer(model)
            else:
                return shap.Explainer(model, X_train)
        except Exception as e:
            logger.warning(f"⚠️  Using generic explainer due to: {e}")
            return shap.Explainer(model, X_train)
    
    def _save_csv_data(self, shap_values, X_test, y_test, n_train_samples, model,
                      feature_names, output_path):
        """Saves only feature importance CSV"""
        csv_results = {}
        
        try:
            if hasattr(shap_values, 'values'):
                shap_matrix = shap_values.values
            else:
                shap_matrix = shap_values
            
            if len(shap_matrix.shape) > 2:
                logger.info(f"   Multi-class SHAP values detected: {shap_matrix.shape}")
                shap_matrix_for_importance = np.abs(shap_matrix).mean(axis=-1)
            else:
                shap_matrix_for_importance = shap_matrix
            
            mean_abs_shap = np.abs(shap_matrix_for_importance).mean(axis=0)
            std_abs_shap = np.abs(shap_matrix_for_importance).std(axis=0)
            
            importance_df = pd.DataFrame({
                'feature_name': feature_names,
                'mean_abs_shap': mean_abs_shap,
                'std_abs_shap': std_abs_shap,
                'mean_shap': shap_matrix_for_importance.mean(axis=0),
                'std_shap': shap_matrix_for_importance.std(axis=0),
                'rank': range(1, len(feature_names) + 1)
            }).sort_values('mean_abs_shap', ascending=False)
            
            importance_df['rank'] = range(1, len(importance_df) + 1)
            
            importance_csv_path = output_path / "feature_importance.csv"
            importance_df.to_csv(importance_csv_path, index=False)
            csv_results['importance_csv'] = str(importance_csv_path)
            
            logger.info(f"   Feature importance saved to: {importance_csv_path}")
            
        except Exception as e:
            logger.error(f"⚠️  Error saving CSV data: {e}")
        
        return csv_results
    
    def get_top_features(self, importance_csv_path: str, n_features: int = 10) -> pd.DataFrame:
        """
        Returns the top N most important features
        
        Args:
            importance_csv_path: Path to importance file
            n_features: Number of features to return
            
        Returns:
            DataFrame with top features
        """
        if not Path(importance_csv_path).exists():
            raise FileNotFoundError(f"File not found: {importance_csv_path}")
        
        importance_df = pd.read_csv(importance_csv_path)
        return importance_df.head(n_features)
    
    def plot_top_features(self, importance_csv_path: str, n_features: int = 15,
                         output_path: Optional[str] = None) -> str:
        """
        Creates plot of top N most important features
        
        Args:
            importance_csv_path: Path to importance file
            n_features: Number of features to plot
            output_path: Path to save plot (optional)
            
        Returns:
            Path of generated file
        """
        top_features = self.get_top_features(importance_csv_path, n_features)
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(top_features)), top_features['mean_abs_shap'], color='skyblue')
        plt.yticks(range(len(top_features)), top_features['feature_name'])
        plt.xlabel('Mean SHAP Importance (Absolute Value)')
        plt.title(f'Top {n_features} Most Important Features')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        if output_path is None:
            output_path = Path(importance_csv_path).parent / f"top_{n_features}_features.png"
        else:
            output_path = Path(output_path)
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
