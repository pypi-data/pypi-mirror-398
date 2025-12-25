# ===================================
# FILE: automl_framework/data/preprocessors.py
# LOCATION: /automl_framework/automl_framework/data/preprocessors.py
# FIXED VERSION - Bug #2 resolved
# ===================================

"""
Data preprocessing components for the AutoML framework.

This module implements concrete data processors that handle missing values,
feature scaling, categorical encoding, and other data transformations.

FIXES APPLIED:
- Fixed high-cardinality column handling in CategoricalEncoder
- Improved categorical column detection
- Better NaN handling throughout encoding process
"""
from ..core.base import DataProcessor
from ..core.exceptions import PreprocessingError, handle_sklearn_error

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from sklearn.preprocessing import (
    MinMaxScaler, StandardScaler, RobustScaler, QuantileTransformer,
    OneHotEncoder, LabelEncoder, OrdinalEncoder, 
    PowerTransformer, KBinsDiscretizer
)
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import SelectKBest, mutual_info_classif, mutual_info_regression
from sklearn.compose import ColumnTransformer
import warnings
from ..core.types import DataFrame, Series, ScalingMethod, EncodingMethod


class MissingValueHandler(DataProcessor):
    """
    Handles missing values in datasets using various imputation strategies.
    
    Supports different strategies for numeric and categorical features,
    with automatic detection of column types.
    """
    
    def __init__(self, 
                numeric_strategy: str = 'median',
                categorical_strategy: str = 'most_frequent',
                fill_value: Optional[Union[str, int, float]] = None,
                n_neighbors: Optional[int] = None):
        """Initialize the missing value handler."""
        self.numeric_strategy = numeric_strategy
        self.categorical_strategy = categorical_strategy
        self.fill_value = fill_value
        self.n_neighbors = n_neighbors
        
        # Initialize attributes that will be set during fit
        self.numeric_columns: List[str] = []
        self.categorical_columns: List[str] = []
        self.numeric_stats: Dict[str, Dict[str, float]] = {}
        self.categorical_stats: Dict[str, Dict[str, Any]] = {}
        self._fitted = False
    
    @handle_sklearn_error
    def fit(self, data: pd.DataFrame) -> 'MissingValueHandler':
        """Fit the handler by computing imputation statistics."""
        # Identify columns by type
        self.numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_columns = data.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Initialize stats dictionaries
        self.numeric_stats = {}
        self.categorical_stats = {}
        
        # Compute numeric statistics for ALL numeric columns
        for col in self.numeric_columns:
            self.numeric_stats[col] = {
                'mean': data[col].mean(),
                'median': data[col].median()
            }
        
        # Compute categorical statistics for ALL categorical columns
        for col in self.categorical_columns:
            mode_val = data[col].mode()
            self.categorical_stats[col] = {
                'most_frequent': mode_val.iloc[0] if len(mode_val) > 0 else 'Unknown'
            }
        
        self._fitted = True
        return self   
    
    @handle_sklearn_error
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform data by imputing missing values."""
        if not self._fitted:
            raise PreprocessingError("MissingValueHandler must be fitted before transform")
        
        data_copy = data.copy()
        
        # Handle numeric columns
        for col in self.numeric_columns:
            if col in data_copy.columns and data_copy[col].isnull().any():
                if self.numeric_strategy == 'mean':
                    fill_value = self.numeric_stats[col]['mean']
                elif self.numeric_strategy == 'median':
                    fill_value = self.numeric_stats[col]['median']
                else:
                    fill_value = self.fill_value
                
                data_copy[col] = data_copy[col].fillna(fill_value)
        
        # Handle categorical columns  
        for col in self.categorical_columns:
            if col in data_copy.columns and data_copy[col].isnull().any():
                if self.categorical_strategy == 'most_frequent':
                    fill_value = self.categorical_stats[col]['most_frequent']
                else:
                    fill_value = self.fill_value
                
                data_copy[col] = data_copy[col].fillna(fill_value)
        
        # Safety net for any remaining missing values
        for col in data_copy.columns:
            if data_copy[col].isnull().any():
                if data_copy[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                    # For numeric columns not handled above
                    if col not in self.numeric_columns:
                        fill_value = data_copy[col].median()
                        if pd.isna(fill_value):
                            fill_value = 0
                        data_copy[col] = data_copy[col].fillna(fill_value)
                else:
                    # For any remaining non-numeric columns
                    if col not in self.categorical_columns:
                        data_copy[col] = data_copy[col].fillna('Unknown')
        
        return data_copy
    
    def get_params(self) -> Dict[str, Any]:
        """Get parameters of the processor."""
        return {
            'numeric_strategy': self.numeric_strategy,
            'categorical_strategy': self.categorical_strategy,
            'fill_value': self.fill_value,
            'n_neighbors': self.n_neighbors
        }
    
    def set_params(self, **params) -> 'MissingValueHandler':
        """Set parameters of the processor."""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
        self._fitted = False
        return self


class FeatureScaler(DataProcessor):
    """
    Scales numerical features using various scaling methods.
    
    Automatically identifies numeric columns and applies scaling
    while preserving non-numeric columns.
    """
    
    def __init__(self, method: str = 'minmax', **scaler_params):
        """
        Initialize the feature scaler.
        
        Args:
            method: Scaling method ('minmax', 'standard', 'robust', 'quantile')
            **scaler_params: Additional parameters for the scaler
        """
        self.method = method
        self.scaler_params = scaler_params
        self.scaler = None
        self.numeric_columns: List[str] = []
        self._fitted = False
        
        # Initialize scaler based on method
        self._init_scaler()
    
    def _init_scaler(self):
        """Initialize the appropriate scaler based on method."""
        scaler_map = {
            'minmax': MinMaxScaler,
            'standard': StandardScaler,
            'robust': RobustScaler,
            'quantile': QuantileTransformer
        }
        
        if self.method not in scaler_map:
            raise PreprocessingError(f"Unknown scaling method: {self.method}")
        
        self.scaler = scaler_map[self.method](**self.scaler_params)
    
    @handle_sklearn_error
    def fit(self, data: DataFrame) -> 'FeatureScaler':
        """Fit the scaler to numeric columns."""
        self.numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if self.numeric_columns:
            self.scaler.fit(data[self.numeric_columns])
        
        self._fitted = True
        return self
    
    @handle_sklearn_error
    def transform(self, data: DataFrame) -> DataFrame:
        """Transform data by scaling numeric features."""
        if not self._fitted:
            raise PreprocessingError("FeatureScaler must be fitted before transform")
        
        if not self.numeric_columns:
            return data.copy()
        
        data_copy = data.copy()
        scaled_data = self.scaler.transform(data_copy[self.numeric_columns])
        data_copy[self.numeric_columns] = scaled_data
        
        return data_copy
    
    def get_params(self) -> Dict[str, Any]:
        """Get parameters of the processor."""
        params = {'method': self.method}
        params.update(self.scaler_params)
        return params
    
    def set_params(self, **params) -> 'FeatureScaler':
        """Set parameters of the processor."""
        if 'method' in params:
            self.method = params.pop('method')
            self._init_scaler()
        
        self.scaler_params.update(params)
        self._init_scaler()
        self._fitted = False
        return self


class CategoricalEncoder(DataProcessor):
    """
    FIXED: Categorical encoder that properly handles high-cardinality columns.
    
    Key fixes:
    - Drops high-cardinality columns instead of skipping (which caused NaN)
    - Better detection of ID-like columns
    - Ensures 100% numeric output, no NaN values
    """
    
    def __init__(self, 
                 method: str = 'label',
                 handle_unknown: str = 'ignore',
                 drop_first: bool = False,
                 max_categories: Optional[int] = 50):
        """
        Initialize the categorical encoder.
        
        Args:
            method: Encoding method ('onehot', 'label', 'ordinal')
            handle_unknown: How to handle unknown categories ('ignore', 'error')
            drop_first: Whether to drop first category in one-hot encoding
            max_categories: Maximum categories per feature (default: 50)
        """
        self.method = method
        self.handle_unknown = handle_unknown
        self.drop_first = drop_first
        self.max_categories = max_categories or 50
        
        self.encoders: Dict[str, LabelEncoder] = {}
        self.categorical_columns: List[str] = []
        self.high_cardinality_columns: List[str] = []
        self.columns_to_drop: List[str] = []
        self._fitted = False
    
    @handle_sklearn_error
    def fit(self, data: pd.DataFrame) -> 'CategoricalEncoder':
        """Fit the encoder to categorical columns."""
        # Identify categorical columns
        self.categorical_columns = data.select_dtypes(
            include=['object', 'category']
        ).columns.tolist()
        
        if not self.categorical_columns:
            self._fitted = True
            return self
        
        print(f"  🔍 Found categorical columns: {self.categorical_columns}")
        
        # Identify high-cardinality and ID-like columns
        self.high_cardinality_columns = []
        self.columns_to_drop = []
        
        for col in self.categorical_columns:
            n_unique = data[col].nunique()
            n_rows = len(data)
            
            # Check if column is ID-like (nearly unique for every row)
            if n_unique / n_rows > 0.95:
                self.columns_to_drop.append(col)
                print(f"  🗑️  Will drop ID-like column '{col}' ({n_unique} unique / {n_rows} rows)")
            
            # Check if column exceeds max_categories
            elif n_unique > self.max_categories:
                self.high_cardinality_columns.append(col)
                self.columns_to_drop.append(col)
                print(f"  🗑️  Will drop high-cardinality column '{col}' ({n_unique} categories > {self.max_categories} max)")
        
        # Filter out columns to drop
        columns_to_encode = [
            col for col in self.categorical_columns 
            if col not in self.columns_to_drop
        ]
        
        if not columns_to_encode:
            print(f"  ⚠️  No categorical columns remain after filtering")
            self._fitted = True
            return self
        
        # Fit label encoders for remaining columns
        if self.method == 'label':
            for col in columns_to_encode:
                le = LabelEncoder()
                # Fit on non-null values
                non_null_values = data[col].dropna().astype(str)
                if len(non_null_values) > 0:
                    le.fit(non_null_values)
                    self.encoders[col] = le
        
        print(f"  ✅ Fitted {self.method} encoder for {len(self.encoders)} columns")
        self._fitted = True
        return self
    
    @handle_sklearn_error
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform categorical features to numerical.
        
        CRITICAL FIX: Actually DROPS high-cardinality columns instead of 
        skipping them (which caused them to become NaN).
        """
        if not self._fitted:
            raise PreprocessingError("CategoricalEncoder must be fitted before transform")
        
        data_copy = data.copy()
        
        # CRITICAL FIX: Drop high-cardinality columns FIRST
        if self.columns_to_drop:
            cols_to_drop_present = [
                col for col in self.columns_to_drop 
                if col in data_copy.columns
            ]
            if cols_to_drop_present:
                print(f"  🗑️  Dropping {len(cols_to_drop_present)} high-cardinality/ID columns")
                data_copy = data_copy.drop(columns=cols_to_drop_present)
        
        # Encode remaining categorical columns
        if self.method == 'label':
            for col, encoder in self.encoders.items():
                if col not in data_copy.columns:
                    continue
                
                # Convert to string
                col_data = data_copy[col].astype(str)
                
                # Separate known and unknown values
                known_categories = set(encoder.classes_)
                is_known = col_data.isin(known_categories)
                is_null = data_copy[col].isna()
                
                # Initialize with default value
                encoded_values = np.full(len(col_data), -1, dtype=int)
                
                # Encode known categories
                if is_known.any():
                    encoded_values[is_known] = encoder.transform(col_data[is_known])
                
                # Handle nulls (use -2 to distinguish from unknown)
                if is_null.any():
                    encoded_values[is_null] = -2
                
                # Handle unknowns (keep as -1)
                # -1 for unknown, -2 for null
                
                data_copy[col] = encoded_values
        
        # FINAL SAFETY CHECK: Ensure NO object/categorical columns remain
        for col in data_copy.columns:
            if data_copy[col].dtype == 'object' or pd.api.types.is_categorical_dtype(data_copy[col]):
                print(f"  ⚠️  Converting remaining non-numeric column '{col}' to numeric")
                try:
                    # Try numeric conversion
                    data_copy[col] = pd.to_numeric(data_copy[col], errors='coerce')
                    # Fill any NaN from failed conversion
                    if data_copy[col].isna().any():
                        data_copy[col] = data_copy[col].fillna(-999)
                except:
                    # If all else fails, drop it
                    print(f"  ❌ Dropping problematic column '{col}'")
                    data_copy = data_copy.drop(columns=[col])
        
        # Verify no NaN values leaked through
        final_missing = data_copy.isnull().sum().sum()
        if final_missing > 0:
            print(f"  ⚠️  WARNING: {final_missing} NaN values remain after encoding")
            # Fill them with a safe value
            data_copy = data_copy.fillna(-999)
            print(f"  ✅ Filled remaining NaN with -999")
        
        return data_copy
    
    def get_params(self) -> Dict[str, Any]:
        """Get parameters of the processor."""
        return {
            'method': self.method,
            'handle_unknown': self.handle_unknown,
            'drop_first': self.drop_first,
            'max_categories': self.max_categories
        }
    
    def set_params(self, **params) -> 'CategoricalEncoder':
        """Set parameters of the processor."""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
        self._fitted = False
        return self


