#!/usr/bin/env python
"""
Data validation utilities for the AutoML framework.

This module provides comprehensive data validation, quality checks,
and schema validation for ensuring data integrity throughout the pipeline.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import warnings
import re

from ..core.exceptions import DataValidationError, ValidationError
from ..core.types import DataFrame, Series, ValidationRule, ValidationRules


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    rule_name: str
    message: str
    severity: str  # 'error', 'warning', 'info'
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    is_valid: bool
    error_count: int
    warning_count: int
    info_count: int
    results: List[ValidationResult]
    summary: Dict[str, Any]
    
    def get_errors(self) -> List[ValidationResult]:
        """Get all error results."""
        return [r for r in self.results if r.severity == 'error']
    
    def get_warnings(self) -> List[ValidationResult]:
        """Get all warning results."""
        return [r for r in self.results if r.severity == 'warning']
    
    def get_info(self) -> List[ValidationResult]:
        """Get all info results."""
        return [r for r in self.results if r.severity == 'info']


class BaseValidator(ABC):
    """Abstract base class for data validators."""
    
    def __init__(self, name: str, severity: str = 'error'):
        """
        Initialize validator.
        
        Args:
            name: Validator name
            severity: Severity level ('error', 'warning', 'info')
        """
        self.name = name
        self.severity = severity
    
    @abstractmethod
    def validate(self, data: DataFrame) -> ValidationResult:
        """Validate data and return result."""
        pass


class SchemaValidator(BaseValidator):
    """Validates data schema (columns, types, constraints)."""
    
    def __init__(self, expected_schema: Dict[str, Any], **kwargs):
        """
        Initialize schema validator.
        
        Args:
            expected_schema: Expected schema with column names and types
        """
        super().__init__("schema_validation", **kwargs)
        self.expected_schema = expected_schema
    
    def validate(self, data: DataFrame) -> ValidationResult:
        """Validate data schema."""
        issues = []
        
        # Check required columns
        expected_columns = set(self.expected_schema.keys())
        actual_columns = set(data.columns)
        
        missing_columns = expected_columns - actual_columns
        if missing_columns:
            issues.append(f"Missing columns: {missing_columns}")
        
        extra_columns = actual_columns - expected_columns
        if extra_columns:
            issues.append(f"Unexpected columns: {extra_columns}")
        
        # Check data types for existing columns
        for col in expected_columns.intersection(actual_columns):
            expected_type = self.expected_schema[col]
            actual_type = str(data[col].dtype)
            
            if not self._is_compatible_type(actual_type, expected_type):
                issues.append(f"Column '{col}': expected {expected_type}, got {actual_type}")
        
        is_valid = len(issues) == 0
        message = "Schema validation passed" if is_valid else f"Schema validation failed: {'; '.join(issues)}"
        
        return ValidationResult(
            is_valid=is_valid,
            rule_name=self.name,
            message=message,
            severity=self.severity,
            details={
                'expected_columns': list(expected_columns),
                'actual_columns': list(actual_columns),
                'missing_columns': list(missing_columns),
                'extra_columns': list(extra_columns),
                'issues': issues
            }
        )
    
    def _is_compatible_type(self, actual_type: str, expected_type: str) -> bool:
        """Check if actual type is compatible with expected type."""
        # Simple type compatibility check
        type_mappings = {
            'int': ['int64', 'int32', 'int16', 'int8'],
            'float': ['float64', 'float32', 'float16'],
            'string': ['object', 'string'],
            'object': ['object'],
            'datetime': ['datetime64[ns]', 'datetime64'],
            'category': ['category']
        }
        
        if expected_type in type_mappings:
            return actual_type in type_mappings[expected_type]
        
        return actual_type == expected_type


class DataQualityValidator(BaseValidator):
    """Validates data quality metrics."""
    
    def __init__(self, 
                 max_missing_percentage: float = 50.0,
                 max_duplicate_percentage: float = 10.0,
                 min_unique_values: int = 2,
                 **kwargs):
        """
        Initialize data quality validator.
        
        Args:
            max_missing_percentage: Maximum allowed missing values percentage
            max_duplicate_percentage: Maximum allowed duplicate rows percentage
            min_unique_values: Minimum unique values per column
        """
        super().__init__("data_quality", **kwargs)
        self.max_missing_percentage = max_missing_percentage
        self.max_duplicate_percentage = max_duplicate_percentage
        self.min_unique_values = min_unique_values
    
    def validate(self, data: DataFrame) -> ValidationResult:
        """Validate data quality."""
        issues = []
        warnings = []
        
        # Check missing values
        missing_percentage = (data.isnull().sum().sum() / data.size) * 100
        if missing_percentage > self.max_missing_percentage:
            issues.append(f"Missing values: {missing_percentage:.1f}% > {self.max_missing_percentage}%")
        elif missing_percentage > self.max_missing_percentage * 0.5:
            warnings.append(f"High missing values: {missing_percentage:.1f}%")
        
        # Check duplicate rows
        duplicate_count = data.duplicated().sum()
        duplicate_percentage = (duplicate_count / len(data)) * 100
        if duplicate_percentage > self.max_duplicate_percentage:
            issues.append(f"Duplicate rows: {duplicate_percentage:.1f}% > {self.max_duplicate_percentage}%")
        elif duplicate_percentage > 0:
            warnings.append(f"Duplicate rows found: {duplicate_count}")
        
        # Check column uniqueness
        for col in data.columns:
            unique_count = data[col].nunique()
            if unique_count < self.min_unique_values:
                issues.append(f"Column '{col}' has only {unique_count} unique values")
        
        # Check for completely empty columns
        empty_columns = data.columns[data.isnull().all()].tolist()
        if empty_columns:
            issues.append(f"Completely empty columns: {empty_columns}")
        
        is_valid = len(issues) == 0
        message = "Data quality validation passed" if is_valid else f"Data quality issues: {'; '.join(issues)}"
        
        return ValidationResult(
            is_valid=is_valid,
            rule_name=self.name,
            message=message,
            severity=self.severity,
            details={
                'missing_percentage': missing_percentage,
                'duplicate_count': duplicate_count,
                'duplicate_percentage': duplicate_percentage,
                'empty_columns': empty_columns,
                'issues': issues,
                'warnings': warnings
            }
        )


class StatisticalValidator(BaseValidator):
    """Validates statistical properties of the data."""
    
    def __init__(self, 
                 max_skewness: float = 3.0,
                 max_outlier_percentage: float = 5.0,
                 min_correlation_threshold: float = 0.95,
                 **kwargs):
        """
        Initialize statistical validator.
        
        Args:
            max_skewness: Maximum allowed skewness
            max_outlier_percentage: Maximum allowed outliers percentage
            min_correlation_threshold: Minimum correlation for high correlation warning
        """
        super().__init__("statistical_validation", **kwargs)
        self.max_skewness = max_skewness
        self.max_outlier_percentage = max_outlier_percentage
        self.min_correlation_threshold = min_correlation_threshold
    
    def validate(self, data: DataFrame) -> ValidationResult:
        """Validate statistical properties."""
        issues = []
        warnings = []
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) == 0:
            return ValidationResult(
                is_valid=True,
                rule_name=self.name,
                message="No numeric columns to validate",
                severity="info"
            )
        
        # Check skewness
        highly_skewed = []
        for col in numeric_columns:
            try:
                skewness = data[col].skew()
                if abs(skewness) > self.max_skewness:
                    highly_skewed.append(f"{col} (skew: {skewness:.2f})")
            except:
                pass
        
        if highly_skewed:
            warnings.append(f"Highly skewed columns: {highly_skewed}")
        
        # Check outliers using IQR method
        outlier_info = []
        for col in numeric_columns:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((data[col] < Q1 - 1.5 * IQR) | (data[col] > Q3 + 1.5 * IQR)).sum()
            outlier_percentage = (outliers / len(data)) * 100
            
            if outlier_percentage > self.max_outlier_percentage:
                outlier_info.append(f"{col} ({outlier_percentage:.1f}%)")
        
        if outlier_info:
            issues.append(f"High outlier percentage: {outlier_info}")
        
        # Check for highly correlated features
        if len(numeric_columns) > 1:
            corr_matrix = data[numeric_columns].corr().abs()
            high_corr_pairs = []
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    if corr_matrix.iloc[i, j] > self.min_correlation_threshold:
                        col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                        high_corr_pairs.append(f"{col1}-{col2} ({corr_matrix.iloc[i, j]:.3f})")
            
            if high_corr_pairs:
                warnings.append(f"Highly correlated pairs: {high_corr_pairs}")
        
        is_valid = len(issues) == 0
        message = "Statistical validation passed" if is_valid else f"Statistical issues: {'; '.join(issues)}"
        
        return ValidationResult(
            is_valid=is_valid,
            rule_name=self.name,
            message=message,
            severity=self.severity,
            details={
                'highly_skewed': highly_skewed,
                'outlier_info': outlier_info,
                'high_correlation_pairs': high_corr_pairs,
                'issues': issues,
                'warnings': warnings
            }
        )


class BusinessRuleValidator(BaseValidator):
    """Validates business rules and domain-specific constraints."""
    
    def __init__(self, rules: List[Dict[str, Any]], **kwargs):
        """
        Initialize business rule validator.
        
        Args:
            rules: List of business rules to validate
        """
        super().__init__("business_rules", **kwargs)
        self.rules = rules
    
    def validate(self, data: DataFrame) -> ValidationResult:
        """Validate business rules."""
        issues = []
        warnings = []
        
        for rule in self.rules:
            rule_name = rule.get('name', 'unnamed_rule')
            rule_condition = rule.get('condition')
            rule_severity = rule.get('severity', 'error')
            rule_message = rule.get('message', f'Rule {rule_name} failed')
            
            try:
                # Evaluate condition
                if callable(rule_condition):
                    result = rule_condition(data)
                elif isinstance(rule_condition, str):
                    result = data.eval(rule_condition).all()
                else:
                    continue
                
                if not result:
                    if rule_severity == 'error':
                        issues.append(f"{rule_name}: {rule_message}")
                    else:
                        warnings.append(f"{rule_name}: {rule_message}")
                        
            except Exception as e:
                issues.append(f"Rule {rule_name} evaluation failed: {str(e)}")
        
        is_valid = len(issues) == 0
        message = "Business rules validation passed" if is_valid else f"Business rule violations: {'; '.join(issues)}"
        
        return ValidationResult(
            is_valid=is_valid,
            rule_name=self.name,
            message=message,
            severity=self.severity,
            details={
                'rules_evaluated': len(self.rules),
                'issues': issues,
                'warnings': warnings
            }
        )


class DataValidator:
    """
    Comprehensive data validator that orchestrates multiple validation checks.
    
    Provides a unified interface for running various validation checks
    and generating comprehensive validation reports.
    """
    
    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        """
        Initialize data validator.
        
        Args:
            validators: List of validators to use
        """
        self.validators = validators or []
    
    def add_validator(self, validator: BaseValidator):
        """Add a validator to the validation pipeline."""
        self.validators.append(validator)
    
    def remove_validator(self, validator_name: str):
        """Remove a validator by name."""
        self.validators = [v for v in self.validators if v.name != validator_name]
    
    def validate_data(self, data: DataFrame) -> ValidationReport:
        """
        Run all validators and generate a comprehensive report.
        
        Args:
            data: Data to validate
            
        Returns:
            Comprehensive validation report
        """
        if data.empty:
            return ValidationReport(
                is_valid=False,
                error_count=1,
                warning_count=0,
                info_count=0,
                results=[ValidationResult(
                    is_valid=False,
                    rule_name="empty_data",
                    message="Dataset is empty",
                    severity="error"
                )],
                summary={'total_validators': 0, 'data_empty': True}
            )
        
        results = []
        
        # Run all validators
        for validator in self.validators:
            try:
                result = validator.validate(data)
                results.append(result)
            except Exception as e:
                # If validator fails, create error result
                results.append(ValidationResult(
                    is_valid=False,
                    rule_name=validator.name,
                    message=f"Validator failed: {str(e)}",
                    severity="error"
                ))
        
        # Count results by severity
        error_count = sum(1 for r in results if r.severity == 'error' and not r.is_valid)
        warning_count = sum(1 for r in results if r.severity == 'warning' and not r.is_valid)
        info_count = sum(1 for r in results if r.severity == 'info')
        
        # Overall validation status
        is_valid = error_count == 0
        
        # Generate summary
        summary = {
            'total_validators': len(self.validators),
            'data_shape': data.shape,
            'data_memory_mb': data.memory_usage(deep=True).sum() / 1024**2,
            'validation_passed': is_valid,
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': info_count
        }
        
        return ValidationReport(
            is_valid=is_valid,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            results=results,
            summary=summary
        )
    
    def validate_with_defaults(self, data: DataFrame, 
                              target_column: Optional[str] = None) -> ValidationReport:
        """
        Validate data with default validators.
        
        Args:
            data: Data to validate
            target_column: Name of target column
            
        Returns:
            Validation report
        """
        # Clear existing validators
        self.validators = []
        
        # Add default validators
        self.add_validator(DataQualityValidator(severity='warning'))
        self.add_validator(StatisticalValidator(severity='warning'))
        
        # Add target-specific validation
        if target_column and target_column in data.columns:
            target_rules = [
                {
                    'name': 'target_not_empty',
                    'condition': lambda df: df[target_column].notna().any(),
                    'message': f'Target column {target_column} is completely empty',
                    'severity': 'error'
                },
                {
                    'name': 'target_variance',
                    'condition': lambda df: df[target_column].nunique() > 1,
                    'message': f'Target column {target_column} has no variance',
                    'severity': 'error'
                }
            ]
            
            self.add_validator(BusinessRuleValidator(target_rules, severity='error'))
        
        return self.validate_data(data)


# Utility functions for common validation patterns
def validate_dataset(data: DataFrame, **kwargs) -> ValidationReport:
    """Convenience function to validate a dataset with default settings."""
    validator = DataValidator()
    return validator.validate_with_defaults(data, **kwargs)


def check_data_quality(data: DataFrame) -> Dict[str, Any]:
    """Quick data quality check returning key metrics."""
    return {
        'shape': data.shape,
        'missing_percentage': (data.isnull().sum().sum() / data.size) * 100,
        'duplicate_count': data.duplicated().sum(),
        'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024**2,
        'column_types': data.dtypes.value_counts().to_dict(),
        'numeric_columns': len(data.select_dtypes(include=[np.number]).columns),
        'categorical_columns': len(data.select_dtypes(include=['object', 'category']).columns),
        'datetime_columns': len(data.select_dtypes(include=['datetime64']).columns)
    }


def create_schema_from_data(data: DataFrame) -> Dict[str, str]:
    """Create schema definition from existing data."""
    schema = {}
    for col in data.columns:
        dtype = str(data[col].dtype)
        if dtype.startswith('int'):
            schema[col] = 'int'
        elif dtype.startswith('float'):
            schema[col] = 'float'
        elif dtype == 'object':
            schema[col] = 'string'
        elif dtype.startswith('datetime'):
            schema[col] = 'datetime'
        elif dtype == 'category':
            schema[col] = 'category'
        else:
            schema[col] = dtype
    
    return schema


def validate_for_ml(data: DataFrame, target_column: str) -> ValidationReport:
    """Validate data specifically for machine learning readiness."""
    validator = DataValidator()
    
    # ML-specific validators
    ml_rules = [
        {
            'name': 'sufficient_samples',
            'condition': lambda df: len(df) >= 100,
            'message': 'Dataset has fewer than 100 samples',
            'severity': 'warning'
        },
        {
            'name': 'feature_count',
            'condition': lambda df: len(df.columns) > 1,
            'message': 'Dataset has no features (only target)',
            'severity': 'error'
        },
        {
            'name': 'target_balance',
            'condition': lambda df: (df[target_column].value_counts().min() / len(df)) > 0.01,
            'message': f'Target column {target_column} is severely imbalanced',
            'severity': 'warning'
        },
        {
            'name': 'no_constant_features',
            'condition': lambda df: all(df[col].nunique() > 1 for col in df.columns if col != target_column),
            'message': 'Dataset contains constant features',
            'severity': 'warning'
        }
    ]
    
    validator.add_validator(DataQualityValidator(
        max_missing_percentage=20.0,
        max_duplicate_percentage=5.0,
        severity='warning'
    ))
    
    validator.add_validator(StatisticalValidator(
        max_skewness=5.0,
        max_outlier_percentage=10.0,
        severity='warning'
    ))
    
    validator.add_validator(BusinessRuleValidator(ml_rules, severity='warning'))
    
    return validator.validate_data(data)


class DataProfiler:
    """
    Comprehensive data profiling for understanding dataset characteristics.
    
    Provides detailed analysis of data distribution, quality, and structure
    to support intelligent preprocessing decisions.
    """
    
    def __init__(self):
        """Initialize data profiler."""
        pass
    
    def profile_data(self, data: DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data profile.
        
        Args:
            data: Data to profile
            
        Returns:
            Comprehensive data profile
        """
        profile = {
            'basic_info': self._get_basic_info(data),
            'column_profiles': self._get_column_profiles(data),
            'data_quality': self._get_data_quality_metrics(data),
            'statistical_summary': self._get_statistical_summary(data),
            'correlations': self._get_correlations(data),
            'recommendations': self._get_recommendations(data)
        }
        
        return profile
    
    def _get_basic_info(self, data: DataFrame) -> Dict[str, Any]:
        """Get basic dataset information."""
        return {
            'shape': data.shape,
            'size': data.size,
            'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024**2,
            'column_count': len(data.columns),
            'row_count': len(data),
            'dtypes': data.dtypes.value_counts().to_dict()
        }
    
    def _get_column_profiles(self, data: DataFrame) -> Dict[str, Dict[str, Any]]:
        """Get detailed profile for each column."""
        profiles = {}
        
        for col in data.columns:
            col_data = data[col]
            
            base_profile = {
                'dtype': str(col_data.dtype),
                'non_null_count': col_data.count(),
                'null_count': col_data.isnull().sum(),
                'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
                'unique_count': col_data.nunique(),
                'unique_percentage': (col_data.nunique() / len(col_data)) * 100
            }
            
            # Type-specific profiling
            if pd.api.types.is_numeric_dtype(col_data):
                base_profile.update(self._profile_numeric_column(col_data))
            elif pd.api.types.is_categorical_dtype(col_data) or col_data.dtype == 'object':
                base_profile.update(self._profile_categorical_column(col_data))
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                base_profile.update(self._profile_datetime_column(col_data))
            
            profiles[col] = base_profile
        
        return profiles
    
    def _profile_numeric_column(self, col_data: Series) -> Dict[str, Any]:
        """Profile numeric column."""
        try:
            return {
                'mean': col_data.mean(),
                'std': col_data.std(),
                'min': col_data.min(),
                'max': col_data.max(),
                'q25': col_data.quantile(0.25),
                'q50': col_data.quantile(0.50),
                'q75': col_data.quantile(0.75),
                'skewness': col_data.skew(),
                'kurtosis': col_data.kurtosis(),
                'zeros_count': (col_data == 0).sum(),
                'zeros_percentage': ((col_data == 0).sum() / len(col_data)) * 100,
                'outliers_iqr': self._count_outliers_iqr(col_data),
                'outliers_zscore': self._count_outliers_zscore(col_data)
            }
        except Exception:
            return {}
    
    def _profile_categorical_column(self, col_data: Series) -> Dict[str, Any]:
        """Profile categorical column."""
        try:
            value_counts = col_data.value_counts()
            return {
                'most_frequent': value_counts.index[0] if len(value_counts) > 0 else None,
                'most_frequent_count': value_counts.iloc[0] if len(value_counts) > 0 else 0,
                'most_frequent_percentage': (value_counts.iloc[0] / len(col_data)) * 100 if len(value_counts) > 0 else 0,
                'least_frequent': value_counts.index[-1] if len(value_counts) > 0 else None,
                'least_frequent_count': value_counts.iloc[-1] if len(value_counts) > 0 else 0,
                'cardinality': col_data.nunique(),
                'cardinality_ratio': col_data.nunique() / len(col_data),
                'top_categories': value_counts.head(10).to_dict()
            }
        except Exception:
            return {}
    
    def _profile_datetime_column(self, col_data: Series) -> Dict[str, Any]:
        """Profile datetime column."""
        try:
            clean_data = col_data.dropna()
            if len(clean_data) == 0:
                return {}
                
            return {
                'min_date': clean_data.min(),
                'max_date': clean_data.max(),
                'date_range_days': (clean_data.max() - clean_data.min()).days,
                'most_frequent_year': clean_data.dt.year.mode().iloc[0] if len(clean_data.dt.year.mode()) > 0 else None,
                'most_frequent_month': clean_data.dt.month.mode().iloc[0] if len(clean_data.dt.month.mode()) > 0 else None,
                'most_frequent_day': clean_data.dt.day.mode().iloc[0] if len(clean_data.dt.day.mode()) > 0 else None,
                'weekday_distribution': clean_data.dt.day_name().value_counts().to_dict(),
                'hour_distribution': clean_data.dt.hour.value_counts().to_dict() if hasattr(clean_data.dt, 'hour') else {}
            }
        except Exception:
            return {}
    
    def _get_data_quality_metrics(self, data: DataFrame) -> Dict[str, Any]:
        """Get data quality metrics."""
        return {
            'completeness': ((data.size - data.isnull().sum().sum()) / data.size) * 100,
            'duplicate_rows': data.duplicated().sum(),
            'duplicate_percentage': (data.duplicated().sum() / len(data)) * 100,
            'constant_columns': [col for col in data.columns if data[col].nunique() <= 1],
            'high_cardinality_columns': [col for col in data.columns 
                                       if data[col].nunique() > len(data) * 0.9],
            'missing_by_column': data.isnull().sum().to_dict(),
            'missing_patterns': self._analyze_missing_patterns(data)
        }
    
    def _get_statistical_summary(self, data: DataFrame) -> Dict[str, Any]:
        """Get statistical summary."""
        numeric_data = data.select_dtypes(include=[np.number])
        
        if len(numeric_data.columns) == 0:
            return {}
        
        return {
            'numeric_summary': numeric_data.describe().to_dict(),
            'skewness_summary': numeric_data.skew().to_dict(),
            'kurtosis_summary': numeric_data.kurtosis().to_dict(),
            'highly_skewed_columns': [col for col in numeric_data.columns 
                                    if abs(numeric_data[col].skew()) > 2],
            'zero_variance_columns': [col for col in numeric_data.columns 
                                    if numeric_data[col].var() == 0]
        }
    
    def _get_correlations(self, data: DataFrame) -> Dict[str, Any]:
        """Get correlation analysis."""
        numeric_data = data.select_dtypes(include=[np.number])
        
        if len(numeric_data.columns) < 2:
            return {}
        
        corr_matrix = numeric_data.corr()
        
        # Find highly correlated pairs
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.8:  # High correlation threshold
                    high_corr_pairs.append({
                        'column1': corr_matrix.columns[i],
                        'column2': corr_matrix.columns[j],
                        'correlation': corr_val
                    })
        
        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'high_correlations': high_corr_pairs,
            'max_correlation': corr_matrix.abs().max().max() if not corr_matrix.empty else 0,
            'mean_correlation': corr_matrix.abs().mean().mean() if not corr_matrix.empty else 0
        }
    
    def _get_recommendations(self, data: DataFrame) -> List[Dict[str, Any]]:
        """Get data preprocessing recommendations."""
        recommendations = []
        
        # Missing values recommendations
        missing_percentage = (data.isnull().sum().sum() / data.size) * 100
        if missing_percentage > 20:
            recommendations.append({
                'type': 'missing_values',
                'priority': 'high',
                'message': f'High missing values ({missing_percentage:.1f}%). Consider imputation or removal.',
                'suggested_action': 'impute_missing_values'
            })
        
        # Duplicate rows recommendations
        duplicate_count = data.duplicated().sum()
        if duplicate_count > 0:
            recommendations.append({
                'type': 'duplicates',
                'priority': 'medium',
                'message': f'Found {duplicate_count} duplicate rows. Consider removal.',
                'suggested_action': 'remove_duplicates'
            })
        
        # High cardinality recommendations
        for col in data.columns:
            if data[col].nunique() > len(data) * 0.9:
                recommendations.append({
                    'type': 'high_cardinality',
                    'priority': 'medium',
                    'message': f'Column {col} has very high cardinality. Consider feature engineering.',
                    'suggested_action': 'reduce_cardinality'
                })
        
        # Skewness recommendations
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            try:
                skewness = data[col].skew()
                if abs(skewness) > 2:
                    recommendations.append({
                        'type': 'skewness',
                        'priority': 'low',
                        'message': f'Column {col} is highly skewed ({skewness:.2f}). Consider transformation.',
                        'suggested_action': 'transform_skewed_feature'
                    })
            except:
                pass
        
        return recommendations
    
    def _count_outliers_iqr(self, col_data: Series) -> int:
        """Count outliers using IQR method."""
        try:
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)).sum()
            return outliers
        except:
            return 0
    
    def _count_outliers_zscore(self, col_data: Series, threshold: float = 3.0) -> int:
        """Count outliers using Z-score method."""
        try:
            z_scores = np.abs((col_data - col_data.mean()) / col_data.std())
            outliers = (z_scores > threshold).sum()
            return outliers
        except:
            return 0
    
    def _analyze_missing_patterns(self, data: DataFrame) -> Dict[str, Any]:
        """Analyze missing value patterns."""
        missing_patterns = {}
        
        # Check if missing values are random or systematic
        missing_mask = data.isnull()
        
        # Pattern 1: Missing values concentrated in specific rows
        missing_per_row = missing_mask.sum(axis=1)
        rows_with_missing = (missing_per_row > 0).sum()
        
        missing_patterns['rows_with_missing'] = rows_with_missing
        missing_patterns['rows_with_missing_percentage'] = (rows_with_missing / len(data)) * 100
        
        # Pattern 2: Missing values concentrated in specific columns
        missing_per_col = missing_mask.sum(axis=0)
        cols_with_missing = (missing_per_col > 0).sum()
        
        missing_patterns['columns_with_missing'] = cols_with_missing
        missing_patterns['columns_with_missing_percentage'] = (cols_with_missing / len(data.columns)) * 100
        
        # Pattern 3: Correlation between missing values in different columns
        if cols_with_missing > 1:
            missing_corr = missing_mask.corr()
            high_missing_corr = []
            
            for i in range(len(missing_corr.columns)):
                for j in range(i + 1, len(missing_corr.columns)):
                    corr_val = missing_corr.iloc[i, j]
                    if abs(corr_val) > 0.5:  # High correlation in missingness
                        high_missing_corr.append({
                            'column1': missing_corr.columns[i],
                            'column2': missing_corr.columns[j],
                            'correlation': corr_val
                        })
            
            missing_patterns['missing_correlations'] = high_missing_corr
        
        return missing_patterns


