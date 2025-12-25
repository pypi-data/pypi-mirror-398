"""
Intelligence module for the Intelligent AutoML framework.

This module provides the AI-driven pipeline selection and optimization
capabilities that make the framework truly intelligent.
"""

from .pipeline_selector import (
    IntelligentPipelineSelector,
    DataCharacteristics,
    ProcessingRecommendation,
    create_intelligent_pipeline
)

__all__ = [
    "IntelligentPipelineSelector",
    "DataCharacteristics", 
    "ProcessingRecommendation",
    "create_intelligent_pipeline"
]