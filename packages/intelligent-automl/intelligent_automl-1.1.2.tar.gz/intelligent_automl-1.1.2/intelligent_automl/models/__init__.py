"""
Model training and evaluation components.

This module provides intelligent model training, evaluation, and selection
capabilities with comprehensive multi-metric support.
"""

from .auto_trainer import EnhancedAutoModelTrainer, AutoModelTrainer, train_auto_model

__all__ = [
    'EnhancedAutoModelTrainer',
    'AutoModelTrainer',  # Legacy compatibility
    'train_auto_model'
]