# intelligent_automl/models/auto_trainer.py

"""
Enhanced AutoModelTrainer with Multi-Metric Support

This module provides comprehensive model training with multi-metric evaluation,
model comparison, and advanced optimization capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
import time
import warnings
from sklearn.model_selection import train_test_split, cross_val_score, cross_validate
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.metrics import make_scorer
import joblib

# Import our enhanced metric system - CORRECTED IMPORT PATH
from ..evaluation.multi_metric_evaluator import MultiMetricEvaluator, ComprehensiveMetrics, MetricResult
from ..core.config import AutoMLConfig, EvaluationConfig, OptimizationConfig


@dataclass
class ModelPerformance:
    """Enhanced model performance container with comprehensive metrics."""
    model_name: str
    task_type: str
    
    # Comprehensive metrics
    train_metrics: ComprehensiveMetrics
    val_metrics: ComprehensiveMetrics
    cv_metrics: Optional[ComprehensiveMetrics] = None
    
    # Performance characteristics
    training_time: float = 0.0
    prediction_time: float = 0.0
    memory_usage: float = 0.0  # MB
    
    # Model artifacts
    feature_importance: Optional[Dict[str, float]] = None
    model_size: Optional[float] = None  # MB
    
    # Multi-objective scores
    pareto_rank: Optional[int] = None
    dominance_count: Optional[int] = None
    composite_score: Optional[float] = None
    
    def get_primary_score(self, split: str = 'val') -> float:
        """Get primary metric score for model ranking."""
        if split == 'val':
            return self.val_metrics.primary_score
        elif split == 'train':
            return self.train_metrics.primary_score
        elif split == 'cv' and self.cv_metrics:
            return self.cv_metrics.primary_score
        else:
            return 0.0
    
    def get_metric_score(self, metric_name: str, split: str = 'val') -> Optional[float]:
        """Get specific metric score."""
        metrics_obj = getattr(self, f'{split}_metrics', None)
        if metrics_obj:
            metric = metrics_obj.get_metric(metric_name)
            return metric.value if metric else None
        return None
    
    def summary(self) -> str:
        """Generate performance summary."""
        lines = [
            f"🤖 Model: {self.model_name}",
            f"📊 Task: {self.task_type}",
            f"🎯 Primary Score: {self.get_primary_score():.4f}",
            f"⏱️ Training Time: {self.training_time:.3f}s",
            f"💾 Memory Usage: {self.memory_usage:.2f}MB",
            "",
            "📈 Validation Metrics:"
        ]
        
        for metric in self.val_metrics.get_best_metrics(5):
            direction = "↗" if metric.higher_is_better else "↘"
            lines.append(f"  • {metric.name}: {metric.value:.4f} {direction}")
        
        return "\n".join(lines)


class EnhancedAutoModelTrainer:
    """
    Enhanced AutoML trainer with comprehensive multi-metric evaluation,
    model comparison, and advanced optimization capabilities.
    """
    
    def __init__(self, 
                 config: Optional[AutoMLConfig] = None,
                 task_type: Optional[str] = None,
                 models: Optional[List[str]] = None,
                 cv_folds: int = 5,
                 random_state: int = 42,
                 verbose: bool = True,
                 n_jobs: int = -1):
        """
        Initialize the enhanced AutoML trainer.
        
        Args:
            config: AutoML configuration object
            task_type: 'classification' or 'regression' (auto-detected if None)
            models: List of model names to train
            cv_folds: Number of cross-validation folds
            random_state: Random seed for reproducibility
            verbose: Whether to print progress information
            n_jobs: Number of parallel jobs
        """
        self.config = config
        self.task_type = task_type
        self.models = models or ['random_forest', 'logistic_regression', 'svm']
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.verbose = verbose
        self.n_jobs = n_jobs
        
        # Initialize components
        self.metric_evaluator = MultiMetricEvaluator()
        self.trained_models: Dict[str, Any] = {}
        self.model_performances: Dict[str, ModelPerformance] = {}
        self.best_model = None
        self.best_model_name = None
        
        # Set up configuration if provided
        if self.config:
            self._configure_from_config()
    
    def _configure_from_config(self):
        """Configure trainer from AutoMLConfig object."""
        if self.config.task_type:
            self.task_type = self.config.task_type
        
        # Set up metric evaluator
        eval_config = self.config.evaluation
        if eval_config.primary_metric:
            self.metric_evaluator.primary_metric = eval_config.primary_metric
        
        if eval_config.custom_metrics:
            self.metric_evaluator.custom_metrics = eval_config.custom_metrics
        
        # Update training parameters
        self.cv_folds = eval_config.cv_folds
        self.verbose = self.config.verbose
        
        # Set models if specified in config
        if hasattr(self.config.model, 'models') and self.config.model.models:
            self.models = self.config.model.models
    
    def _detect_task_type(self, y: Series) -> str:
        """Auto-detect task type from target variable."""
        if self.task_type:
            return self.task_type
        
        # Check if target is continuous or categorical
        unique_values = y.nunique()
        total_values = len(y)
        
        # Heuristics for task detection
        if unique_values <= 20 and unique_values / total_values < 0.05:
            return 'classification'
        elif y.dtype in ['int64', 'int32'] and unique_values <= 50:
            return 'classification'
        elif y.dtype in ['object', 'category']:
            return 'classification'
        else:
            return 'regression'
    
    def _get_model_instance(self, model_name: str, task_type: str) -> Any:
        """Get model instance for given name and task type."""
        models = {
            'random_forest': {
                'classification': RandomForestClassifier(
                    random_state=self.random_state,
                    n_jobs=self.n_jobs
                ),
                'regression': RandomForestRegressor(
                    random_state=self.random_state,
                    n_jobs=self.n_jobs
                )
            },
            'logistic_regression': {
                'classification': LogisticRegression(
                    random_state=self.random_state,
                    max_iter=1000,
                    n_jobs=self.n_jobs
                ),
                'regression': LinearRegression(n_jobs=self.n_jobs)
            },
            'linear_regression': {
                'classification': LogisticRegression(
                    random_state=self.random_state,
                    max_iter=1000,
                    n_jobs=self.n_jobs
                ),
                'regression': LinearRegression(n_jobs=self.n_jobs)
            },
            'svm': {
                'classification': SVC(
                    random_state=self.random_state,
                    probability=True
                ),
                'regression': SVR()
            }
        }
        
        if model_name not in models:
            raise ValueError(f"Unknown model: {model_name}")
        
        return models[model_name][task_type]
    
    def _get_selected_metrics(self, task_type: str) -> List[str]:
        """Get metrics to evaluate based on configuration."""
        if self.config and self.config.evaluation.metrics:
            return self.config.evaluation.get_metric_names()
        else:
            return MultiMetricEvaluator.get_default_metrics(task_type)
    
    def _train_single_model(self, 
                          model_name: str, 
                          X_train: DataFrame, 
                          y_train: Series,
                          X_val: DataFrame, 
                          y_val: Series, 
                          task_type: str) -> ModelPerformance:
        """Train a single model and return comprehensive performance metrics."""
        if self.verbose:
            print(f"  🔧 Training {model_name}...")
        
        start_time = time.time()
        
        try:
            # Get model instance
            model = self._get_model_instance(model_name, task_type)
            
            # Train model
            model.fit(X_train, y_train)
            training_time = time.time() - start_time
            
            # Get selected metrics
            selected_metrics = self._get_selected_metrics(task_type)
            
            # Evaluate on training set
            start_pred_time = time.time()
            y_train_pred = model.predict(X_train)
            y_train_proba = None
            if task_type == 'classification' and hasattr(model, 'predict_proba'):
                y_train_proba = model.predict_proba(X_train)
            
            if task_type == 'classification':
                train_metrics = self.metric_evaluator.evaluate_classification(
                    y_train, y_train_pred, y_train_proba, selected_metrics
                )
            else:
                train_metrics = self.metric_evaluator.evaluate_regression(
                    y_train, y_train_pred, selected_metrics
                )
            
            # Evaluate on validation set
            y_val_pred = model.predict(X_val)
            y_val_proba = None
            if task_type == 'classification' and hasattr(model, 'predict_proba'):
                y_val_proba = model.predict_proba(X_val)
            
            if task_type == 'classification':
                val_metrics = self.metric_evaluator.evaluate_classification(
                    y_val, y_val_pred, y_val_proba, selected_metrics
                )
            else:
                val_metrics = self.metric_evaluator.evaluate_regression(
                    y_val, y_val_pred, selected_metrics
                )
            
            prediction_time = time.time() - start_pred_time
            
            # Cross-validation evaluation
            cv_metrics = None
            if self.config is None or self.config.evaluation.cross_validation:
                try:
                    cv_metrics = self.metric_evaluator.cross_validate_comprehensive(
                        model, X_train, y_train, task_type, 
                        cv=self.cv_folds, selected_metrics=selected_metrics
                    )
                except Exception as e:
                    if self.verbose:
                        print(f"    ⚠️ Cross-validation failed: {str(e)}")
            
            # Get feature importance
            feature_importance = self._get_feature_importance(model, X_train.columns.tolist())
            
            # Estimate memory usage
            memory_usage = self._estimate_model_memory(model)
            
            # Store model
            self.trained_models[model_name] = model
            
            # Create performance object
            performance = ModelPerformance(
                model_name=model_name,
                task_type=task_type,
                train_metrics=train_metrics,
                val_metrics=val_metrics,
                cv_metrics=cv_metrics,
                training_time=training_time,
                prediction_time=prediction_time,
                memory_usage=memory_usage,
                feature_importance=feature_importance
            )
            
            if self.verbose:
                primary_score = performance.get_primary_score()
                primary_metric = val_metrics.primary_metric
                cv_score = cv_metrics.primary_score if cv_metrics else "N/A"
                print(f"    ✅ {model_name}: {primary_metric}={primary_score:.4f} (CV: {cv_score})")
            
            return performance
            
        except Exception as e:
            if self.verbose:
                print(f"    ❌ {model_name} failed: {str(e)}")
            raise ValueError(f"Failed to train {model_name}: {str(e)}")
    
    def _get_feature_importance(self, model: Any, feature_names: List[str]) -> Optional[Dict[str, float]]:
        """Extract feature importance from model if available."""
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                return dict(zip(feature_names, importances))
            elif hasattr(model, 'coef_'):
                # For linear models, use absolute coefficient values
                coef = np.abs(model.coef_).flatten() if len(model.coef_.shape) > 1 else np.abs(model.coef_)
                return dict(zip(feature_names, coef))
        except Exception:
            pass
        
        return None
    
    def _estimate_model_memory(self, model: Any) -> float:
        """Estimate model memory usage in MB."""
        try:
            # Rough estimate based on model attributes
            memory_bytes = 0
            for attr_name in dir(model):
                if not attr_name.startswith('_'):
                    attr = getattr(model, attr_name, None)
                    if hasattr(attr, 'nbytes'):
                        memory_bytes += attr.nbytes
                    elif isinstance(attr, (list, tuple)) and len(attr) > 0:
                        if hasattr(attr[0], 'nbytes'):
                            memory_bytes += sum(item.nbytes for item in attr if hasattr(item, 'nbytes'))
            
            return memory_bytes / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0
    
    def _select_best_model(self) -> Tuple[str, Any]:
        """Select best model based on primary metric and configuration."""
        if not self.model_performances:
            raise ValueError("No models have been trained")
        
        if self.config and self.config.optimization.multi_objective:
            return self._select_best_multi_objective()
        else:
            return self._select_best_single_objective()
    
    def _select_best_single_objective(self) -> Tuple[str, Any]:
        """Select best model based on single primary metric."""
        best_model_name = None
        best_score = float('-inf')
        
        primary_metric = None
        if self.config and self.config.evaluation.primary_metric:
            primary_metric = self.config.evaluation.primary_metric
        
        for model_name, performance in self.model_performances.items():
            # Use cross-validation score if available, otherwise validation score
            if performance.cv_metrics:
                score = performance.cv_metrics.primary_score
            else:
                score = performance.val_metrics.primary_score
            
            # Check if this metric should be minimized
            if primary_metric and performance.val_metrics.get_metric(primary_metric):
                metric_obj = performance.val_metrics.get_metric(primary_metric)
                if not metric_obj.higher_is_better:
                    score = -score  # Convert to maximization problem
            
            if score > best_score:
                best_score = score
                best_model_name = model_name
        
        if best_model_name is None:
            raise ValueError("Could not select best model")
        
        return best_model_name, self.trained_models[best_model_name]
    
    def _select_best_multi_objective(self) -> Tuple[str, Any]:
        """Select best model using multi-objective optimization."""
        # Calculate Pareto dominance
        self._calculate_pareto_ranking()
        
        # Select model with best Pareto rank, then by composite score
        best_model_name = None
        best_rank = float('inf')
        best_composite = float('-inf')
        
        for model_name, performance in self.model_performances.items():
            if (performance.pareto_rank < best_rank or 
                (performance.pareto_rank == best_rank and 
                 performance.composite_score > best_composite)):
                best_rank = performance.pareto_rank
                best_composite = performance.composite_score
                best_model_name = model_name
        
        if best_model_name is None:
            raise ValueError("Could not select best model")
        
        return best_model_name, self.trained_models[best_model_name]
    
    def _calculate_pareto_ranking(self):
        """Calculate Pareto ranking for multi-objective optimization."""
        if not self.config or not self.config.optimization.optimization_metrics:
            return
        
        optimization_metrics = self.config.optimization.optimization_metrics
        models = list(self.model_performances.keys())
        n_models = len(models)
        
        # Get metric values for all models
        metric_values = {}
        for metric in optimization_metrics:
            metric_values[metric] = []
            for model_name in models:
                performance = self.model_performances[model_name]
                score = performance.get_metric_score(metric, 'val')
                if score is None:
                    score = 0.0
                
                # Handle minimization metrics
                metric_obj = performance.val_metrics.get_metric(metric)
                if metric_obj and not metric_obj.higher_is_better:
                    score = -score
                
                metric_values[metric].append(score)
        
        # Calculate dominance
        dominance_count = [0] * n_models
        dominated_by = [[] for _ in range(n_models)]
        
        for i in range(n_models):
            for j in range(n_models):
                if i != j:
                    dominates = True
                    strictly_better = False
                    
                    for metric in optimization_metrics:
                        val_i = metric_values[metric][i]
                        val_j = metric_values[metric][j]
                        
                        if val_i < val_j:
                            dominates = False
                            break
                        elif val_i > val_j:
                            strictly_better = True
                    
                    if dominates and strictly_better:
                        dominance_count[i] += 1
                        dominated_by[j].append(i)
        
        # Assign Pareto ranks
        pareto_ranks = [0] * n_models
        current_front = []
        
        # Find first front (non-dominated solutions)
        for i in range(n_models):
            if len(dominated_by[i]) == 0:
                pareto_ranks[i] = 1
                current_front.append(i)
        
        # Find subsequent fronts
        rank = 1
        while current_front:
            next_front = []
            for i in current_front:
                for j in range(n_models):
                    if i in dominated_by[j]:
                        dominated_by[j].remove(i)
                        if len(dominated_by[j]) == 0:
                            pareto_ranks[j] = rank + 1
                            next_front.append(j)
            
            current_front = next_front
            rank += 1
        
        # Calculate composite scores using weighted sum
        for i, model_name in enumerate(models):
            performance = self.model_performances[model_name]
            performance.pareto_rank = pareto_ranks[i]
            performance.dominance_count = dominance_count[i]
            
            # Calculate composite score
            composite = 0.0
            total_weight = 0.0
            
            for metric in optimization_metrics:
                weight = self.config.optimization.metric_weights.get(metric, 1.0)
                score = metric_values[metric][i]
                composite += weight * score
                total_weight += weight
            
            if total_weight > 0:
                performance.composite_score = composite / total_weight
            else:
                performance.composite_score = composite
    
    def fit(self, X: DataFrame, y: Series) -> 'EnhancedAutoModelTrainer':
        """
        Train multiple models with comprehensive evaluation.
        
        Args:
            X: Feature matrix
            y: Target variable
            
        Returns:
            Self for method chaining
        """
        if self.verbose:
            print("🚀 Starting Enhanced AutoML Training")
            print("=" * 50)
        
        # Detect task type
        self.task_type = self._detect_task_type(y)
        if self.verbose:
            print(f"📊 Detected task type: {self.task_type}")
        
        # Configure metrics for detected task type
        if self.config:
            self.config.evaluation.set_task_defaults(self.task_type)
            self.config.optimization.set_task_defaults(self.task_type)
        
        # Split data for validation
        test_size = 0.2
        if self.config and hasattr(self.config.evaluation, 'holdout_size'):
            test_size = self.config.evaluation.holdout_size
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, 
            random_state=self.random_state,
            stratify=y if self.task_type == 'classification' else None
        )
        
        if self.verbose:
            print(f"📈 Training set: {X_train.shape[0]} samples")
            print(f"📊 Validation set: {X_val.shape[0]} samples")
            selected_metrics = self._get_selected_metrics(self.task_type)
            print(f"🎯 Evaluation metrics: {selected_metrics}")
        
        # Train all models
        for model_name in self.models:
            try:
                performance = self._train_single_model(
                    model_name, X_train, y_train, X_val, y_val, self.task_type
                )
                self.model_performances[model_name] = performance
                
            except Exception as e:
                if self.verbose:
                    print(f"    ❌ Failed to train {model_name}: {str(e)}")
                continue
        
        if not self.model_performances:
            raise ValueError("No models were successfully trained")
        
        # Select best model
        self.best_model_name, self.best_model = self._select_best_model()
        
        if self.verbose:
            print(f"\n🏆 Best model: {self.best_model_name}")
            best_performance = self.model_performances[self.best_model_name]
            print(f"🎯 Best score: {best_performance.get_primary_score():.4f}")
            
            if self.config and self.config.optimization.multi_objective:
                print(f"📊 Pareto rank: {best_performance.pareto_rank}")
                print(f"💯 Composite score: {best_performance.composite_score:.4f}")
        
        return self
    
    def predict(self, X: DataFrame) -> np.ndarray:
        """Make predictions using the best model."""
        if self.best_model is None:
            raise ValueError("No model has been trained. Call fit() first.")
        
        return self.best_model.predict(X)
    
    def predict_proba(self, X: DataFrame) -> np.ndarray:
        """Make probability predictions using the best model (classification only)."""
        if self.best_model is None:
            raise ValueError("No model has been trained. Call fit() first.")
        
        if self.task_type != 'classification':
            raise ValueError("predict_proba is only available for classification tasks")
        
        if not hasattr(self.best_model, 'predict_proba'):
            raise ValueError(f"Model {self.best_model_name} does not support probability predictions")
        
        return self.best_model.predict_proba(X)
    
    def get_model_comparison(self) -> DataFrame:
        """Get comprehensive comparison of all trained models."""
        if not self.model_performances:
            raise ValueError("No models have been trained")
        
        comparison_data = []
        
        for model_name, performance in self.model_performances.items():
            row = {
                'model': model_name,
                'primary_score': performance.get_primary_score(),
                'training_time': performance.training_time,
                'prediction_time': performance.prediction_time,
                'memory_usage': performance.memory_usage
            }
            
            # Add all validation metrics
            for metric_name, metric in performance.val_metrics.all_metrics.items():
                row[f'val_{metric_name}'] = metric.value
            
            # Add cross-validation scores if available
            if performance.cv_metrics:
                for metric_name, metric in performance.cv_metrics.all_metrics.items():
                    row[f'cv_{metric_name}'] = metric.value
            
            # Add multi-objective scores if available
            if performance.pareto_rank is not None:
                row['pareto_rank'] = performance.pareto_rank
                row['dominance_count'] = performance.dominance_count
                row['composite_score'] = performance.composite_score
            
            comparison_data.append(row)
        
        return DataFrame(comparison_data).sort_values('primary_score', ascending=False)
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Get comprehensive training summary."""
        if not self.model_performances:
            return {"status": "No models trained"}
        
        summary = {
            "task_type": self.task_type,
            "models_trained": len(self.model_performances),
            "best_model": self.best_model_name,
            "best_score": self.model_performances[self.best_model_name].get_primary_score(),
            "total_training_time": sum(p.training_time for p in self.model_performances.values()),
            "metrics_evaluated": list(next(iter(self.model_performances.values())).val_metrics.all_metrics.keys()),
            "model_performances": {name: perf.get_primary_score() for name, perf in self.model_performances.items()}
        }
        
        # Add multi-objective information if available
        if self.config and self.config.optimization.multi_objective:
            summary["optimization_type"] = "multi_objective"
            summary["optimization_metrics"] = self.config.optimization.optimization_metrics
            summary["pareto_front_size"] = len([p for p in self.model_performances.values() if p.pareto_rank == 1])
        else:
            summary["optimization_type"] = "single_objective"
            if self.config:
                summary["primary_metric"] = self.config.evaluation.primary_metric
        
        return summary
    
    def save_model(self, filepath: str, model_name: Optional[str] = None):
        """Save trained model to file."""
        if model_name is None:
            model_name = self.best_model_name
            model = self.best_model
        else:
            model = self.trained_models.get(model_name)
        
        if model is None:
            raise ValueError(f"Model {model_name} not found")
        
        # Save model with metadata
        model_data = {
            'model': model,
            'model_name': model_name,
            'task_type': self.task_type,
            'performance': self.model_performances.get(model_name),
            'config': self.config,
            'feature_names': getattr(model, 'feature_names_in_', None)
        }
        
        joblib.dump(model_data, filepath)
        
        if self.verbose:
            print(f"💾 Model {model_name} saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file."""
        model_data = joblib.load(filepath)
        
        self.best_model = model_data['model']
        self.best_model_name = model_data['model_name']
        self.task_type = model_data['task_type']
        
        if 'performance' in model_data:
            self.model_performances[self.best_model_name] = model_data['performance']
        
        if 'config' in model_data:
            self.config = model_data['config']
        
        self.trained_models[self.best_model_name] = self.best_model
        
        if self.verbose:
            print(f"📂 Model {self.best_model_name} loaded from {filepath}")
    
    def generate_report(self) -> str:
        """Generate comprehensive training report."""
        if not self.model_performances:
            return "No models have been trained."
        
        lines = [
            "🤖 Enhanced AutoML Training Report",
            "=" * 50,
            "",
            f"📊 Task Type: {self.task_type}",
            f"🏆 Best Model: {self.best_model_name}",
            f"🎯 Best Score: {self.model_performances[self.best_model_name].get_primary_score():.4f}",
            f"📈 Models Trained: {len(self.model_performances)}",
            "",
            "📋 Model Performance Summary:",
            "-" * 30
        ]
        
        # Sort models by performance
        sorted_models = sorted(
            self.model_performances.items(),
            key=lambda x: x[1].get_primary_score(),
            reverse=True
        )
        
        for i, (model_name, performance) in enumerate(sorted_models, 1):
            lines.append(f"{i}. {model_name}:")
            lines.append(f"   Score: {performance.get_primary_score():.4f}")
            lines.append(f"   Time: {performance.training_time:.2f}s")
            lines.append(f"   Memory: {performance.memory_usage:.2f}MB")
            
            if performance.pareto_rank is not None:
                lines.append(f"   Pareto Rank: {performance.pareto_rank}")
            
            lines.append("")
        
        # Add best model detailed metrics
        best_performance = self.model_performances[self.best_model_name]
        lines.extend([
            f"🔍 Detailed Metrics for {self.best_model_name}:",
            "-" * 40
        ])
        
        for metric in best_performance.val_metrics.get_best_metrics(10):
            direction = "↗" if metric.higher_is_better else "↘"
            lines.append(f"  • {metric.name}: {metric.value:.4f} {direction}")
        
        return "\n".join(lines)


# Convenience function for quick training
def train_auto_model(X: DataFrame, 
                    y: Series, 
                    task_type: Optional[str] = None,
                    config: Optional[AutoMLConfig] = None,
                    **kwargs) -> Tuple[Any, Dict[str, Any]]:
    """
    Convenience function for quick model training with comprehensive evaluation.
    
    Args:
        X: Feature matrix
        y: Target variable
        task_type: 'classification' or 'regression' (auto-detected if None)
        config: AutoML configuration
        **kwargs: Additional arguments for EnhancedAutoModelTrainer
        
    Returns:
        Tuple of (best_model, training_summary)
    """
    trainer = EnhancedAutoModelTrainer(config=config, task_type=task_type, **kwargs)
    trainer.fit(X, y)
    
    return trainer.best_model, trainer.get_training_summary()


# Legacy compatibility - keep AutoModelTrainer as an alias
AutoModelTrainer = EnhancedAutoModelTrainer