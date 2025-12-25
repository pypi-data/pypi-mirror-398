# intelligent_automl/core/config.py

"""
Enhanced Configuration management for the AutoML framework with Multi-Metric Support.

This module provides type-safe configuration classes using dataclasses
and validation logic to ensure configurations are valid.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path

# Optional yaml import with graceful fallback
try:
    import yaml
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False

from .exceptions import ConfigurationError


@dataclass
class DataConfig:
    """Configuration for data handling and loading."""
    
    file_path: str
    target_column: str
    test_size: float = 0.2
    random_state: int = 42
    validation_size: float = 0.1
    stratify: bool = True
    handle_missing_target: str = 'drop'  # 'drop' or 'impute'
    date_columns: Optional[List[str]] = None
    index_column: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 0 < self.test_size < 1:
            raise ConfigurationError("test_size must be between 0 and 1")
        
        if not 0 <= self.validation_size < 1:
            raise ConfigurationError("validation_size must be between 0 and 1")
        
        if self.test_size + self.validation_size >= 1:
            raise ConfigurationError("test_size + validation_size must be < 1")
        
        if self.handle_missing_target not in ['drop', 'impute']:
            raise ConfigurationError("handle_missing_target must be 'drop' or 'impute'")


@dataclass
class PreprocessingConfig:
    """Configuration for data preprocessing."""
    
    scaling_method: str = 'minmax'  # 'minmax', 'standard', 'robust', 'none'
    encoding_method: str = 'onehot'  # 'onehot', 'label', 'target', 'none'
    handle_missing: str = 'auto'  # 'auto', 'mean', 'median', 'mode', 'drop'
    handle_outliers: bool = False
    outlier_method: str = 'iqr'  # 'iqr', 'zscore', 'isolation_forest'
    feature_selection: bool = False
    feature_selection_method: str = 'mutual_info'  # 'mutual_info', 'chi2', 'f_test'
    feature_selection_k: int = 10
    polynomial_features: bool = False
    polynomial_degree: int = 2
    interaction_features: bool = False
    
    def __post_init__(self):
        """Validate preprocessing configuration."""
        valid_scaling = ['minmax', 'standard', 'robust', 'none']
        if self.scaling_method not in valid_scaling:
            raise ConfigurationError(f"scaling_method must be one of {valid_scaling}")
        
        valid_encoding = ['onehot', 'label', 'target', 'none']
        if self.encoding_method not in valid_encoding:
            raise ConfigurationError(f"encoding_method must be one of {valid_encoding}")
        
        valid_missing = ['auto', 'mean', 'median', 'mode', 'drop']
        if self.handle_missing not in valid_missing:
            raise ConfigurationError(f"handle_missing must be one of {valid_missing}")
        
        valid_outlier = ['iqr', 'zscore', 'isolation_forest']
        if self.outlier_method not in valid_outlier:
            raise ConfigurationError(f"outlier_method must be one of {valid_outlier}")
        
        if self.polynomial_degree < 1 or self.polynomial_degree > 5:
            raise ConfigurationError("polynomial_degree must be between 1 and 5")


@dataclass
class ModelConfig:
    """Configuration for model training."""
    
    model_type: str
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    cross_validation_folds: int = 5
    cross_validation_strategy: str = 'kfold'  # 'kfold', 'stratified', 'time_series'
    ensemble_method: Optional[str] = None  # 'voting', 'stacking', 'blending'
    ensemble_models: Optional[List[str]] = None
    auto_ensemble: bool = False
    
    def __post_init__(self):
        """Validate model configuration."""
        if self.cross_validation_folds < 2:
            raise ConfigurationError("cross_validation_folds must be >= 2")
        
        valid_cv_strategies = ['kfold', 'stratified', 'time_series']
        if self.cross_validation_strategy not in valid_cv_strategies:
            raise ConfigurationError(f"cv_strategy must be one of {valid_cv_strategies}")
        
        if self.ensemble_method:
            valid_ensemble = ['voting', 'stacking', 'blending']
            if self.ensemble_method not in valid_ensemble:
                raise ConfigurationError(f"ensemble_method must be one of {valid_ensemble}")


@dataclass
class MetricConfig:
    """Configuration for individual metrics."""
    name: str
    weight: float = 1.0  # Weight for ensemble scoring
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.weight < 0:
            raise ValueError("Metric weight must be non-negative")


@dataclass
class EvaluationConfig:
    """Enhanced configuration for comprehensive model evaluation."""
    
    # Multi-metric configuration
    metrics: List[Union[str, MetricConfig]] = field(default_factory=list)
    primary_metric: Optional[str] = None  # Main metric for model selection
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Evaluation strategy
    cross_validation: bool = True
    cv_folds: int = 5
    cv_strategy: str = 'kfold'  # 'kfold', 'stratified', 'time_series'
    holdout_evaluation: bool = True
    holdout_size: float = 0.2
    
    # Bootstrap and confidence intervals
    bootstrap_samples: int = 0  # 0 means no bootstrap
    confidence_level: float = 0.95
    
    # Output configuration
    save_predictions: bool = True
    save_feature_importance: bool = True
    save_learning_curves: bool = False
    save_confusion_matrix: bool = True  # For classification
    save_residual_plots: bool = True   # For regression
    
    # Advanced evaluation options
    enable_comprehensive_metrics: bool = True  # Use all available metrics
    enable_probabilistic_metrics: bool = True  # ROC-AUC, log-loss, etc.
    enable_fairness_metrics: bool = False     # Fairness and bias metrics
    
    # Multi-objective optimization
    enable_multi_objective: bool = False
    pareto_optimization: bool = False
    metric_weights: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and process evaluation configuration."""
        # Ensure we have some metrics
        if not self.metrics and self.enable_comprehensive_metrics:
            # Will be auto-populated based on task type
            pass
        elif not self.metrics:
            raise ValueError("Must specify metrics or enable comprehensive_metrics")
        
        # Validate CV configuration
        if self.cv_folds < 2:
            raise ValueError("cv_folds must be >= 2")
        
        valid_cv_strategies = ['kfold', 'stratified', 'time_series', 'group']
        if self.cv_strategy not in valid_cv_strategies:
            raise ValueError(f"cv_strategy must be one of {valid_cv_strategies}")
        
        # Validate holdout size
        if not 0 < self.holdout_size < 1:
            raise ValueError("holdout_size must be between 0 and 1")
        
        # Validate confidence level
        if not 0 < self.confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        
        # Process metrics to MetricConfig objects
        self._process_metrics()
    
    def _process_metrics(self):
        """Convert string metrics to MetricConfig objects."""
        processed_metrics = []
        
        for metric in self.metrics:
            if isinstance(metric, str):
                processed_metrics.append(MetricConfig(name=metric))
            elif isinstance(metric, MetricConfig):
                processed_metrics.append(metric)
            elif isinstance(metric, dict):
                processed_metrics.append(MetricConfig(**metric))
            else:
                raise ValueError(f"Invalid metric specification: {metric}")
        
        self.metrics = processed_metrics
    
    def get_metric_names(self) -> List[str]:
        """Get list of metric names."""
        return [m.name for m in self.metrics if m.enabled]
    
    def get_enabled_metrics(self) -> List[MetricConfig]:
        """Get list of enabled metrics."""
        return [m for m in self.metrics if m.enabled]
    
    def set_task_defaults(self, task_type: str):
        """Set default metrics based on task type."""
        if not self.metrics and self.enable_comprehensive_metrics:
            if task_type == 'classification':
                default_metrics = [
                    'accuracy', 'balanced_accuracy', 'f1_weighted', 
                    'precision_weighted', 'recall_weighted', 'matthews_corrcoef'
                ]
                if self.enable_probabilistic_metrics:
                    default_metrics.extend(['roc_auc', 'average_precision', 'log_loss'])
            else:  # regression
                default_metrics = [
                    'r2', 'explained_variance', 'mae', 'mse', 'rmse', 'mape'
                ]
            
            self.metrics = [MetricConfig(name=metric) for metric in default_metrics]
        
        # Set primary metric if not specified
        if not self.primary_metric:
            if task_type == 'classification':
                self.primary_metric = 'f1_weighted'
            else:
                self.primary_metric = 'r2'


