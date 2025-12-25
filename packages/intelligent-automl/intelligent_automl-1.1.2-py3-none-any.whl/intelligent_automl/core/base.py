# ===================================
# FILE: automl_framework/core/base.py
# LOCATION: /automl_framework/automl_framework/core/base.py
# ===================================

"""
Abstract base classes that define the core interfaces for the AutoML framework.

These classes establish the contracts that all components must follow,
enabling polymorphism and ensuring consistent behavior across implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List
import pandas as pd
import numpy as np


class DataProcessor(ABC):
    """
    Abstract base class for all data processing components.
    
    This class defines the standard interface for data preprocessing steps
    that can be chained together in a pipeline.
    """
    
    @abstractmethod
    def fit(self, data: pd.DataFrame) -> 'DataProcessor':
        """
        Fit the processor to the data.
        
        Args:
            data: Input DataFrame to fit the processor on
            
        Returns:
            Self, to enable method chaining
            
        Raises:
            PreprocessingError: If fitting fails
        """
        pass
    
    @abstractmethod
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the data using the fitted processor.
        
        Args:
            data: Input DataFrame to transform
            
        Returns:
            Transformed DataFrame
            
        Raises:
            PreprocessingError: If transformation fails
        """
        pass
    
    def fit_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Fit the processor and transform data in one step.
        
        Args:
            data: Input DataFrame to fit and transform
            
        Returns:
            Transformed DataFrame
        """
        return self.fit(data).transform(data)
    
    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """
        Get parameters of the processor.
        
        Returns:
            Dictionary of processor parameters
        """
        pass
    
    @abstractmethod
    def set_params(self, **params) -> 'DataProcessor':
        """
        Set parameters of the processor.
        
        Args:
            **params: Parameters to set
            
        Returns:
            Self, to enable method chaining
        """
        pass


class ModelStrategy(ABC):
    """
    Abstract base class for all model training strategies.
    
    This class defines the interface for machine learning models,
    enabling the Strategy pattern for model selection.
    """
    
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> 'ModelStrategy':
        """
        Train the model on the given data.
        
        Args:
            X: Feature matrix
            y: Target vector
            **kwargs: Additional training parameters
            
        Returns:
            Self, to enable method chaining
            
        Raises:
            ModelTrainingError: If training fails
        """
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X: Feature matrix for prediction
            
        Returns:
            Array of predictions
            
        Raises:
            ModelTrainingError: If prediction fails
        """
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Predict class probabilities (for classification models).
        
        Args:
            X: Feature matrix for prediction
            
        Returns:
            Array of class probabilities, or None if not supported
        """
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance scores if available.
        
        Returns:
            Dictionary mapping feature names to importance scores,
            or None if not supported
        """
        pass
    
    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """
        Get model hyperparameters.
        
        Returns:
            Dictionary of model parameters
        """
        pass
    
    @abstractmethod
    def set_params(self, **params) -> 'ModelStrategy':
        """
        Set model hyperparameters.
        
        Args:
            **params: Parameters to set
            
        Returns:
            Self, to enable method chaining
        """
        pass
    
    @property
    @abstractmethod
    def is_fitted(self) -> bool:
        """
        Check if the model has been fitted.
        
        Returns:
            True if model is fitted, False otherwise
        """
        pass


class Evaluator(ABC):
    """
    Abstract base class for model evaluation strategies.
    
    This class defines the interface for evaluating model performance
    using various metrics appropriate for different task types.
    """
    
    @abstractmethod
    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray, 
                **kwargs) -> Dict[str, float]:
        """
        Evaluate predictions against true values.
        
        Args:
            y_true: True target values
            y_pred: Predicted values
            **kwargs: Additional evaluation parameters
            
        Returns:
            Dictionary of metric names to scores
        """
        pass
    
    @abstractmethod
    def get_supported_metrics(self) -> List[str]:
        """
        Get list of supported evaluation metrics.
        
        Returns:
            List of metric names
        """
        pass


