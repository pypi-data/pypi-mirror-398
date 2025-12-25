"""
Utilities module for the Intelligent AutoML framework.

This module provides logging, validation, and other utility functions.
"""

try:
    from .logging import configure_logging, get_logger, MetricsTracker
    from .validation import validate_dataset, DataProfiler
    __all__ = [
        "configure_logging", 
        "get_logger", 
        "MetricsTracker", 
        "validate_dataset", 
        "DataProfiler"
    ]
except ImportError:
    # Some utilities might not be fully implemented yet
    __all__ = []

# Module metadata
__version__ = "1.0.0"
__author__ = "Intelligent AutoML Team"