@dataclass
class OptimizationConfig:
    """Enhanced configuration for hyperparameter optimization with multi-metric support."""
    
    enabled: bool = False
    method: str = 'random'  # 'grid', 'random', 'bayesian', 'optuna'
    n_trials: int = 50
    timeout_minutes: Optional[int] = None
    
    # Multi-objective optimization
    optimization_metrics: List[str] = field(default_factory=list)  # Multiple metrics to optimize
    primary_metric: str = 'accuracy'  # Primary metric for single-objective
    optimization_direction: Dict[str, str] = field(default_factory=dict)  # per-metric direction
    
    # Advanced optimization
    multi_objective: bool = False
    pareto_optimization: bool = False
    scalarization_method: str = 'weighted_sum'  # 'weighted_sum', 'tchebycheff', 'augmented_tchebycheff'
    metric_weights: Dict[str, float] = field(default_factory=dict)
    
    # Search configuration
    search_space: Dict[str, Any] = field(default_factory=dict)
    early_stopping: bool = True
    early_stopping_rounds: int = 10
    early_stopping_metric: Optional[str] = None
    
    # Advanced features
    pruning: bool = True  # For Optuna
    sampler: str = 'tpe'  # 'tpe', 'cmaes', 'random'
    
    def __post_init__(self):
        """Validate optimization configuration."""
        valid_methods = ['grid', 'random', 'bayesian', 'optuna']
        if self.method not in valid_methods:
            raise ValueError(f"optimization method must be one of {valid_methods}")
        
        if self.n_trials < 1:
            raise ValueError("n_trials must be >= 1")
        
        valid_scalarization = ['weighted_sum', 'tchebycheff', 'augmented_tchebycheff']
        if self.scalarization_method not in valid_scalarization:
            raise ValueError(f"scalarization_method must be one of {valid_scalarization}")
        
        # Set up multi-objective if multiple metrics specified
        if len(self.optimization_metrics) > 1:
            self.multi_objective = True
        elif len(self.optimization_metrics) == 1:
            self.primary_metric = self.optimization_metrics[0]
        
        # Validate metric weights sum to 1 for weighted methods
        if self.metric_weights and self.scalarization_method == 'weighted_sum':
            total_weight = sum(self.metric_weights.values())
            if abs(total_weight - 1.0) > 1e-6:
                raise ValueError("Metric weights must sum to 1.0 for weighted_sum scalarization")
    
    def get_optimization_direction(self, metric: str) -> str:
        """Get optimization direction for a metric."""
        return self.optimization_direction.get(metric, 'maximize')
    
    def set_task_defaults(self, task_type: str):
        """Set default optimization configuration based on task type."""
        if not self.optimization_metrics:
            if task_type == 'classification':
                self.optimization_metrics = ['f1_weighted']
                self.optimization_direction = {'f1_weighted': 'maximize'}
            else:
                self.optimization_metrics = ['r2']
                self.optimization_direction = {'r2': 'maximize'}
        
        if not self.early_stopping_metric:
            self.early_stopping_metric = self.primary_metric


