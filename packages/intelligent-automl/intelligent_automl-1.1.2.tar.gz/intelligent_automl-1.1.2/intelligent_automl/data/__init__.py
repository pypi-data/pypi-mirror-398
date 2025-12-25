"""
Data processing module for the Intelligent AutoML framework.

This module provides data loading, preprocessing, and pipeline management
capabilities for automated machine learning workflows.
"""

from .preprocessors import (
    MissingValueHandler,
    FeatureScaler,
    CategoricalEncoder,
    OutlierHandler,
    FeatureEngineering,
    DateTimeProcessor,
    FeatureSelector
)

from .pipeline import DataPipeline

from .loaders import (
    CSVLoader,
    ExcelLoader,
    JSONLoader,
    ParquetLoader,
    AutoLoader,
    DatabaseLoader,
    URLLoader,
    create_loader,
    load_data
)

__all__ = [
    # Preprocessors
    "MissingValueHandler",
    "FeatureScaler", 
    "CategoricalEncoder",
    "OutlierHandler",
    "FeatureEngineering",
    "DateTimeProcessor",
    "FeatureSelector",
    
    # Pipeline
    "DataPipeline",
    
    # Loaders
    "CSVLoader",
    "ExcelLoader",
    "JSONLoader", 
    "ParquetLoader",
    "AutoLoader",
    "DatabaseLoader",
    "URLLoader",
    "create_loader",
    "load_data"
]