class HyperparameterOptimizer(ABC):
    """
    Abstract base class for hyperparameter optimization strategies.
    
    This class defines the interface for optimizing model hyperparameters
    using various search strategies.
    """
    
    @abstractmethod
    def optimize(self, model_strategy: ModelStrategy, X: pd.DataFrame, 
                y: pd.Series, search_space: Dict[str, Any], 
                **kwargs) -> Dict[str, Any]:
        """
        Optimize hyperparameters for the given model.
        
        Args:
            model_strategy: Model to optimize
            X: Feature matrix
            y: Target vector
            search_space: Hyperparameter search space
            **kwargs: Additional optimization parameters
            
        Returns:
            Dictionary of optimized hyperparameters
        """
        pass
    
    @abstractmethod
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        Get history of optimization trials.
        
        Returns:
            List of trial results
        """
        pass


class Observer(ABC):
    """
    Abstract base class for observers in the Observer pattern.
    
    This class defines the interface for components that need to be
    notified of events during model training and evaluation.
    """
    
    @abstractmethod
    def on_training_start(self, context: Dict[str, Any]) -> None:
        """
        Called when training starts.
        
        Args:
            context: Training context information
        """
        pass
    
    @abstractmethod
    def on_training_end(self, context: Dict[str, Any]) -> None:
        """
        Called when training ends.
        
        Args:
            context: Training context and results
        """
        pass
    
    @abstractmethod
    def on_epoch_start(self, epoch: int, context: Dict[str, Any]) -> None:
        """
        Called at the start of each training epoch.
        
        Args:
            epoch: Current epoch number
            context: Training context information
        """
        pass
    
    @abstractmethod
    def on_epoch_end(self, epoch: int, logs: Dict[str, Any]) -> None:
        """
        Called at the end of each training epoch.
        
        Args:
            epoch: Current epoch number
            logs: Epoch metrics and logs
        """
        pass


class Command(ABC):
    """
    Abstract base class for commands in the Command pattern.
    
    This class defines the interface for encapsulating operations
    that can be executed, undone, and queued.
    """
    
    @abstractmethod
    def execute(self) -> Any:
        """
        Execute the command.
        
        Returns:
            Command execution result
            
        Raises:
            CommandExecutionError: If execution fails
        """
        pass
    
    @abstractmethod
    def undo(self) -> Any:
        """
        Undo the command execution.
        
        Returns:
            Undo operation result
            
        Raises:
            CommandExecutionError: If undo fails
        """
        pass
    
    @abstractmethod
    def can_undo(self) -> bool:
        """
        Check if the command can be undone.
        
        Returns:
            True if command can be undone, False otherwise
        """
        pass


class DataLoader(ABC):
    """
    Abstract base class for data loading strategies.
    
    This class defines the interface for loading data from various sources.
    """
    
    @abstractmethod
    def load(self, source: str, **kwargs) -> pd.DataFrame:
        """
        Load data from the specified source.
        
        Args:
            source: Data source (file path, URL, etc.)
            **kwargs: Additional loading parameters
            
        Returns:
            Loaded DataFrame
            
        Raises:
            DataLoadError: If loading fails
        """
        pass
    
    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """
        Validate if the data source is accessible and valid.
        
        Args:
            source: Data source to validate
            
        Returns:
            True if source is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported data formats.
        
        Returns:
            List of supported file extensions or format names
        """
        pass


class FeatureSelector(ABC):
    """
    Abstract base class for feature selection strategies.
    
    This class defines the interface for selecting relevant features
    from the dataset.
    """
    
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'FeatureSelector':
        """
        Fit the feature selector to the data.
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            Self, to enable method chaining
        """
        pass
    
    @abstractmethod
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the data by selecting features.
        
        Args:
            X: Input feature matrix
            
        Returns:
            DataFrame with selected features
        """
        pass
    
    @abstractmethod
    def get_selected_features(self) -> List[str]:
        """
        Get list of selected feature names.
        
        Returns:
            List of selected feature names
        """
        pass
    
    @abstractmethod
    def get_feature_scores(self) -> Dict[str, float]:
        """
        Get feature importance/selection scores.
        
        Returns:
            Dictionary mapping feature names to scores
        """
        pass


class ModelPersistence(ABC):
    """
    Abstract base class for model persistence strategies.
    
    This class defines the interface for saving and loading trained models.
    """
    
    @abstractmethod
    def save_model(self, model: ModelStrategy, filepath: str, 
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Save a trained model to disk.
        
        Args:
            model: Trained model to save
            filepath: Path where to save the model
            metadata: Optional metadata to save with the model
            
        Raises:
            ModelPersistenceError: If saving fails
        """
        pass
    
    @abstractmethod
    def load_model(self, filepath: str) -> ModelStrategy:
        """
        Load a trained model from disk.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded model instance
            
        Raises:
            ModelPersistenceError: If loading fails
        """
        pass
    
    @abstractmethod
    def save_pipeline(self, pipeline: 'DataPipeline', filepath: str,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Save a data processing pipeline to disk.
        
        Args:
            pipeline: Pipeline to save
            filepath: Path where to save the pipeline
            metadata: Optional metadata to save with the pipeline
        """
        pass
    
    @abstractmethod
    def load_pipeline(self, filepath: str) -> 'DataPipeline':
        """
        Load a data processing pipeline from disk.
        
        Args:
            filepath: Path to the saved pipeline
            
        Returns:
            Loaded pipeline instance
        """
        pass


class MetricTracker(ABC):
    """
    Abstract base class for tracking and storing metrics during training.
    
    This class defines the interface for metric collection and storage.
    """
    
    @abstractmethod
    def log_metric(self, name: str, value: float, step: Optional[int] = None) -> None:
        """
        Log a single metric value.
        
        Args:
            name: Metric name
            value: Metric value
            step: Optional step/epoch number
        """
        pass
    
    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float], 
                   step: Optional[int] = None) -> None:
        """
        Log multiple metrics at once.
        
        Args:
            metrics: Dictionary of metric names to values
            step: Optional step/epoch number
        """
        pass
    
    @abstractmethod
    def get_metric_history(self, name: str) -> List[float]:
        """
        Get history of a specific metric.
        
        Args:
            name: Metric name
            
        Returns:
            List of metric values
        """
        pass
    
    @abstractmethod
    def get_all_metrics(self) -> Dict[str, List[float]]:
        """
        Get all tracked metrics.
        
        Returns:
            Dictionary mapping metric names to value lists
        """
        pass