@dataclass
class TrainingConfig:
    """Configuration for the training process."""
    
    max_time_minutes: Optional[int] = None
    early_stopping: bool = True
    early_stopping_patience: int = 10
    save_intermediate: bool = False
    checkpoint_frequency: int = 10  # epochs
    verbose: bool = True
    log_level: str = 'INFO'
    random_seed: int = 42
    n_jobs: int = -1  # number of parallel jobs
    memory_limit_gb: Optional[float] = None
    
    def __post_init__(self):
        """Validate training configuration."""
        if self.max_time_minutes is not None and self.max_time_minutes <= 0:
            raise ConfigurationError("max_time_minutes must be positive")
        
        if self.early_stopping_patience < 1:
            raise ConfigurationError("early_stopping_patience must be >= 1")
        
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if self.log_level not in valid_log_levels:
            raise ConfigurationError(f"log_level must be one of {valid_log_levels}")
        
        if self.checkpoint_frequency < 1:
            raise ConfigurationError("checkpoint_frequency must be >= 1")


@dataclass
class ModelComparisonConfig:
    """Configuration for comparing multiple models with multiple metrics."""
    
    enable_model_comparison: bool = True
    models_to_compare: List[str] = field(default_factory=list)
    
    # Comparison methods
    statistical_tests: bool = True
    test_type: str = 'wilcoxon'  # 'wilcoxon', 'friedman', 'ttest'
    significance_level: float = 0.05
    
    # Ranking and selection
    ranking_method: str = 'pareto'  # 'pareto', 'weighted_sum', 'borda_count'
    consensus_ranking: bool = True
    
    # Visualization
    generate_comparison_plots: bool = True
    radar_charts: bool = True
    performance_profiles: bool = True
    
    def __post_init__(self):
        """Validate model comparison configuration."""
        valid_tests = ['wilcoxon', 'friedman', 'ttest', 'mcnemar']
        if self.test_type not in valid_tests:
            raise ValueError(f"test_type must be one of {valid_tests}")
        
        valid_ranking = ['pareto', 'weighted_sum', 'borda_count', 'topsis']
        if self.ranking_method not in valid_ranking:
            raise ValueError(f"ranking_method must be one of {valid_ranking}")
        
        if not 0 < self.significance_level < 1:
            raise ValueError("significance_level must be between 0 and 1")


