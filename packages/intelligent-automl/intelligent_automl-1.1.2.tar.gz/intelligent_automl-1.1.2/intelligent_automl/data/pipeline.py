# ===================================
# FILE: automl_framework/data/pipeline.py (UPDATED)
# LOCATION: /automl_framework/automl_framework/data/pipeline.py
# ===================================

"""
Fixed Data processing pipeline management for the AutoML framework.

This module provides pipeline orchestration with smart parameter handling
for different processor types that may or may not need target variables.
"""

import pickle
import joblib
import json
import inspect
from typing import List, Dict, Any, Optional, Tuple, Union
import pandas as pd
from pathlib import Path

from ..core.base import DataProcessor
from ..core.exceptions import PipelineError, PreprocessingError, PersistenceError
from ..core.types import DataFrame, Series, PipelineStep, PipelineSteps


class DataPipeline:
    """
    Pipeline for chaining data processing steps with smart parameter handling.
    
    Automatically detects whether each processor needs target variable (y)
    and calls the appropriate method signature.
    """
    
    def __init__(self, steps: Optional[PipelineSteps] = None, memory: Optional[str] = None):
        """
        Initialize the data pipeline.
        
        Args:
            steps: List of (name, processor) tuples
            memory: Directory for caching intermediate results
        """
        self.steps: PipelineSteps = steps or []
        self.memory = memory
        self._fitted = False
        self._step_names: List[str] = []
        self._processors: List[DataProcessor] = []
        
        # Validate steps on initialization
        if self.steps:
            self._validate_steps()
            self._update_step_info()
    
    def _validate_steps(self) -> None:
        """Validate that all steps are properly formatted."""
        for i, step in enumerate(self.steps):
            if not isinstance(step, tuple) or len(step) != 2:
                raise PipelineError(f"Step {i} must be a tuple of (name, processor)")
            
            name, processor = step
            if not isinstance(name, str):
                raise PipelineError(f"Step {i} name must be a string")
            
            if not isinstance(processor, DataProcessor):
                raise PipelineError(f"Step {i} processor must implement DataProcessor interface")
    
    def _update_step_info(self) -> None:
        """Update internal step tracking."""
        self._step_names = [name for name, _ in self.steps]
        self._processors = [processor for _, processor in self.steps]
        
        # Check for duplicate step names
        if len(set(self._step_names)) != len(self._step_names):
            raise PipelineError("Duplicate step names are not allowed")
    
    def _processor_needs_target(self, processor: DataProcessor) -> bool:
        """
        Check if a processor's fit method can accept target variable (y).
        
        Args:
            processor: The processor to check
            
        Returns:
            True if processor can accept y parameter, False otherwise
        """
        try:
            # Get the fit method signature
            fit_method = getattr(processor, 'fit')
            signature = inspect.signature(fit_method)
            parameters = list(signature.parameters.keys())
            
            # Check if 'y' parameter exists or if there are more than 2 parameters
            # (self, X, y) or (self, data, target) etc.
            return len(parameters) > 2 or 'y' in parameters or 'target' in parameters
            
        except Exception:
            # If we can't determine, assume it doesn't need target
            return False
    
    def add_step(self, name: str, processor: DataProcessor, position: Optional[int] = None) -> 'DataPipeline':
        """
        Add a processing step to the pipeline.
        
        Args:
            name: Unique name for the step
            processor: Data processor instance
            position: Position to insert the step (append if None)
            
        Returns:
            Self for method chaining
        """
        if name in self._step_names:
            raise PipelineError(f"Step name '{name}' already exists")
        
        if not isinstance(processor, DataProcessor):
            raise PipelineError("Processor must implement DataProcessor interface")
        
        step = (name, processor)
        
        if position is None:
            self.steps.append(step)
        else:
            self.steps.insert(position, step)
        
        self._update_step_info()
        self._fitted = False  # Need to refit after adding step
        return self
    
    def remove_step(self, name: str) -> 'DataPipeline':
        """
        Remove a step from the pipeline.
        
        Args:
            name: Name of the step to remove
            
        Returns:
            Self for method chaining
        """
        if name not in self._step_names:
            raise PipelineError(f"Step '{name}' not found in pipeline")
        
        step_index = self._step_names.index(name)
        self.steps.pop(step_index)
        self._update_step_info()
        self._fitted = False
        return self
    
    def get_step(self, name: str) -> DataProcessor:
        """
        Get a specific step by name.
        
        Args:
            name: Name of the step
            
        Returns:
            The data processor for the step
        """
        if name not in self._step_names:
            raise PipelineError(f"Step '{name}' not found in pipeline")
        
        step_index = self._step_names.index(name)
        return self._processors[step_index]
    
    def replace_step(self, name: str, new_processor: DataProcessor) -> 'DataPipeline':
        """
        Replace an existing step with a new processor.
        
        Args:
            name: Name of the step to replace
            new_processor: New data processor
            
        Returns:
            Self for method chaining
        """
        if name not in self._step_names:
            raise PipelineError(f"Step '{name}' not found in pipeline")
        
        if not isinstance(new_processor, DataProcessor):
            raise PipelineError("New processor must implement DataProcessor interface")
        
        step_index = self._step_names.index(name)
        self.steps[step_index] = (name, new_processor)
        self._update_step_info()
        self._fitted = False
        return self
    
    def fit(self, X: DataFrame, y: Optional[Series] = None) -> 'DataPipeline':
        """
        Fit all pipeline steps sequentially with smart parameter handling.
        
        Args:
            X: Input features DataFrame
            y: Optional target variable for supervised processors
            
        Returns:
            Self for method chaining
        """
        if not self.steps:
            self._fitted = True
            return self
        
        current_X = X.copy()
        
        for step_name, processor in self.steps:
            try:
                # Check if processor has a fit method
                if not hasattr(processor, 'fit') or not callable(getattr(processor, 'fit')):
                    raise PipelineError(f"Step '{step_name}' processor does not have a fit method")
                
                # Smart parameter passing based on processor signature
                if self._processor_needs_target(processor) and y is not None:
                    # Processor can accept target variable
                    processor.fit(current_X, y)
                else:
                    # Processor only needs features
                    processor.fit(current_X)
                
                # Transform for next step (if processor has transform method)
                if hasattr(processor, 'transform') and callable(getattr(processor, 'transform')):
                    current_X = processor.transform(current_X)
                
            except Exception as e:
                raise PipelineError(f"Failed to fit step '{step_name}': {str(e)}") from e
        
        self._fitted = True
        return self
    
    def transform(self, X: DataFrame) -> DataFrame:
        """
        Transform data through all pipeline steps.
        
        Args:
            X: Input features DataFrame
            
        Returns:
            Transformed DataFrame
        """
        if not self._fitted:
            raise PipelineError("Pipeline must be fitted before transform")
        
        if not self.steps:
            return X.copy()
        
        current_X = X.copy()
        
        for step_name, processor in self.steps:
            try:
                if hasattr(processor, 'transform') and callable(getattr(processor, 'transform')):
                    current_X = processor.transform(current_X)
            except Exception as e:
                raise PipelineError(f"Failed to transform in step '{step_name}': {str(e)}") from e
        
        return current_X
    
    def fit_transform(self, X: DataFrame, y: Optional[Series] = None) -> DataFrame:
        """
        Fit pipeline and transform data in one step.
        
        Args:
            X: Input features DataFrame
            y: Optional target variable
            
        Returns:
            Transformed DataFrame
        """
        return self.fit(X, y).transform(X)
    
    def get_step_names(self) -> List[str]:
        """
        Get names of all pipeline steps.
        
        Returns:
            List of step names
        """
        return self._step_names.copy()
    
    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """
        Get parameters of all pipeline steps.
        
        Args:
            deep: Whether to return parameters of individual processors
            
        Returns:
            Dictionary of pipeline parameters
        """
        params = {
            'steps': self.steps.copy(),
            'memory': self.memory
        }
        
        if deep:
            for step_name, processor in self.steps:
                step_params = processor.get_params()
                for param_name, param_value in step_params.items():
                    params[f'{step_name}__{param_name}'] = param_value
        
        return params
    
    def set_params(self, **params) -> 'DataPipeline':
        """
        Set parameters of pipeline steps.
        
        Args:
            **params: Parameters to set (use step_name__param_name format)
            
        Returns:
            Self for method chaining
        """
        pipeline_params = {}
        step_params = {}
        
        # Separate pipeline params from step params
        for param_name, param_value in params.items():
            if '__' in param_name:
                step_name, step_param = param_name.split('__', 1)
                if step_name not in step_params:
                    step_params[step_name] = {}
                step_params[step_name][step_param] = param_value
            else:
                pipeline_params[param_name] = param_value
        
        # Set pipeline-level parameters
        for param_name, param_value in pipeline_params.items():
            if hasattr(self, param_name):
                setattr(self, param_name, param_value)
        
        # Set step-level parameters
        for step_name, params_dict in step_params.items():
            if step_name in self._step_names:
                processor = self.get_step(step_name)
                processor.set_params(**params_dict)
        
        self._fitted = False  # Need to refit after parameter change
        return self
    
    def copy(self) -> 'DataPipeline':
        """
        Create a copy of the pipeline.
        
        Returns:
            New DataPipeline instance with copied steps
        """
        import copy
        copied_steps = copy.deepcopy(self.steps)
        new_pipeline = DataPipeline(steps=copied_steps, memory=self.memory)
        new_pipeline._fitted = False  # Copy should not be fitted
        return new_pipeline
    
    def save(self, filepath: str, format: str = 'joblib') -> None:
        """
        Save the pipeline to disk.
        
        Args:
            filepath: Path to save the pipeline
            format: Serialization format ('joblib', 'pickle')
        """
        try:
            if format == 'joblib':
                joblib.dump(self, filepath)
            elif format == 'pickle':
                with open(filepath, 'wb') as f:
                    pickle.dump(self, f)
            else:
                raise PersistenceError(f"Unsupported format: {format}")
                
        except Exception as e:
            raise PersistenceError(f"Failed to save pipeline: {str(e)}") from e
    
    @classmethod
    def load(cls, filepath: str, format: str = 'auto') -> 'DataPipeline':
        """
        Load a pipeline from disk.
        
        Args:
            filepath: Path to the saved pipeline
            format: Serialization format ('auto', 'joblib', 'pickle')
            
        Returns:
            Loaded DataPipeline instance
        """
        try:
            if format == 'auto':
                # Guess format from file extension
                if filepath.endswith('.joblib'):
                    format = 'joblib'
                elif filepath.endswith('.pkl') or filepath.endswith('.pickle'):
                    format = 'pickle'
                else:
                    format = 'joblib'  # Default
            
            if format == 'joblib':
                return joblib.load(filepath)
            elif format == 'pickle':
                with open(filepath, 'rb') as f:
                    return pickle.load(f)
            else:
                raise PersistenceError(f"Unsupported format: {format}")
                
        except Exception as e:
            raise PersistenceError(f"Failed to load pipeline: {str(e)}") from e
    
    def save_config(self, filepath: str) -> None:
        """
        Save pipeline configuration to JSON.
        
        Args:
            filepath: Path to save the configuration
        """
        try:
            config = {
                'steps': [
                    {
                        'name': name,
                        'processor_type': type(processor).__name__,
                        'parameters': processor.get_params()
                    }
                    for name, processor in self.steps
                ],
                'memory': self.memory,
                'fitted': self._fitted
            }
            
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2, default=str)
                
        except Exception as e:
            raise PersistenceError(f"Failed to save pipeline config: {str(e)}") from e
    
    def validate(self, X: DataFrame, y: Optional[Series] = None) -> Dict[str, Any]:
        """
        Validate the pipeline configuration and data compatibility.
        
        Args:
            X: Input features DataFrame
            y: Optional target variable
            
        Returns:
            Validation report
        """
        report = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'step_info': []
        }
        
        try:
            # Check if pipeline has steps
            if not self.steps:
                report['warnings'].append("Pipeline has no steps")
            
            # Validate each step
            current_X = X.copy()
            for step_name, processor in self.steps:
                step_info = {
                    'name': step_name,
                    'processor_type': type(processor).__name__,
                    'input_shape': current_X.shape,
                    'status': 'unknown'
                }
                
                try:
                    # Check if processor can handle the current data
                    if hasattr(processor, 'fit'):
                        # Try fitting (in a copy to avoid side effects)
                        test_processor = type(processor)(**processor.get_params())
                        test_data = current_X.head(min(100, len(current_X)))
                        
                        # Smart parameter passing for validation
                        if self._processor_needs_target(test_processor) and y is not None:
                            test_target = y.head(min(100, len(y)))
                            test_processor.fit(test_data, test_target)
                        else:
                            test_processor.fit(test_data)
                        
                        if hasattr(test_processor, 'transform'):
                            current_X = test_processor.transform(test_data)
                            step_info['output_shape'] = current_X.shape
                        
                        step_info['status'] = 'valid'
                    else:
                        report['errors'].append(f"Step '{step_name}' processor has no fit method")
                        step_info['status'] = 'error'
                        report['is_valid'] = False
                        
                except Exception as e:
                    report['errors'].append(f"Step '{step_name}' validation failed: {str(e)}")
                    step_info['status'] = 'error'
                    step_info['error'] = str(e)
                    report['is_valid'] = False
                
                report['step_info'].append(step_info)
            
        except Exception as e:
            report['errors'].append(f"Pipeline validation failed: {str(e)}")
            report['is_valid'] = False
        
        return report
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Estimate memory usage of the pipeline.
        
        Returns:
            Memory usage information
        """
        import sys
        
        memory_info = {
            'pipeline_size_bytes': sys.getsizeof(self),
            'steps': []
        }
        
        for step_name, processor in self.steps:
            step_memory = {
                'name': step_name,
                'processor_type': type(processor).__name__,
                'size_bytes': sys.getsizeof(processor)
            }
            memory_info['steps'].append(step_memory)
        
        memory_info['total_size_bytes'] = sum(step['size_bytes'] for step in memory_info['steps'])
        memory_info['total_size_mb'] = memory_info['total_size_bytes'] / (1024 * 1024)
        
        return memory_info
    
    def profile_performance(self, X: DataFrame, y: Optional[Series] = None, 
                          n_iterations: int = 3) -> Dict[str, Any]:
        """
        Profile the performance of each pipeline step.
        
        Args:
            X: Input features DataFrame
            y: Optional target variable
            n_iterations: Number of iterations for timing
            
        Returns:
            Performance profiling results
        """
        import time
        
        if not self._fitted:
            raise PipelineError("Pipeline must be fitted before profiling")
        
        profile_results = {
            'total_time_seconds': 0,
            'steps': []
        }
        
        current_X = X.copy()
        
        for step_name, processor in self.steps:
            if not hasattr(processor, 'transform'):
                continue
                
            step_times = []
            
            for _ in range(n_iterations):
                start_time = time.time()
                transformed_X = processor.transform(current_X)
                end_time = time.time()
                step_times.append(end_time - start_time)
            
            avg_time = sum(step_times) / len(step_times)
            step_info = {
                'name': step_name,
                'processor_type': type(processor).__name__,
                'avg_time_seconds': avg_time,
                'input_shape': current_X.shape,
                'output_shape': transformed_X.shape,
                'throughput_rows_per_second': len(current_X) / avg_time if avg_time > 0 else float('inf')
            }
            
            profile_results['steps'].append(step_info)
            profile_results['total_time_seconds'] += avg_time
            current_X = transformed_X
        
        return profile_results
    
    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> List[str]:
        """
        Get feature names after transformation.
        
        Args:
            input_features: Input feature names
            
        Returns:
            Output feature names after all transformations
        """
        if not self._fitted:
            raise PipelineError("Pipeline must be fitted to get feature names")
        
        current_features = input_features
        
        for step_name, processor in self.steps:
            if hasattr(processor, 'get_feature_names_out'):
                current_features = processor.get_feature_names_out(current_features)
            elif hasattr(processor, 'get_feature_names'):
                current_features = processor.get_feature_names(current_features)
            # If processor doesn't support feature names, keep current
        
        return current_features
    
    def __len__(self) -> int:
        """Return number of steps in the pipeline."""
        return len(self.steps)
    
    def __getitem__(self, index: Union[int, str]) -> DataProcessor:
        """Get step by index or name."""
        if isinstance(index, int):
            return self._processors[index]
        elif isinstance(index, str):
            return self.get_step(index)
        else:
            raise TypeError("Index must be int or str")
    
    def __repr__(self) -> str:
        """Return string representation of the pipeline."""
        if not self.steps:
            return "DataPipeline(steps=[])"
        
        step_reprs = []
        for name, processor in self.steps:
            step_reprs.append(f"('{name}', {type(processor).__name__})")
        
        return f"DataPipeline(steps=[{', '.join(step_reprs)}])"
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        if not self.steps:
            return "Empty DataPipeline"
        
        lines = ["DataPipeline:"]
        for i, (name, processor) in enumerate(self.steps):
            lines.append(f"  {i+1}. {name}: {type(processor).__name__}")
        
        return "\n".join(lines)