# Example usage
if __name__ == "__main__":
    # Create sample data with various issues
    np.random.seed(42)
    
    sample_data = pd.DataFrame({
        'id': range(1000),
        'feature1': np.random.normal(0, 1, 1000),
        'feature2': np.random.exponential(1, 1000),  # Highly skewed
        'category': np.random.choice(['A', 'B', 'C'], 1000),
        'high_card': [f'item_{i}' for i in np.random.randint(0, 800, 1000)],  # High cardinality
        'target': np.random.choice([0, 1], 1000, p=[0.7, 0.3])
    })
    
    # Introduce missing values
    sample_data.loc[::10, 'feature1'] = np.nan
    sample_data.loc[::15, 'category'] = np.nan
    
    # Introduce duplicates
    sample_data = pd.concat([sample_data, sample_data.iloc[:50]], ignore_index=True)
    
    # Test validation
    print("🧪 Testing Data Validation...")
    
    # Basic validation
    report = validate_dataset(sample_data, target_column='target')
    print(f"Validation passed: {report.is_valid}")
    print(f"Errors: {report.error_count}, Warnings: {report.warning_count}")
    
    # ML-specific validation
    ml_report = validate_for_ml(sample_data, 'target')
    print(f"ML validation passed: {ml_report.is_valid}")
    
    # Data profiling
    profiler = DataProfiler()
    profile = profiler.profile_data(sample_data)
    print(f"Data profile generated with {len(profile['recommendations'])} recommendations")
    
    # Show some recommendations
    for rec in profile['recommendations'][:3]:
        print(f"- {rec['type']}: {rec['message']}")
    
    print("✅ Validation system test completed!")