class OutlierHandler(DataProcessor):
    """
    Handles outliers in numeric features using various detection and treatment methods.
    
    Supports IQR, Z-score, and Isolation Forest methods for outlier detection,
    with options to remove, cap, or transform outliers.
    """
    
    def __init__(self, 
                 method: str = 'iqr',
                 treatment: str = 'cap',
                 threshold: float = 1.5,
                 contamination: float = 0.1):
        """
        Initialize the outlier handler.
        
        Args:
            method: Detection method ('iqr', 'zscore', 'isolation_forest')
            treatment: Treatment method ('remove', 'cap', 'transform')
            threshold: Threshold for IQR or Z-score methods
            contamination: Expected proportion of outliers for Isolation Forest
        """
        self.method = method
        self.treatment = treatment
        self.threshold = threshold
        self.contamination = contamination
        
        self.numeric_columns: List[str] = []
        self.lower_bounds: Dict[str, float] = {}
        self.upper_bounds: Dict[str, float] = {}
        self._fitted = False
    
    @handle_sklearn_error
    def fit(self, data: DataFrame) -> 'OutlierHandler':
        """Fit the outlier handler to compute bounds."""
        self.numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not self.numeric_columns:
            self._fitted = True
            return self
        
        for col in self.numeric_columns:
            if self.method == 'iqr':
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                self.lower_bounds[col] = Q1 - self.threshold * IQR
                self.upper_bounds[col] = Q3 + self.threshold * IQR
                
            elif self.method == 'zscore':
                mean = data[col].mean()
                std = data[col].std()
                self.lower_bounds[col] = mean - self.threshold * std
                self.upper_bounds[col] = mean + self.threshold * std
        
        self._fitted = True
        return self
    
    @handle_sklearn_error
    def transform(self, data: DataFrame) -> DataFrame:
        """Transform data by handling outliers."""
        if not self._fitted:
            raise PreprocessingError("OutlierHandler must be fitted before transform")
        
        if not self.numeric_columns:
            return data.copy()
        
        data_copy = data.copy()
        
        for col in self.numeric_columns:
            if col in self.lower_bounds:
                if self.treatment == 'cap':
                    data_copy[col] = data_copy[col].clip(
                        lower=self.lower_bounds[col],
                        upper=self.upper_bounds[col]
                    )
                elif self.treatment == 'remove':
                    mask = (
                        (data_copy[col] >= self.lower_bounds[col]) &
                        (data_copy[col] <= self.upper_bounds[col])
                    )
                    data_copy = data_copy[mask]
        
        return data_copy
    
    def get_params(self) -> Dict[str, Any]:
        """Get parameters of the processor."""
        return {
            'method': self.method,
            'treatment': self.treatment,
            'threshold': self.threshold,
            'contamination': self.contamination
        }
    
    def set_params(self, **params) -> 'OutlierHandler':
        """Set parameters of the processor."""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
        self._fitted = False
        return self


