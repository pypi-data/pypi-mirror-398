# intelligent_automl/evaluation/multi_metric_evaluator.py

"""
Multi-Metric Evaluation System for Intelligent AutoML Framework

This module provides comprehensive evaluation capabilities with support for
multiple metrics, multi-objective optimization, and detailed performance analysis.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from sklearn.metrics import (
    # Classification metrics
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    log_loss, classification_report, confusion_matrix, balanced_accuracy_score,
    average_precision_score, matthews_corrcoef, cohen_kappa_score,
    
    # Regression metrics
    r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error,
    explained_variance_score, max_error, median_absolute_error
)
from sklearn.model_selection import cross_val_score, cross_validate
import warnings


@dataclass
class MetricResult:
    """Container for a single metric result."""
    name: str
    value: float
    higher_is_better: bool
    description: str
    category: str  # 'accuracy', 'precision_recall', 'probabilistic', 'error', etc.


@dataclass
class ComprehensiveMetrics:
    """Container for comprehensive evaluation results."""
    task_type: str
    primary_metric: str
    primary_score: float
    all_metrics: Dict[str, MetricResult]
    cross_validation_scores: Dict[str, np.ndarray]
    ranking_scores: Dict[str, float]  # Normalized scores for ranking models
    
    def get_metric(self, name: str) -> Optional[MetricResult]:
        """Get a specific metric result."""
        return self.all_metrics.get(name)
    
    def get_best_metrics(self, top_n: int = 5) -> List[MetricResult]:
        """Get top N metrics sorted by normalized scores."""
        sorted_metrics = sorted(
            self.all_metrics.values(),
            key=lambda m: self.ranking_scores.get(m.name, 0),
            reverse=True
        )
        return sorted_metrics[:top_n]
    
    def summary(self) -> str:
        """Generate a summary string of the evaluation."""
        lines = [
            f"📊 {self.task_type.title()} Task Evaluation Summary",
            f"🎯 Primary Metric: {self.primary_metric} = {self.primary_score:.4f}",
            "",
            "🏆 Top Metrics:"
        ]
        
        for i, metric in enumerate(self.get_best_metrics(3), 1):
            direction = "↗" if metric.higher_is_better else "↘"
            lines.append(f"  {i}. {metric.name}: {metric.value:.4f} {direction}")
        
        return "\n".join(lines)


class MultiMetricEvaluator:
    """
    Comprehensive multi-metric evaluation system that computes and analyzes
    multiple relevant metrics for both classification and regression tasks.
    """
    
    # Define comprehensive metric sets for each task type
    CLASSIFICATION_METRICS = {
        # Accuracy-based metrics
        'accuracy': {
            'func': accuracy_score,
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Overall classification accuracy',
            'category': 'accuracy'
        },
        'balanced_accuracy': {
            'func': balanced_accuracy_score,
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Balanced accuracy (handles class imbalance)',
            'category': 'accuracy'
        },
        
        # Precision/Recall metrics
        'precision_macro': {
            'func': lambda y_true, y_pred: precision_score(y_true, y_pred, average='macro', zero_division=0),
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Macro-averaged precision',
            'category': 'precision_recall'
        },
        'precision_weighted': {
            'func': lambda y_true, y_pred: precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Weighted-averaged precision',
            'category': 'precision_recall'
        },
        'recall_macro': {
            'func': lambda y_true, y_pred: recall_score(y_true, y_pred, average='macro', zero_division=0),
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Macro-averaged recall',
            'category': 'precision_recall'
        },
        'recall_weighted': {
            'func': lambda y_true, y_pred: recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Weighted-averaged recall',
            'category': 'precision_recall'
        },
        'f1_macro': {
            'func': lambda y_true, y_pred: f1_score(y_true, y_pred, average='macro', zero_division=0),
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Macro-averaged F1 score',
            'category': 'precision_recall'
        },
        'f1_weighted': {
            'func': lambda y_true, y_pred: f1_score(y_true, y_pred, average='weighted', zero_division=0),
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Weighted-averaged F1 score',
            'category': 'precision_recall'
        },
        
        # Probabilistic metrics (binary classification)
        'roc_auc': {
            'func': lambda y_true, y_proba: roc_auc_score(y_true, y_proba, multi_class='ovr', average='weighted'),
            'needs_proba': True,
            'higher_is_better': True,
            'description': 'Area under ROC curve',
            'category': 'probabilistic'
        },
        'average_precision': {
            'func': lambda y_true, y_proba: average_precision_score(y_true, y_proba, average='weighted'),
            'needs_proba': True,
            'higher_is_better': True,
            'description': 'Area under Precision-Recall curve',
            'category': 'probabilistic'
        },
        'log_loss': {
            'func': lambda y_true, y_proba: log_loss(y_true, y_proba),
            'needs_proba': True,
            'higher_is_better': False,
            'description': 'Logarithmic loss',
            'category': 'probabilistic'
        },
        
        # Agreement metrics
        'matthews_corrcoef': {
            'func': matthews_corrcoef,
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Matthews correlation coefficient',
            'category': 'agreement'
        },
        'cohen_kappa': {
            'func': cohen_kappa_score,
            'needs_proba': False,
            'higher_is_better': True,
            'description': 'Cohen\'s kappa coefficient',
            'category': 'agreement'
        }
    }
    
    REGRESSION_METRICS = {
        # Error-based metrics
        'r2': {
            'func': r2_score,
            'higher_is_better': True,
            'description': 'Coefficient of determination (R²)',
            'category': 'variance_explained'
        },
        'explained_variance': {
            'func': explained_variance_score,
            'higher_is_better': True,
            'description': 'Explained variance score',
            'category': 'variance_explained'
        },
        
        # Absolute error metrics
        'mae': {
            'func': mean_absolute_error,
            'higher_is_better': False,
            'description': 'Mean absolute error',
            'category': 'absolute_error'
        },
        'median_ae': {
            'func': median_absolute_error,
            'higher_is_better': False,
            'description': 'Median absolute error',
            'category': 'absolute_error'
        },
        'max_error': {
            'func': max_error,
            'higher_is_better': False,
            'description': 'Maximum residual error',
            'category': 'absolute_error'
        },
        
        # Squared error metrics
        'mse': {
            'func': mean_squared_error,
            'higher_is_better': False,
            'description': 'Mean squared error',
            'category': 'squared_error'
        },
        'rmse': {
            'func': lambda y_true, y_pred: np.sqrt(mean_squared_error(y_true, y_pred)),
            'higher_is_better': False,
            'description': 'Root mean squared error',
            'category': 'squared_error'
        },
        
        # Percentage error metrics
        'mape': {
            'func': lambda y_true, y_pred: mean_absolute_percentage_error(y_true, y_pred) * 100,
            'higher_is_better': False,
            'description': 'Mean absolute percentage error (%)',
            'category': 'percentage_error'
        },
        'symmetric_mape': {
            'func': lambda y_true, y_pred: np.mean(2.0 * np.abs(y_pred - y_true) / (np.abs(y_pred) + np.abs(y_true))) * 100,
            'higher_is_better': False,
            'description': 'Symmetric mean absolute percentage error (%)',
            'category': 'percentage_error'
        }
    }
    
    def __init__(self, 
                 custom_metrics: Optional[Dict[str, Callable]] = None,
                 primary_metric: Optional[str] = None):
        """
        Initialize the multi-metric evaluator.
        
        Args:
            custom_metrics: Dictionary of custom metric functions
            primary_metric: Primary metric to use for model selection
        """
        self.custom_metrics = custom_metrics or {}
        self.primary_metric = primary_metric
    
    def evaluate_classification(self, 
                              y_true: np.ndarray, 
                              y_pred: np.ndarray,
                              y_proba: Optional[np.ndarray] = None,
                              selected_metrics: Optional[List[str]] = None) -> ComprehensiveMetrics:
        """
        Comprehensive evaluation for classification tasks.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (for probabilistic metrics)
            selected_metrics: Specific metrics to compute (None for all)
            
        Returns:
            ComprehensiveMetrics object with all results
        """
        metrics_to_use = selected_metrics or list(self.CLASSIFICATION_METRICS.keys())
        all_metrics = {}
        
        # Determine if binary classification for probabilistic metrics
        n_classes = len(np.unique(y_true))
        is_binary = n_classes == 2
        
        for metric_name in metrics_to_use:
            if metric_name in self.CLASSIFICATION_METRICS:
                metric_info = self.CLASSIFICATION_METRICS[metric_name]
                
                try:
                    if metric_info['needs_proba']:
                        if y_proba is not None:
                            if is_binary and metric_name in ['roc_auc', 'average_precision']:
                                # For binary classification, use probability of positive class
                                if y_proba.ndim > 1:
                                    score = metric_info['func'](y_true, y_proba[:, 1])
                                else:
                                    score = metric_info['func'](y_true, y_proba)
                            else:
                                score = metric_info['func'](y_true, y_proba)
                        else:
                            continue  # Skip probabilistic metrics if no probabilities
                    else:
                        score = metric_info['func'](y_true, y_pred)
                    
                    all_metrics[metric_name] = MetricResult(
                        name=metric_name,
                        value=score,
                        higher_is_better=metric_info['higher_is_better'],
                        description=metric_info['description'],
                        category=metric_info['category']
                    )
                    
                except Exception as e:
                    warnings.warn(f"Could not compute {metric_name}: {str(e)}")
                    continue
        
        # Add custom metrics
        for name, func in self.custom_metrics.items():
            try:
                score = func(y_true, y_pred)
                all_metrics[name] = MetricResult(
                    name=name,
                    value=score,
                    higher_is_better=True,  # Assume higher is better for custom metrics
                    description=f"Custom metric: {name}",
                    category='custom'
                )
            except Exception as e:
                warnings.warn(f"Could not compute custom metric {name}: {str(e)}")
        
        # Determine primary metric
        primary = self.primary_metric or ('accuracy' if 'accuracy' in all_metrics else list(all_metrics.keys())[0])
        primary_score = all_metrics[primary].value if primary in all_metrics else 0.0
        
        # Calculate ranking scores (normalized)
        ranking_scores = self._calculate_ranking_scores(all_metrics)
        
        return ComprehensiveMetrics(
            task_type='classification',
            primary_metric=primary,
            primary_score=primary_score,
            all_metrics=all_metrics,
            cross_validation_scores={},  # To be filled by cross-validation
            ranking_scores=ranking_scores
        )
    
    def evaluate_regression(self, 
                          y_true: np.ndarray, 
                          y_pred: np.ndarray,
                          selected_metrics: Optional[List[str]] = None) -> ComprehensiveMetrics:
        """
        Comprehensive evaluation for regression tasks.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            selected_metrics: Specific metrics to compute (None for all)
            
        Returns:
            ComprehensiveMetrics object with all results
        """
        metrics_to_use = selected_metrics or list(self.REGRESSION_METRICS.keys())
        all_metrics = {}
        
        for metric_name in metrics_to_use:
            if metric_name in self.REGRESSION_METRICS:
                metric_info = self.REGRESSION_METRICS[metric_name]
                
                try:
                    score = metric_info['func'](y_true, y_pred)
                    
                    all_metrics[metric_name] = MetricResult(
                        name=metric_name,
                        value=score,
                        higher_is_better=metric_info['higher_is_better'],
                        description=metric_info['description'],
                        category=metric_info['category']
                    )
                    
                except Exception as e:
                    warnings.warn(f"Could not compute {metric_name}: {str(e)}")
                    continue
        
        # Add custom metrics
        for name, func in self.custom_metrics.items():
            try:
                score = func(y_true, y_pred)
                all_metrics[name] = MetricResult(
                    name=name,
                    value=score,
                    higher_is_better=False,  # Assume lower is better for custom regression metrics
                    description=f"Custom metric: {name}",
                    category='custom'
                )
            except Exception as e:
                warnings.warn(f"Could not compute custom metric {name}: {str(e)}")
        
        # Determine primary metric
        primary = self.primary_metric or ('r2' if 'r2' in all_metrics else list(all_metrics.keys())[0])
        primary_score = all_metrics[primary].value if primary in all_metrics else 0.0
        
        # Calculate ranking scores (normalized)
        ranking_scores = self._calculate_ranking_scores(all_metrics)
        
        return ComprehensiveMetrics(
            task_type='regression',
            primary_metric=primary,
            primary_score=primary_score,
            all_metrics=all_metrics,
            cross_validation_scores={},  # To be filled by cross-validation
            ranking_scores=ranking_scores
        )
    
    def cross_validate_comprehensive(self,
                                   estimator,
                                   X: np.ndarray,
                                   y: np.ndarray,
                                   task_type: str,
                                   cv: int = 5,
                                   selected_metrics: Optional[List[str]] = None) -> ComprehensiveMetrics:
        """
        Perform comprehensive cross-validation with multiple metrics.
        
        Args:
            estimator: ML model to evaluate
            X: Feature matrix
            y: Target variable
            task_type: 'classification' or 'regression'
            cv: Number of cross-validation folds
            selected_metrics: Specific metrics to compute
            
        Returns:
            ComprehensiveMetrics with cross-validation results
        """
        # Get metric definitions
        if task_type == 'classification':
            metric_defs = self.CLASSIFICATION_METRICS
        else:
            metric_defs = self.REGRESSION_METRICS
        
        metrics_to_use = selected_metrics or list(metric_defs.keys())
        
        # Prepare scoring parameter for cross_validate
        scoring = {}
        for metric_name in metrics_to_use:
            if metric_name in metric_defs:
                metric_info = metric_defs[metric_name]
                
                # Skip probabilistic metrics for cross-validation (sklearn limitation)
                if task_type == 'classification' and metric_info.get('needs_proba', False):
                    continue
                
                # Map to sklearn scorer names
                sklearn_name = self._map_to_sklearn_scorer(metric_name, task_type)
                if sklearn_name:
                    scoring[metric_name] = sklearn_name
        
        # Perform cross-validation
        cv_results = cross_validate(
            estimator, X, y,
            cv=cv,
            scoring=scoring,
            return_train_score=True,
            n_jobs=-1
        )
        
        # Convert results to our format
        all_metrics = {}
        cv_scores = {}
        
        for metric_name in scoring.keys():
            test_scores = cv_results[f'test_{metric_name}']
            cv_scores[metric_name] = test_scores
            
            metric_info = metric_defs[metric_name]
            all_metrics[metric_name] = MetricResult(
                name=metric_name,
                value=test_scores.mean(),
                higher_is_better=metric_info['higher_is_better'],
                description=metric_info['description'],
                category=metric_info['category']
            )
        
        # Determine primary metric
        primary = self.primary_metric or list(all_metrics.keys())[0] if all_metrics else 'accuracy'
        primary_score = all_metrics[primary].value if primary in all_metrics else 0.0
        
        # Calculate ranking scores
        ranking_scores = self._calculate_ranking_scores(all_metrics)
        
        return ComprehensiveMetrics(
            task_type=task_type,
            primary_metric=primary,
            primary_score=primary_score,
            all_metrics=all_metrics,
            cross_validation_scores=cv_scores,
            ranking_scores=ranking_scores
        )
    
    def _calculate_ranking_scores(self, metrics: Dict[str, MetricResult]) -> Dict[str, float]:
        """Calculate normalized ranking scores for comparing metrics."""
        ranking_scores = {}
        
        # Get values for normalization
        values = np.array([m.value for m in metrics.values()])
        
        if len(values) == 0:
            return ranking_scores
        
        # Handle infinite values
        finite_mask = np.isfinite(values)
        if not np.any(finite_mask):
            return {name: 0.0 for name in metrics.keys()}
        
        finite_values = values[finite_mask]
        value_range = finite_values.max() - finite_values.min()
        
        if value_range == 0:
            # All values are the same
            return {name: 1.0 for name in metrics.keys()}
        
        # Normalize each metric
        for name, metric in metrics.items():
            if not np.isfinite(metric.value):
                ranking_scores[name] = 0.0
                continue
            
            # Normalize to [0, 1]
            normalized = (metric.value - finite_values.min()) / value_range
            
            # Flip if lower is better
            if not metric.higher_is_better:
                normalized = 1 - normalized
            
            ranking_scores[name] = normalized
        
        return ranking_scores
    
    def _map_to_sklearn_scorer(self, metric_name: str, task_type: str) -> Optional[str]:
        """Map our metric names to sklearn scorer names."""
        sklearn_mapping = {
            'classification': {
                'accuracy': 'accuracy',
                'balanced_accuracy': 'balanced_accuracy',
                'precision_macro': 'precision_macro',
                'precision_weighted': 'precision_weighted',
                'recall_macro': 'recall_macro',
                'recall_weighted': 'recall_weighted',
                'f1_macro': 'f1_macro',
                'f1_weighted': 'f1_weighted',
                'roc_auc': 'roc_auc_ovr_weighted',
                'matthews_corrcoef': 'matthews_corrcoef'
            },
            'regression': {
                'r2': 'r2',
                'mae': 'neg_mean_absolute_error',
                'mse': 'neg_mean_squared_error',
                'rmse': 'neg_root_mean_squared_error',
                'explained_variance': 'explained_variance',
                'max_error': 'max_error'
            }
        }
        
        return sklearn_mapping.get(task_type, {}).get(metric_name)
    
    @classmethod
    def get_default_metrics(cls, task_type: str) -> List[str]:
        """Get default metric set for a task type."""
        if task_type == 'classification':
            return ['accuracy', 'balanced_accuracy', 'f1_weighted', 'precision_weighted', 'recall_weighted']
        else:
            return ['r2', 'mae', 'mse', 'rmse', 'explained_variance']
    
    @classmethod
    def get_all_available_metrics(cls, task_type: str) -> List[str]:
        """Get all available metrics for a task type."""
        if task_type == 'classification':
            return list(cls.CLASSIFICATION_METRICS.keys())
        else:
            return list(cls.REGRESSION_METRICS.keys())