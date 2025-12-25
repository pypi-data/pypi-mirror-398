"""
Core module for the Intelligent AutoML framework.

This module provides the fundamental abstractions, configuration management,
and type definitions that form the foundation of the framework.
"""

from .base import (
    DataProcessor,
    ModelStrategy,
    Evaluator,
    HyperparameterOptimizer,
    Observer,
    Command,
    DataLoader,
    FeatureSelector,
    ModelPersistence,
    MetricTracker
)

from .config import (
    AutoMLConfig,
    DataConfig,
    PreprocessingConfig,
    ModelConfig,
    OptimizationConfig,
    TrainingConfig,
    EvaluationConfig,
    LoggingConfig
)

from .exceptions import (
    AutoMLError,
    ConfigurationError,
    DataLoadError,
    DataValidationError,
    PreprocessingError,
    ModelTrainingError,
    ModelPredictionError,
    EvaluationError,
    OptimizationError,
    PipelineError,
    PersistenceError,
    ResourceError,
    FeatureError,
    CommandExecutionError,
    ObserverError,
    AdapterError,
    ValidationError,
    TimeoutError,
    InsufficientDataError,
    UnsupportedOperationError,
    DependencyError,
    handle_sklearn_error,
    handle_data_error,
    create_error_context,
    log_and_raise
)

from .types import (
    # Basic types
    DataFrame,
    Series,
    NDArray,
    Matrix,
    Vector,
    Hyperparameters,
    Metrics,
    Features,
    TargetValues,
    FilePath,
    DataSource,
    Score,
    Probability,
    Weight,
    
    # Enums
    TaskType,
    ModelType,
    ScalingMethod,
    EncodingMethod,
    OptimizationMethod,
    CrossValidationStrategy,
    DataFormat,
    
    # TypedDict definitions
    ModelResult,
    EvaluationResult,
    OptimizationResult,
    PipelineResult,
    DataInfo,
    
    # Protocols
    Fittable,
    Transformable,
    Predictable,
    Explainable,
    
    # Generic types
    Result,
    
    # Function types
    MetricFunction,
    TransformFunction,
    ValidationFunction,
    LoggingFunction,
    OnEpochStart,
    OnEpochEnd,
    OnTrainingStart,
    OnTrainingEnd,
    
    # Data structures
    FeatureInfo,
    ModelMetadata,
    ExperimentInfo,
    SearchSpace,
    SearchSpaceDict,
    PipelineStep,
    PipelineSteps,
    PipelineConfig,
    ValidationRule,
    ValidationRules,
    ValidationReport,
    TrainingEvent,
    EventHandler,
    DatabaseConfig,
    APIConfig,
    ModelExport,
    VersionInfo,
    
    # Utility types
    NumericValue,
    OptionalDataFrame,
    OptionalSeries,
    StringOrList,
    Duration,
    Timestamp,
    MemoryLimit,
    CPUCount,
    
    # Constants
    DEFAULT_RANDOM_STATE,
    DEFAULT_TEST_SIZE,
    DEFAULT_CV_FOLDS,
    DEFAULT_N_JOBS,
    MAX_FEATURE_COUNT,
    MAX_OPTIMIZATION_TRIALS,
    MAX_TRAINING_TIME_HOURS,
    MAX_CSV_SIZE,
    MAX_EXCEL_SIZE,
    MIN_ACCURACY_THRESHOLD,
    MIN_R2_THRESHOLD
)

# Export all public interfaces
__all__ = [
    # Base classes
    "DataProcessor",
    "ModelStrategy", 
    "Evaluator",
    "HyperparameterOptimizer",
    "Observer",
    "Command",
    "DataLoader",
    "FeatureSelector",
    "ModelPersistence",
    "MetricTracker",
    
    # Configuration classes
    "AutoMLConfig",
    "DataConfig",
    "PreprocessingConfig", 
    "ModelConfig",
    "OptimizationConfig",
    "TrainingConfig",
    "EvaluationConfig",
    "LoggingConfig",
    
    # Exception classes
    "AutoMLError",
    "ConfigurationError",
    "DataLoadError",
    "DataValidationError",
    "PreprocessingError",
    "ModelTrainingError",
    "ModelPredictionError",
    "EvaluationError",
    "OptimizationError",
    "PipelineError",
    "PersistenceError",
    "ResourceError",
    "FeatureError",
    "CommandExecutionError",
    "ObserverError",
    "AdapterError",
    "ValidationError",
    "TimeoutError",
    "InsufficientDataError",
    "UnsupportedOperationError",
    "DependencyError",
    
    # Exception utilities
    "handle_sklearn_error",
    "handle_data_error",
    "create_error_context",
    "log_and_raise",
    
    # Type definitions
    "DataFrame",
    "Series", 
    "NDArray",
    "Matrix",
    "Vector",
    "Hyperparameters",
    "Metrics",
    "Features",
    "TargetValues",
    "FilePath",
    "DataSource",
    "Score",
    "Probability",
    "Weight",
    "TaskType",
    "ModelType",
    "ScalingMethod",
    "EncodingMethod",
    "OptimizationMethod",
    "CrossValidationStrategy",
    "DataFormat",
    "ModelResult",
    "EvaluationResult",
    "OptimizationResult",
    "PipelineResult",
    "DataInfo",
    "Fittable",
    "Transformable",
    "Predictable", 
    "Explainable",
    "Result",
    "MetricFunction",
    "TransformFunction",
    "ValidationFunction",
    "LoggingFunction",
    "FeatureInfo",
    "ModelMetadata",
    "ExperimentInfo",
]