class FeatureEngineering(DataProcessor):
    """
    Creates new features through polynomial features, interactions, and transformations.
    
    Supports polynomial feature creation, interaction terms,
    and mathematical transformations of existing features.
    """
    
    def __init__(self, 
                 polynomial_degree: int = 2,
                 interaction_only: bool = False,
                 include_bias: bool = False,
                 log_transform: bool = False,
                 sqrt_transform: bool = False):
        """
        Initialize the feature engineering processor.
        
        Args:
            polynomial_degree: Degree for polynomial features
            interaction_only: Only create interaction terms, no powers
            include_bias: Include bias column in polynomial features
            log_transform: Apply log transformation to positive features
            sqrt_transform: Apply square root transformation
        """
        self.polynomial_degree = polynomial_degree
        self.interaction_only = interaction_only
        self.include_bias = include_bias
        self.log_transform = log_transform
        self.sqrt_transform = sqrt_transform
        
        self.numeric_columns: List[str] = []
        self.log_columns: List[str] = []
        self.sqrt_columns: List[str] = []
        self._fitted = False
    
    @handle_sklearn_error
    def fit(self, data: DataFrame) -> 'FeatureEngineering':
        """Fit the feature engineering processor."""
        self.numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if self.log_transform:
            # Identify columns suitable for log transformation (positive values)
            self.log_columns = [
                col for col in self.numeric_columns 
                if (data[col] > 0).all()
            ]
        
        if self.sqrt_transform:
            # Identify columns suitable for sqrt transformation (non-negative values)
            self.sqrt_columns = [
                col for col in self.numeric_columns 
                if (data[col] >= 0).all()
            ]
        
        self._fitted = True
        return self
    
    @handle_sklearn_error
    def transform(self, data: DataFrame) -> DataFrame:
        """Transform data by engineering new features."""
        if not self._fitted:
            raise PreprocessingError("FeatureEngineering must be fitted before transform")
        
        data_copy = data.copy()
        
        # Log transformation
        if self.log_transform and self.log_columns:
            for col in self.log_columns:
                data_copy[f'{col}_log'] = np.log1p(data_copy[col])
        
        # Square root transformation
        if self.sqrt_transform and self.sqrt_columns:
            for col in self.sqrt_columns:
                data_copy[f'{col}_sqrt'] = np.sqrt(data_copy[col])
        
        return data_copy    
    
    def get_params(self) -> Dict[str, Any]:
        """Get parameters of the processor."""
        return {
            'polynomial_degree': self.polynomial_degree,
            'interaction_only': self.interaction_only,
            'include_bias': self.include_bias,
            'log_transform': self.log_transform,
            'sqrt_transform': self.sqrt_transform
        }
    
    def set_params(self, **params) -> 'FeatureEngineering':
        """Set parameters of the processor."""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
        self._fitted = False
        return self


