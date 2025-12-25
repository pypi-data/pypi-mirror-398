#!/usr/bin/env python
"""
Logging and monitoring utilities for the AutoML framework.

This module provides comprehensive logging, monitoring, and metrics tracking
capabilities for all framework components.
"""

import logging
import json
import time
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import threading
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from ..core.exceptions import AutoMLError


@dataclass
class LogEntry:
    """Structured log entry for AutoML operations."""
    timestamp: str
    level: str
    component: str
    operation: str
    message: str
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    data_shape: Optional[tuple] = None
    metadata: Optional[Dict[str, Any]] = None


class AutoMLLogger:
    """
    Comprehensive logging system for AutoML operations.
    
    Provides structured logging with performance metrics, component tracking,
    and integration with various logging backends.
    """
    
    def __init__(self, 
                 name: str = "intelligent_automl",
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 log_to_console: bool = True,
                 structured_logging: bool = True,
                 include_performance: bool = True):
        """
        Initialize the AutoML logger.
        
        Args:
            name: Logger name
            level: Logging level
            log_file: Optional file path for logging
            log_to_console: Whether to log to console
            structured_logging: Whether to use structured JSON logging
            include_performance: Whether to include performance metrics
        """
        self.name = name
        self.structured_logging = structured_logging
        self.include_performance = include_performance
        self.log_entries: List[LogEntry] = []
        self._lock = threading.Lock()
        
        # Setup Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(console_handler)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(file_handler)
    
    def _get_formatter(self) -> logging.Formatter:
        """Get appropriate formatter based on configuration."""
        if self.structured_logging:
            return StructuredFormatter()
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _create_log_entry(self, level: str, component: str, operation: str, 
                         message: str, **kwargs) -> LogEntry:
        """Create a structured log entry."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            component=component,
            operation=operation,
            message=message,
            execution_time=kwargs.get('execution_time'),
            memory_usage=self._get_memory_usage() if self.include_performance else None,
            data_shape=kwargs.get('data_shape'),
            metadata=kwargs.get('metadata')
        )
        
        with self._lock:
            self.log_entries.append(entry)
        
        return entry
    
    def log_operation(self, component: str, operation: str, message: str, 
                     level: str = "INFO", **kwargs):
        """Log an operation with structured information."""
        entry = self._create_log_entry(level, component, operation, message, **kwargs)
        
        log_message = message
        if self.structured_logging:
            try:
                log_message = json.dumps(asdict(entry), default=self._json_serializer)
            except (TypeError, ValueError):
                # Fallback to simple message if JSON serialization fails
                log_message = message
        
        getattr(self.logger, level.lower())(log_message)
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for numpy and pandas objects."""
        if hasattr(obj, 'dtype'):
            return str(obj)
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if hasattr(obj, '__dict__'):
            return str(obj)
        return str(obj)
    
    def log_data_operation(self, component: str, operation: str, message: str,
                          data: Optional[pd.DataFrame] = None, **kwargs):
        """Log a data operation with dataset information."""
        metadata = kwargs.get('metadata', {})
        
        if data is not None:
            # Convert dtypes to safe format for JSON serialization
            dtypes_dict = {}
            for col, dtype in data.dtypes.items():
                dtypes_dict[str(col)] = str(dtype)
            
            metadata.update({
                'rows': len(data),
                'columns': len(data.columns),
                'memory_mb': data.memory_usage(deep=True).sum() / 1024**2,
                'missing_values': data.isnull().sum().sum(),
                'dtypes': dtypes_dict
            })
            kwargs['data_shape'] = data.shape
        
        kwargs['metadata'] = metadata
        self.log_operation(component, operation, message, **kwargs)
    
    def log_model_operation(self, component: str, operation: str, message: str,
                           model_info: Optional[Dict[str, Any]] = None, **kwargs):
        """Log a model operation with model information."""
        metadata = kwargs.get('metadata', {})
        
        if model_info:
            metadata.update(model_info)
        
        kwargs['metadata'] = metadata
        self.log_operation(component, operation, message, **kwargs)
    
    def log_performance(self, component: str, operation: str, execution_time: float,
                       message: Optional[str] = None, **kwargs):
        """Log performance metrics for an operation."""
        if not message:
            message = f"{operation} completed in {execution_time:.3f}s"
        
        kwargs['execution_time'] = execution_time
        self.log_operation(component, operation, message, level="INFO", **kwargs)
    
    def log_error(self, component: str, operation: str, error: Exception, **kwargs):
        """Log an error with full context."""
        message = f"Error in {operation}: {str(error)}"
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
        kwargs['metadata'] = metadata
        
        self.log_operation(component, operation, message, level="ERROR", **kwargs)
    
    def get_log_entries(self, component: Optional[str] = None, 
                       operation: Optional[str] = None,
                       level: Optional[str] = None) -> List[LogEntry]:
        """Get filtered log entries."""
        with self._lock:
            entries = self.log_entries.copy()
        
        if component:
            entries = [e for e in entries if e.component == component]
        if operation:
            entries = [e for e in entries if e.operation == operation]
        if level:
            entries = [e for e in entries if e.level == level]
        
        return entries
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from logged operations."""
        with self._lock:
            entries = [e for e in self.log_entries if e.execution_time is not None]
        
        if not entries:
            return {}
        
        performance_by_component = {}
        for entry in entries:
            component = entry.component
            if component not in performance_by_component:
                performance_by_component[component] = []
            performance_by_component[component].append(entry.execution_time)
        
        summary = {}
        for component, times in performance_by_component.items():
            summary[component] = {
                'count': len(times),
                'total_time': sum(times),
                'avg_time': np.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_time': np.std(times)
            }
        
        return summary
    
    def export_logs(self, filepath: str, format: str = 'json'):
        """Export logs to file."""
        with self._lock:
            entries = [asdict(e) for e in self.log_entries]
        
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(entries, f, indent=2, default=str)
        elif format == 'csv':
            df = pd.DataFrame(entries)
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record):
        # Try to parse as JSON first
        try:
            log_data = json.loads(record.getMessage())
            return json.dumps(log_data, separators=(',', ':'))
        except (json.JSONDecodeError, TypeError):
            # Fallback to regular formatting
            return super().format(record)


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection.
    
    Tracks execution times, memory usage, and other performance metrics
    across all framework components.
    """
    
    def __init__(self, logger: Optional[AutoMLLogger] = None):
        """Initialize performance monitor."""
        self.logger = logger or AutoMLLogger()
        self.active_operations: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def monitor_operation(self, component: str, operation: str, 
                         data: Optional[pd.DataFrame] = None,
                         metadata: Optional[Dict[str, Any]] = None):
        """Context manager for monitoring operation performance."""
        operation_id = f"{component}.{operation}"
        start_time = time.time()
        
        with self._lock:
            self.active_operations[operation_id] = start_time
        
        try:
            if data is not None:
                self.logger.log_data_operation(
                    component, f"{operation}_start", 
                    f"Starting {operation}", data=data, metadata=metadata
                )
            else:
                self.logger.log_operation(
                    component, f"{operation}_start", 
                    f"Starting {operation}", metadata=metadata
                )
            
            yield
            
            execution_time = time.time() - start_time
            self.logger.log_performance(
                component, operation, execution_time,
                f"{operation} completed successfully", metadata=metadata
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.log_error(
                component, operation, e, 
                execution_time=execution_time, metadata=metadata
            )
            raise
        
        finally:
            with self._lock:
                self.active_operations.pop(operation_id, None)
    
    def get_active_operations(self) -> Dict[str, float]:
        """Get currently active operations and their start times."""
        with self._lock:
            current_time = time.time()
            return {
                op_id: current_time - start_time 
                for op_id, start_time in self.active_operations.items()
            }


class MetricsTracker:
    """
    Comprehensive metrics tracking for AutoML operations.
    
    Tracks model performance, data quality metrics, and system performance
    across training runs and experiments.
    """
    
    def __init__(self, logger: Optional[AutoMLLogger] = None):
        """Initialize metrics tracker."""
        self.logger = logger or AutoMLLogger()
        self.metrics_history: List[Dict[str, Any]] = []
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def track_data_quality(self, data: pd.DataFrame, stage: str, 
                          component: str = "data_processing") -> Dict[str, Any]:
        """Track data quality metrics."""
        metrics = {
            'stage': stage,
            'timestamp': datetime.now().isoformat(),
            'rows': len(data),
            'columns': len(data.columns),
            'missing_values': data.isnull().sum().sum(),
            'missing_percentage': (data.isnull().sum().sum() / data.size) * 100,
            'duplicate_rows': data.duplicated().sum(),
            'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024**2,
            'dtypes': data.dtypes.value_counts().to_dict()
        }
        
        # Add numeric-specific metrics
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            metrics.update({
                'numeric_columns': len(numeric_cols),
                'outliers_iqr': self._count_outliers_iqr(data[numeric_cols]),
                'skewness_high': self._count_highly_skewed(data[numeric_cols])
            })
        
        # Add categorical-specific metrics
        cat_cols = data.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) > 0:
            metrics.update({
                'categorical_columns': len(cat_cols),
                'high_cardinality_features': self._count_high_cardinality(data[cat_cols])
            })
        
        with self._lock:
            self.metrics_history.append(metrics)
        
        self.logger.log_data_operation(
            component, f"data_quality_{stage}", 
            f"Data quality metrics for {stage}", 
            data=data, metadata=metrics
        )
        
        return metrics
    
    def track_model_performance(self, model_name: str, metrics: Dict[str, float],
                               stage: str = "validation", 
                               component: str = "model_training") -> Dict[str, Any]:
        """Track model performance metrics."""
        performance_record = {
            'model_name': model_name,
            'stage': stage,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'primary_metric': max(metrics.items(), key=lambda x: x[1])
        }
        
        with self._lock:
            self.metrics_history.append(performance_record)
        
        self.logger.log_model_operation(
            component, f"model_performance_{stage}",
            f"Model performance for {model_name} on {stage}",
            model_info=performance_record
        )
        
        return performance_record
    
    def track_experiment(self, experiment_id: str, config: Dict[str, Any],
                        results: Dict[str, Any]) -> None:
        """Track complete experiment results."""
        experiment_record = {
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            'config': config,
            'results': results,
            'status': 'completed'
        }
        
        with self._lock:
            self.experiments[experiment_id] = experiment_record
        
        self.logger.log_operation(
            "experiment_tracker", "experiment_completed",
            f"Experiment {experiment_id} completed",
            metadata=experiment_record
        )
    
    def get_metrics_summary(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        with self._lock:
            metrics = self.metrics_history.copy()
        
        if component:
            # Filter by component (would need to track component in metrics)
            pass
        
        if not metrics:
            return {}
        
        # Aggregate metrics by type
        data_quality_metrics = [m for m in metrics if 'rows' in m]
        model_performance_metrics = [m for m in metrics if 'model_name' in m]
        
        summary = {
            'total_records': len(metrics),
            'data_quality_checks': len(data_quality_metrics),
            'model_evaluations': len(model_performance_metrics),
            'time_range': {
                'start': min(m['timestamp'] for m in metrics),
                'end': max(m['timestamp'] for m in metrics)
            }
        }
        
        # Data quality summary
        if data_quality_metrics:
            summary['data_quality_summary'] = {
                'avg_missing_percentage': np.mean([m['missing_percentage'] for m in data_quality_metrics]),
                'max_missing_percentage': max(m['missing_percentage'] for m in data_quality_metrics),
                'total_duplicate_rows': sum(m.get('duplicate_rows', 0) for m in data_quality_metrics)
            }
        
        # Model performance summary
        if model_performance_metrics:
            all_metrics = {}
            for record in model_performance_metrics:
                for metric_name, value in record['metrics'].items():
                    if metric_name not in all_metrics:
                        all_metrics[metric_name] = []
                    all_metrics[metric_name].append(value)
            
            summary['model_performance_summary'] = {
                metric_name: {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': min(values),
                    'max': max(values)
                }
                for metric_name, values in all_metrics.items()
            }
        
        return summary
    
    def _count_outliers_iqr(self, df: pd.DataFrame) -> int:
        """Count outliers using IQR method."""
        outlier_count = 0
        for col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum()
            outlier_count += outliers
        return outlier_count
    
    def _count_highly_skewed(self, df: pd.DataFrame, threshold: float = 1.0) -> int:
        """Count highly skewed features."""
        skewed_count = 0
        for col in df.columns:
            try:
                skewness = df[col].skew()
                if abs(skewness) > threshold:
                    skewed_count += 1
            except:
                pass
        return skewed_count
    
    def _count_high_cardinality(self, df: pd.DataFrame, threshold: int = 50) -> int:
        """Count high cardinality categorical features."""
        high_card_count = 0
        for col in df.columns:
            if df[col].nunique() > threshold:
                high_card_count += 1
        return high_card_count
    
    def export_metrics(self, filepath: str, format: str = 'json'):
        """Export metrics to file."""
        with self._lock:
            data = {
                'metrics_history': self.metrics_history,
                'experiments': self.experiments,
                'summary': self.get_metrics_summary()
            }
        
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            # Export metrics history as CSV
            df = pd.DataFrame(self.metrics_history)
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global logger instance
_global_logger = None

def get_logger(name: str = "intelligent_automl", **kwargs) -> AutoMLLogger:
    """Get or create a global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AutoMLLogger(name, **kwargs)
    return _global_logger

def configure_logging(level: str = "INFO", log_file: Optional[str] = None, 
                     log_to_console: bool = True, **kwargs):
    """Configure global logging settings."""
    global _global_logger
    _global_logger = AutoMLLogger(
        level=level, 
        log_file=log_file, 
        log_to_console=log_to_console, 
        **kwargs
    )

# Convenience functions
def log_info(component: str, operation: str, message: str, **kwargs):
    """Log info message."""
    get_logger().log_operation(component, operation, message, level="INFO", **kwargs)

def log_error(component: str, operation: str, error: Exception, **kwargs):
    """Log error."""
    get_logger().log_error(component, operation, error, **kwargs)

def log_performance(component: str, operation: str, execution_time: float, **kwargs):
    """Log performance metrics."""
    get_logger().log_performance(component, operation, execution_time, **kwargs)


class FrameworkLogger:
    """
    Simple wrapper around AutoMLLogger for framework compatibility.
    This provides the interface expected by the complete_framework.py
    """
    
    def __init__(self, log_level: str = 'INFO', log_file: Optional[str] = None):
        """Initialize framework logger."""
        self.logger = AutoMLLogger(
            name="intelligent_automl_framework",
            level=log_level,
            log_file=log_file,
            log_to_console=True,
            structured_logging=False  # Keep it simple for now
        )
    
    def log_info(self, component: str, operation: str, message: str, **kwargs):
        """Log info message."""
        self.logger.log_operation(component, operation, message, level="INFO", **kwargs)
    
    def log_error(self, component: str, operation: str, error: Exception, **kwargs):
        """Log error message."""
        self.logger.log_error(component, operation, error, **kwargs)
    
    def log_warning(self, component: str, operation: str, message: str, **kwargs):
        """Log warning message."""
        self.logger.log_operation(component, operation, message, level="WARNING", **kwargs)
    
    def log_debug(self, component: str, operation: str, message: str, **kwargs):
        """Log debug message."""
        self.logger.log_operation(component, operation, message, level="DEBUG", **kwargs)
    
    def log_performance(self, component: str, operation: str, execution_time: float, **kwargs):
        """Log performance metrics."""
        self.logger.log_performance(component, operation, execution_time, **kwargs)


# Also add this for backward compatibility
def get_framework_logger(log_level: str = 'INFO') -> FrameworkLogger:
    """Get a framework logger instance."""
    return FrameworkLogger(log_level=log_level)


# Example usage
if __name__ == "__main__":
    # Configure logging
    configure_logging(level="INFO", log_to_console=True)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'feature1': np.random.normal(0, 1, 1000),
        'feature2': np.random.normal(0, 1, 1000),
        'target': np.random.randint(0, 2, 1000)
    })
    
    # Add some missing values
    sample_data.loc[::10, 'feature1'] = np.nan
    
    # Test logging
    logger = get_logger()
    monitor = PerformanceMonitor(logger)
    metrics_tracker = MetricsTracker(logger)
    
    # Monitor an operation
    with monitor.monitor_operation("data_processing", "load_data", data=sample_data):
        time.sleep(0.1)  # Simulate processing
    
    # Track data quality
    metrics_tracker.track_data_quality(sample_data, "raw_data")
    
    # Track model performance
    metrics_tracker.track_model_performance(
        "random_forest", 
        {"accuracy": 0.85, "precision": 0.82, "recall": 0.88}
    )
    
    # Get summary
    summary = metrics_tracker.get_metrics_summary()
    print("Metrics Summary:")
    print(json.dumps(summary, indent=2, default=str))
    
    # Export logs
    logger.export_logs("test_logs.json")
    metrics_tracker.export_metrics("test_metrics.json")
    
    print("✅ Logging system test completed!")

