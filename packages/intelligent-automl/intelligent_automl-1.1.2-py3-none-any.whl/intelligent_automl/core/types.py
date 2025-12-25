# ===================================
# FILE: automl_framework/core/types.py
# LOCATION: /automl_framework/automl_framework/core/types.py
# ===================================

"""
Type definitions and type aliases for the AutoML framework.

This module provides centralized type definitions, making the codebase
more maintainable and enabling better IDE support and static type checking.
"""

from typing import (
    Any, Dict, List, Optional, Union, Tuple, Callable, 
    TypeVar, Generic, Protocol, Literal, TypedDict
)
import pandas as pd
import numpy as np
from enum import Enum, auto
from dataclasses import dataclass

# ================================
# Basic Type Aliases
# ================================

# Data types
DataFrame = pd.DataFrame
Series = pd.Series
NDArray = np.ndarray
Matrix = Union[DataFrame, NDArray]
Vector = Union[Series, NDArray]

# Parameter types
Hyperparameters = Dict[str, Any]
Metrics = Dict[str, float]
Features = List[str]
TargetValues = Union[Series, NDArray, List]

# File and path types
FilePath = Union[str, 'os.PathLike']
DataSource = Union[FilePath, DataFrame]

# Numeric types
Score = float
Probability = float
Weight = float

# ================================
# Enums for Categorical Values
# ================================

class TaskType(Enum):
    """Types of machine learning tasks."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"


class ModelType(Enum):
    """Types of machine learning models."""
    # Classical ML
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR_REGRESSION = "linear_regression"
    SVM = "svm"
    KNN = "knn"
    DECISION_TREE = "decision_tree"
    NAIVE_BAYES = "naive_bayes"
    
    # Ensemble methods
    VOTING_CLASSIFIER = "voting_classifier"
    VOTING_REGRESSOR = "voting_regressor"
    STACKING_CLASSIFIER = "stacking_classifier"
    STACKING_REGRESSOR = "stacking_regressor"
    
    # Deep learning
    NEURAL_NETWORK = "neural_network"
    CNN = "cnn"
    RNN = "rnn"
    LSTM = "lstm"
    TRANSFORMER = "transformer"


class ScalingMethod(Enum):
    """Feature scaling methods."""
    MINMAX = "minmax"
    STANDARD = "standard"
    ROBUST = "robust"
    QUANTILE = "quantile"
    NONE = "none"


class EncodingMethod(Enum):
    """Categorical encoding methods."""
    ONEHOT = "onehot"
    LABEL = "label"
    TARGET = "target"
    ORDINAL = "ordinal"
    BINARY = "binary"
    FREQUENCY = "frequency"
    NONE = "none"


class OptimizationMethod(Enum):
    """Hyperparameter optimization methods."""
    GRID_SEARCH = "grid"
    RANDOM_SEARCH = "random"
    BAYESIAN = "bayesian"
    OPTUNA = "optuna"
    GENETIC = "genetic"


class CrossValidationStrategy(Enum):
    """Cross-validation strategies."""
    K_FOLD = "kfold"
    STRATIFIED_K_FOLD = "stratified"
    TIME_SERIES_SPLIT = "time_series"
    GROUP_K_FOLD = "group"
    LEAVE_ONE_OUT = "loo"


class DataFormat(Enum):
    """Supported data formats."""
    CSV = "csv"
    EXCEL = "xlsx"
    JSON = "json"
    PARQUET = "parquet"
    PICKLE = "pkl"
    HDF5 = "h5"


# ================================
# TypedDict Definitions
# ================================

class ModelResult(TypedDict):
    """Result from model training."""
    model: Any
    scores: Metrics
    training_time: float
    feature_importance: Optional[Dict[str, float]]
    hyperparameters: Hyperparameters


class EvaluationResult(TypedDict):
    """Result from model evaluation."""
    test_scores: Metrics
    cv_scores: Optional[List[float]]
    cv_mean: Optional[float]
    cv_std: Optional[float]
    predictions: List[Any]
    probabilities: Optional[List[List[float]]]


class OptimizationResult(TypedDict):
    """Result from hyperparameter optimization."""
    best_params: Hyperparameters
    best_score: Score
    optimization_history: List[Dict[str, Any]]
    total_trials: int
    optimization_time: float


class PipelineResult(TypedDict):
    """Result from complete pipeline execution."""
    config: Dict[str, Any]
    model_result: ModelResult
    evaluation_result: EvaluationResult
    optimization_result: Optional[OptimizationResult]
    pipeline_time: float
    data_info: Dict[str, Any]


class DataInfo(TypedDict):
    """Information about dataset."""
    shape: Tuple[int, int]
    feature_count: int
    target_type: str
    missing_values: int
    duplicate_rows: int
    memory_usage: float


# ================================
# Protocol Definitions
# ================================

class Fittable(Protocol):
    """Protocol for objects that can be fitted to data."""
    
    def fit(self, X: DataFrame, y: Optional[Series] = None) -> 'Fittable':
        """Fit the object to data."""
        ...


class Transformable(Protocol):
    """Protocol for objects that can transform data."""
    
    def transform(self, X: DataFrame) -> DataFrame:
        """Transform the data."""
        ...


class Predictable(Protocol):
    """Protocol for objects that can make predictions."""
    
    def predict(self, X: DataFrame) -> NDArray:
        """Make predictions on data."""
        ...


class Explainable(Protocol):
    """Protocol for objects that can provide explanations."""
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance scores."""
        ...