class DateTimeProcessor(DataProcessor):
    """
    Processes datetime columns by extracting useful features.
    
    Extracts year, month, day, hour, minute, weekday, quarter,
    and other temporal features from datetime columns.
    """
    
    def __init__(self, 
                 datetime_columns: Optional[List[str]] = None,
                 extract_components: bool = True,
                 extract_cyclical: bool = True,
                 drop_original: bool = True):
        """
        Initialize the datetime processor.
        
        Args:
            datetime_columns: List of datetime column names (auto-detect if None)
            extract_components: Extract basic components (year, month, etc.)
            extract_cyclical: Extract cyclical features (sin/cos of time components)
            drop_original: Drop original datetime columns after processing
        """
        self.datetime_columns = datetime_columns
        self.extract_components = extract_components
        self.extract_cyclical = extract_cyclical
        self.drop_original = drop_original
        
        self.detected_datetime_columns: List[str] = []
        self._fitted = False
    
    def _detect_datetime_columns(self, data: DataFrame) -> List[str]:
        """Detect datetime columns in the DataFrame with improved error handling."""
        datetime_cols = []
        
        # Check existing datetime columns
        datetime_cols.extend(data.select_dtypes(include=['datetime64']).columns.tolist())
        
        # Try to parse object columns as datetime
        for col in data.select_dtypes(include=['object']).columns:
            try:
                sample = data[col].dropna().head(100)
                if len(sample) == 0:
                    continue
                
                # Suppress warnings during datetime detection
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    
                    try:
                        pd.to_datetime(sample, errors='raise')
                        datetime_cols.append(col)
                        continue
                    except:
                        pass
                    
                    try:
                        parsed = pd.to_datetime(sample, errors='coerce', infer_datetime_format=True)
                        if (parsed.notna().sum() / len(sample)) > 0.8:
                            datetime_cols.append(col)
                            continue
                    except:
                        pass
                        
            except:
                pass
        
        return list(set(datetime_cols))
    
    @handle_sklearn_error
    def fit(self, data: DataFrame) -> 'DateTimeProcessor':
        """Fit the datetime processor."""
        if self.datetime_columns is None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.detected_datetime_columns = self._detect_datetime_columns(data)
        else:
            self.detected_datetime_columns = self.datetime_columns
        
        self._fitted = True
        return self
    
    @handle_sklearn_error
    def transform(self, data: DataFrame) -> DataFrame:
        """Transform data by extracting datetime features."""
        if not self._fitted:
            raise PreprocessingError("DateTimeProcessor must be fitted before transform")
        
        if not self.detected_datetime_columns:
            return data.copy()
        
        data_copy = data.copy()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            for col in self.detected_datetime_columns:
                if col not in data_copy.columns:
                    continue
                    
                # Convert to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(data_copy[col]):
                    try:
                        data_copy[col] = pd.to_datetime(data_copy[col], errors='coerce')
                    except:
                        continue
                
                dt_col = data_copy[col]
                
                if dt_col.isna().all():
                    continue
                
                if self.extract_components:
                    try:
                        data_copy[f'{col}_year'] = dt_col.dt.year
                        data_copy[f'{col}_month'] = dt_col.dt.month
                        data_copy[f'{col}_day'] = dt_col.dt.day
                        data_copy[f'{col}_hour'] = dt_col.dt.hour
                        data_copy[f'{col}_minute'] = dt_col.dt.minute
                        data_copy[f'{col}_weekday'] = dt_col.dt.weekday
                        data_copy[f'{col}_quarter'] = dt_col.dt.quarter
                        data_copy[f'{col}_is_weekend'] = (dt_col.dt.weekday >= 5).astype(int)
                    except Exception:
                        continue
                    
                if self.extract_cyclical:
                    try:
                        data_copy[f'{col}_month_sin'] = np.sin(2 * np.pi * dt_col.dt.month / 12)
                        data_copy[f'{col}_month_cos'] = np.cos(2 * np.pi * dt_col.dt.month / 12)
                        data_copy[f'{col}_day_sin'] = np.sin(2 * np.pi * dt_col.dt.day / 31)
                        data_copy[f'{col}_day_cos'] = np.cos(2 * np.pi * dt_col.dt.day / 31)
                        data_copy[f'{col}_hour_sin'] = np.sin(2 * np.pi * dt_col.dt.hour / 24)
                        data_copy[f'{col}_hour_cos'] = np.cos(2 * np.pi * dt_col.dt.hour / 24)
                    except Exception:
                        pass
        
        # Drop original datetime columns if requested
        if self.drop_original:
            columns_to_drop = [col for col in self.detected_datetime_columns if col in data_copy.columns]
            data_copy = data_copy.drop(columns=columns_to_drop)
        
        return data_copy
    
    def get_params(self) -> Dict[str, Any]:
        """Get parameters of the processor."""
        return {
            'datetime_columns': self.datetime_columns,
            'extract_components': self.extract_components,
            'extract_cyclical': self.extract_cyclical,
            'drop_original': self.drop_original
        }
    
    def set_params(self, **params) -> 'DateTimeProcessor':
        """Set parameters of the processor."""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
        self._fitted = False
        return self    