@dataclass
class LoggingConfig:
    """Configuration for logging and monitoring."""
    
    log_to_file: bool = True
    log_to_console: bool = True
    log_file_path: str = 'automl.log'
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    rotate_logs: bool = True
    max_log_size_mb: int = 10
    backup_count: int = 5
    track_metrics: bool = True
    metrics_backend: str = 'local'  # 'local', 'mlflow', 'wandb'
    experiment_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate logging configuration."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if self.log_level not in valid_levels:
            raise ConfigurationError(f"log_level must be one of {valid_levels}")
        
        valid_backends = ['local', 'mlflow', 'wandb']
        if self.metrics_backend not in valid_backends:
            raise ConfigurationError(f"metrics_backend must be one of {valid_backends}")


@dataclass
class AutoMLConfig:
    """Enhanced AutoML configuration with comprehensive multi-metric support."""
    
    # Core configuration sections
    data: 'DataConfig'
    model: 'ModelConfig' 
    training: 'TrainingConfig'
    evaluation: EvaluationConfig
    optimization: OptimizationConfig
    model_comparison: ModelComparisonConfig = field(default_factory=ModelComparisonConfig)
    
    # Global settings
    task_type: Optional[str] = None  # Auto-detected if None
    random_seed: int = 42
    verbose: bool = True
    log_level: str = 'INFO'
    
    # Output configuration
    output_dir: str = './automl_results'
    save_models: bool = True
    save_reports: bool = True
    save_visualizations: bool = True
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Auto-detect task type if not specified
        if self.task_type is None:
            self.task_type = self._detect_task_type()
        
        # Set task-specific defaults
        if self.task_type:
            self.evaluation.set_task_defaults(self.task_type)
            self.optimization.set_task_defaults(self.task_type)
    
    def _detect_task_type(self) -> Optional[str]:
        """Detect task type from metrics configuration."""
        classification_metrics = {
            'accuracy', 'precision', 'recall', 'f1', 'roc_auc', 
            'balanced_accuracy', 'matthews_corrcoef', 'cohen_kappa'
        }
        regression_metrics = {
            'r2', 'mse', 'mae', 'rmse', 'explained_variance', 'mape'
        }
        
        # Check evaluation metrics
        eval_metric_names = self.evaluation.get_metric_names()
        opt_metrics = set(self.optimization.optimization_metrics)
        all_metrics = set(eval_metric_names) | opt_metrics
        
        has_classification = bool(all_metrics & classification_metrics)
        has_regression = bool(all_metrics & regression_metrics)
        
        if has_classification and not has_regression:
            return 'classification'
        elif has_regression and not has_classification:
            return 'regression'
        else:
            return None  # Ambiguous or no clear indication
    
    @classmethod
    def create_default(cls, task_type: str = 'classification') -> 'AutoMLConfig':
        """Create a default configuration for a specific task type."""
        # Default evaluation config with comprehensive metrics
        evaluation = EvaluationConfig(
            enable_comprehensive_metrics=True,
            enable_probabilistic_metrics=True,
            cross_validation=True,
            cv_folds=5,
            save_predictions=True,
            save_feature_importance=True
        )
        
        # Default optimization config
        optimization = OptimizationConfig(
            enabled=True,
            method='optuna',
            n_trials=100,
            multi_objective=False,
            early_stopping=True
        )
        
        # Model comparison config
        model_comparison = ModelComparisonConfig(
            enable_model_comparison=True,
            statistical_tests=True,
            generate_comparison_plots=True
        )
        
        config = cls(
            data=DataConfig(file_path='', target_column=''),
            model=ModelConfig(model_type='auto'),
            training=TrainingConfig(),
            evaluation=evaluation,
            optimization=optimization,
            model_comparison=model_comparison,
            task_type=task_type
        )
        
        return config
    
    @classmethod
    def create_multi_objective(cls, 
                             task_type: str, 
                             metrics: List[str],
                             weights: Optional[Dict[str, float]] = None) -> 'AutoMLConfig':
        """Create a configuration for multi-objective optimization."""
        config = cls.create_default(task_type)
        
        # Set up multi-objective optimization
        config.optimization.multi_objective = True
        config.optimization.optimization_metrics = metrics
        config.optimization.pareto_optimization = True
        
        if weights:
            config.optimization.metric_weights = weights
            config.optimization.scalarization_method = 'weighted_sum'
        
        # Set evaluation metrics to match optimization metrics
        config.evaluation.metrics = [MetricConfig(name=metric) for metric in metrics]
        config.evaluation.enable_multi_objective = True
        
        return config
    
    @classmethod
    def create_interpretable(cls, task_type: str = 'classification') -> 'AutoMLConfig':
        """Create a configuration focused on interpretable models (e.g., for healthcare)."""
        config = cls.create_default(task_type)
        
        # Focus on interpretable models
        config.model.model_type = 'interpretable'
        
        # Enhanced evaluation for interpretability
        config.evaluation.save_feature_importance = True
        config.evaluation.enable_comprehensive_metrics = True
        
        return config
    
    def validate(self) -> List[str]:
        """Validate the entire configuration and return any issues."""
        errors = []
        
        try:
            # Validate task type consistency
            if self.task_type:
                detected_type = self._detect_task_type()
                if detected_type and detected_type != self.task_type:
                    errors.append(f"Task type mismatch: specified {self.task_type}, detected {detected_type}")
            
            # Validate metric consistency between evaluation and optimization
            eval_metrics = set(self.evaluation.get_metric_names())
            opt_metrics = set(self.optimization.optimization_metrics)
            
            if opt_metrics and not opt_metrics.issubset(eval_metrics):
                missing = opt_metrics - eval_metrics
                errors.append(f"Optimization metrics not in evaluation metrics: {missing}")
            
            # Validate multi-objective configuration
            if self.optimization.multi_objective:
                if len(self.optimization.optimization_metrics) < 2:
                    errors.append("Multi-objective optimization requires at least 2 metrics")
                
                if self.optimization.metric_weights:
                    weight_metrics = set(self.optimization.metric_weights.keys())
                    if not weight_metrics.issubset(opt_metrics):
                        missing = weight_metrics - opt_metrics
                        errors.append(f"Metric weights specified for non-optimization metrics: {missing}")
            
            # Validate directory paths
            output_path = Path(self.output_dir)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create output directory {self.output_dir}: {str(e)}")
        
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def save_json(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    def save_yaml(self, filepath: str):
        """Save configuration to YAML file."""
        if not HAS_YAML:
            raise ImportError("PyYAML is required for YAML functionality. Install with: pip install pyyaml")
        
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    @classmethod
    def load_json(cls, filepath: str) -> 'AutoMLConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    @classmethod
    def load_yaml(cls, filepath: str) -> 'AutoMLConfig':
        """Load configuration from YAML file."""
        if not HAS_YAML:
            raise ImportError("PyYAML is required for YAML functionality. Install with: pip install pyyaml")
        
        with open(filepath, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AutoMLConfig':
        """Create configuration from dictionary."""
        # This would need proper implementation to handle nested dataclasses
        # For now, simplified version
        return cls(**config_dict)


# Example configurations for different use cases
def create_classification_config() -> AutoMLConfig:
    """Example configuration for classification with comprehensive metrics."""
    return AutoMLConfig.create_default('classification')


def create_regression_config() -> AutoMLConfig:
    """Example configuration for regression with comprehensive metrics."""
    return AutoMLConfig.create_default('regression')


def create_multi_objective_classification() -> AutoMLConfig:
    """Example multi-objective classification configuration."""
    metrics = ['f1_weighted', 'precision_weighted', 'roc_auc']
    weights = {'f1_weighted': 0.5, 'precision_weighted': 0.3, 'roc_auc': 0.2}
    return AutoMLConfig.create_multi_objective('classification', metrics, weights)


def create_comprehensive_evaluation_config() -> AutoMLConfig:
    """Configuration with all available metrics enabled."""
    config = AutoMLConfig.create_default('classification')
    
    # Enable all advanced features
    config.evaluation.enable_comprehensive_metrics = True
    config.evaluation.enable_probabilistic_metrics = True
    config.evaluation.enable_fairness_metrics = True
    config.evaluation.bootstrap_samples = 1000
    config.evaluation.save_learning_curves = True
    config.evaluation.save_confusion_matrix = True
    
    # Advanced model comparison
    config.model_comparison.statistical_tests = True
    config.model_comparison.consensus_ranking = True
    config.model_comparison.generate_comparison_plots = True
    
    return config