# ================================
# Generic Types
# ================================

T = TypeVar('T')
ModelT = TypeVar('ModelT', bound='ModelStrategy')
ProcessorT = TypeVar('ProcessorT', bound='DataProcessor')

class Result(Generic[T]):
    """Generic result wrapper with success/failure state."""
    
    def __init__(self, value: Optional[T] = None, error: Optional[Exception] = None):
        self.value = value
        self.error = error
        self.is_success = error is None
    
    def unwrap(self) -> T:
        """Get the value or raise the error."""
        if self.error:
            raise self.error
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        """Get the value or return default."""
        return self.value if self.is_success else default


# ================================
# Function Type Aliases
# ================================

MetricFunction = Callable[[NDArray, NDArray], float]
TransformFunction = Callable[[DataFrame], DataFrame]
ValidationFunction = Callable[[DataFrame], bool]
LoggingFunction = Callable[[str], None]

# Callback types for training
OnEpochStart = Callable[[int, Dict[str, Any]], None]
OnEpochEnd = Callable[[int, Dict[str, Any]], None]
OnTrainingStart = Callable[[Dict[str, Any]], None]
OnTrainingEnd = Callable[[Dict[str, Any]], None]

# ================================
# Data Structure Types
# ================================

@dataclass
class FeatureInfo:
    """Information about a feature column."""
    name: str
    dtype: str
    is_numeric: bool
    is_categorical: bool
    unique_count: int
    missing_count: int
    missing_percentage: float


@dataclass
class ModelMetadata:
    """Metadata for a trained model."""
    model_type: str
    task_type: str
    training_time: float
    feature_count: int
    target_classes: Optional[List[str]]
    hyperparameters: Hyperparameters
    performance_metrics: Metrics
    created_at: str
    framework_version: str


@dataclass
class ExperimentInfo:
    """Information about an experiment run."""
    experiment_id: str
    run_id: str
    config: Dict[str, Any]
    start_time: str
    end_time: Optional[str]
    status: str
    metrics: Metrics
    artifacts: Dict[str, str]


# ================================
# Search Space Types
# ================================

class SearchSpace(TypedDict):
    """Type for hyperparameter search spaces."""
    param_name: str
    param_type: Literal["int", "float", "categorical", "bool"]
    low: Optional[float]
    high: Optional[float]
    choices: Optional[List[Any]]
    log: Optional[bool]


SearchSpaceDict = Dict[str, SearchSpace]

# ================================
# Pipeline Types
# ================================

PipelineStep = Tuple[str, Any]  # (step_name, processor)
PipelineSteps = List[PipelineStep]

class PipelineConfig(TypedDict):
    """Configuration for a processing pipeline."""
    steps: List[Dict[str, Any]]
    parallel: bool
    memory: Optional[str]
    verbose: bool


# ================================
# Validation Types
# ================================

ValidationRule = Callable[[DataFrame], Tuple[bool, str]]
ValidationRules = List[ValidationRule]

class ValidationReport(TypedDict):
    """Report from data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


# ================================
# Monitoring Types
# ================================

class TrainingEvent(TypedDict):
    """Event data for training monitoring."""
    event_type: str
    timestamp: str
    epoch: Optional[int]
    metrics: Optional[Metrics]
    additional_data: Dict[str, Any]


EventHandler = Callable[[TrainingEvent], None]

# ================================
# Configuration Types
# ================================

class DatabaseConfig(TypedDict):
    """Database connection configuration."""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl: bool


class APIConfig(TypedDict):
    """API configuration."""
    host: str
    port: int
    debug: bool
    cors_origins: List[str]
    rate_limit: int


# ================================
# Export Types
# ================================

class ModelExport(TypedDict):
    """Model export configuration."""
    format: Literal["pickle", "joblib", "onnx", "pmml"]
    include_preprocessing: bool
    include_metadata: bool
    compression: Optional[str]


# ================================
# Utility Types
# ================================

class VersionInfo(TypedDict):
    """Version information."""
    major: int
    minor: int
    patch: int
    pre_release: Optional[str]
    build: Optional[str]


# Common union types
NumericValue = Union[int, float]
OptionalDataFrame = Optional[DataFrame]
OptionalSeries = Optional[Series]
StringOrList = Union[str, List[str]]

# Time-related types
Duration = Union[int, float]  # seconds
Timestamp = Union[str, 'datetime.datetime']

# Resource-related types
MemoryLimit = Union[str, int]  # e.g., "1GB" or bytes
CPUCount = Union[int, Literal["auto"]]

# ================================
# Constants
# ================================

# Default values
DEFAULT_RANDOM_STATE = 42
DEFAULT_TEST_SIZE = 0.2
DEFAULT_CV_FOLDS = 5
DEFAULT_N_JOBS = -1

# Limits
MAX_FEATURE_COUNT = 10000
MAX_OPTIMIZATION_TRIALS = 1000
MAX_TRAINING_TIME_HOURS = 24

# File size limits (in bytes)
MAX_CSV_SIZE = 1_000_000_000  # 1GB
MAX_EXCEL_SIZE = 100_000_000   # 100MB

# Performance thresholds
MIN_ACCURACY_THRESHOLD = 0.5
MIN_R2_THRESHOLD = 0.0