class FeatureSelector(DataProcessor):
    """
    Selects the most important features using various selection methods.
    
    Supports univariate selection, recursive feature elimination,
    and other feature selection techniques.
    """
    
    def __init__(self, 
                 method: str = 'mutual_info',
                 k: int = 10,
                 threshold: Optional[float] = None):
        """
        Initialize the feature selector.
        
        Args:
            method: Selection method ('mutual_info', 'chi2', 'f_test')
            k: Number of features to select
            threshold: Threshold for feature scores (if not using k)
        """
        self.method = method
        self.k = k
        self.threshold = threshold
        
        self.selector = None
        self.selected_features: List[str] = []
        self._fitted = False
    
    @handle_sklearn_error
    def fit(self, data: DataFrame, target: Optional[Series] = None) -> 'FeatureSelector':
        """Fit the feature selector."""
        if target is None:
            raise PreprocessingError("Target variable required for feature selection")
        
        # Select only numeric columns for feature selection
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            self._fitted = True
            return self
        
        # Choose selection method
        if self.method == 'mutual_info':
            if target.dtype == 'object' or target.nunique() < 20:
                score_func = mutual_info_classif
            else:
                score_func = mutual_info_regression
        else:
            raise PreprocessingError(f"Unknown selection method: {self.method}")
        
        # Initialize selector
        if self.threshold is not None:
            from sklearn.feature_selection import SelectPercentile
            self.selector = SelectPercentile(score_func=score_func, percentile=self.threshold)
        else:
            self.selector = SelectKBest(score_func=score_func, k=min(self.k, numeric_data.shape[1]))
        
        # Fit selector
        self.selector.fit(numeric_data, target)
        
        # Get selected feature names
        selected_mask = self.selector.get_support()
        self.selected_features = numeric_data.columns[selected_mask].tolist()
        
        # Add non-numeric columns to selected features
        non_numeric_columns = data.select_dtypes(exclude=[np.number]).columns.tolist()
        self.selected_features.extend(non_numeric_columns)
        
        self._fitted = True
        return self
    
    @handle_sklearn_error
    def transform(self, data: DataFrame) -> DataFrame:
        """Transform data by selecting features."""
        if not self._fitted:
            raise PreprocessingError("FeatureSelector must be fitted before transform")
        
        # Return only selected features
        available_features = [col for col in self.selected_features if col in data.columns]
        return data[available_features].copy()
    
    def get_params(self) -> Dict[str, Any]:
        """Get parameters of the processor."""
        return {
            'method': self.method,
            'k': self.k,
            'threshold': self.threshold
        }
    
    def set_params(self, **params) -> 'FeatureSelector':
        """Set parameters of the processor."""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
        self._fitted = False
        return self
    
    def get_feature_scores(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self._fitted or self.selector is None:
            return {}
        
        numeric_data_columns = self.selector.feature_names_in_ if hasattr(self.selector, 'feature_names_in_') else []
        scores = self.selector.scores_ if hasattr(self.selector, 'scores_') else []
        
        if len(numeric_data_columns) == len(scores):
            return dict(zip(numeric_data_columns, scores))
        
        return {}