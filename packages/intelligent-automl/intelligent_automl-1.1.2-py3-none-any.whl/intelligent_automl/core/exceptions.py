# ===================================
# FILE: automl_framework/core/exceptions.py
# LOCATION: /automl_framework/automl_framework/core/exceptions.py
# ===================================

"""
Custom exception classes for the AutoML framework.

This module defines a hierarchy of exceptions that provide clear error messages
and enable specific error handling for different types of failures.
"""

from typing import Optional, Any, Dict
import pandas as pd



class AutoMLError(Exception):
    """
    Base exception class for all AutoML framework errors.
    
    This is the root exception that all other framework exceptions inherit from,
    allowing for catch-all error handling when needed.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(AutoMLError):
    """
    Raised when there are issues with configuration settings.
    
    This includes invalid parameter values, missing required settings,
    or conflicting configuration options.
    """
    pass


class DataLoadError(AutoMLError):
    """
    Raised when data loading operations fail.
    
    This includes file not found, unsupported formats, corrupted data,
    or network issues when loading remote data.
    """
    pass


class DataValidationError(AutoMLError):
    """
    Raised when data validation checks fail.
    
    This includes schema mismatches, missing required columns,
    data type inconsistencies, or data quality issues.
    """
    pass


class PreprocessingError(AutoMLError):
    """
    Raised when data preprocessing operations fail.
    
    This includes transformation errors, scaling failures,
    encoding issues, or feature engineering problems.
    """
    pass


class ModelTrainingError(AutoMLError):
    """
    Raised when model training operations fail.
    
    This includes convergence issues, invalid hyperparameters,
    insufficient data, or algorithm-specific errors.
    """
    pass


class ModelPredictionError(AutoMLError):
    """
    Raised when model prediction operations fail.
    
    This includes incompatible input data, model not fitted,
    or prediction computation errors.
    """
    pass


class EvaluationError(AutoMLError):
    """
    Raised when model evaluation operations fail.
    
    This includes metric computation errors, cross-validation failures,
    or incompatible evaluation settings.
    """
    pass


class OptimizationError(AutoMLError):
    """
    Raised when hyperparameter optimization fails.
    
    This includes search space issues, optimization algorithm failures,
    or timeout/resource limit errors.
    """
    pass


class PipelineError(AutoMLError):
    """
    Raised when pipeline execution fails.
    
    This includes step execution errors, pipeline validation failures,
    or workflow orchestration issues.
    """
    pass


class PersistenceError(AutoMLError):
    """
    Raised when model or pipeline persistence operations fail.
    
    This includes save/load failures, serialization errors,
    or file system issues.
    """
    pass


class ResourceError(AutoMLError):
    """
    Raised when resource constraints are exceeded.
    
    This includes memory limits, timeout errors, disk space issues,
    or computational resource constraints.
    """
    pass


class FeatureError(AutoMLError):
    """
    Raised when feature processing operations fail.
    
    This includes feature selection errors, feature engineering failures,
    or feature importance computation issues.
    """
    pass


class CommandExecutionError(AutoMLError):
    """
    Raised when command pattern operations fail.
    
    This includes command execution failures, undo operation errors,
    or command queue management issues.
    """
    pass


class ObserverError(AutoMLError):
    """
    Raised when observer pattern operations fail.
    
    This includes notification delivery failures, observer registration errors,
    or monitoring system issues.
    """
    pass


class AdapterError(AutoMLError):
    """
    Raised when adapter pattern operations fail.
    
    This includes external library integration issues, API compatibility errors,
    or adapter configuration problems.
    """
    pass


class ValidationError(AutoMLError):
    """
    Raised when general validation operations fail.
    
    This is a general validation error for cases that don't fit
    into more specific validation error categories.
    """
    pass


class TimeoutError(AutoMLError):
    """
    Raised when operations exceed their time limits.
    
    This includes training timeouts, optimization timeouts,
    or any other time-constrained operation failures.
    """
    pass


class InsufficientDataError(AutoMLError):
    """
    Raised when there is insufficient data for an operation.
    
    This includes cases where datasets are too small for cross-validation,
    insufficient samples for training, or missing required data.
    """
    pass


class UnsupportedOperationError(AutoMLError):
    """
    Raised when an unsupported operation is attempted.
    
    This includes operations not implemented for specific model types,
    unsupported data types, or feature combinations not supported.
    """
    pass


class DependencyError(AutoMLError):
    """
    Raised when required dependencies are missing or incompatible.
    
    This includes missing optional libraries, version incompatibilities,
    or system dependency issues.
    """
    pass


# Utility functions for exception handling

def handle_sklearn_error(func):
    """
    Decorator to convert scikit-learn errors to AutoML framework errors.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that converts exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            if "not fitted" in str(e).lower():
                raise ModelTrainingError(f"Model not fitted: {str(e)}")
            else:
                raise PreprocessingError(f"Data processing error: {str(e)}")
        except Exception as e:
            raise AutoMLError(f"Unexpected error in {func.__name__}: {str(e)}")
    return wrapper


def handle_data_error(func):
    """
    Decorator to convert data-related errors to AutoML framework errors.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that converts exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            raise DataLoadError(f"File not found: {str(e)}")
        except PermissionError as e:
            raise DataLoadError(f"Permission denied: {str(e)}")
        except pd.errors.EmptyDataError as e:
            raise DataValidationError(f"Empty data file: {str(e)}")
        except pd.errors.ParserError as e:
            raise DataLoadError(f"Data parsing error: {str(e)}")
        except Exception as e:
            raise DataLoadError(f"Unexpected data error: {str(e)}")
    return wrapper


def create_error_context(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Create a standardized error context dictionary.
    
    Args:
        operation: Name of the operation that failed
        **kwargs: Additional context information
        
    Returns:
        Dictionary with error context
    """
    context = {
        'operation': operation,
        'timestamp': str(pd.Timestamp.now()),
    }
    context.update(kwargs)
    return context


def log_and_raise(logger, exception_class, message: str, **context):
    """
    Log an error and raise the appropriate exception.
    
    Args:
        logger: Logger instance
        exception_class: Exception class to raise
        message: Error message
        **context: Additional context for the error
    """
    error_context = create_error_context(**context)
    logger.error(f"{message} | Context: {error_context}")
    raise exception_class(message, details=error_context)