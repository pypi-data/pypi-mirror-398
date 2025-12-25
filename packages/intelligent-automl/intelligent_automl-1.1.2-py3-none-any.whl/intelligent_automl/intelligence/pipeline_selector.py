# ===================================
# FILE: automl_framework/intelligence/pipeline_selector.py
# LOCATION: /automl_framework/automl_framework/intelligence/pipeline_selector.py
# ===================================

"""
Intelligent Pipeline Selector for AutoML Framework

This module automatically analyzes datasets and selects the most suitable
preprocessing steps based on data characteristics, patterns, and best practices.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder
import warnings

from ..core.base import DataProcessor
from ..core.exceptions import PreprocessingError
from ..data.pipeline import DataPipeline
from ..data.preprocessors import (
    MissingValueHandler, FeatureScaler, CategoricalEncoder,
    OutlierHandler, DateTimeProcessor, FeatureEngineering, FeatureSelector
)


@dataclass
class DataCharacteristics:
    """Data characteristics discovered through intelligent analysis."""
    
    # Basic info
    n_rows: int
    n_features: int
    memory_usage_mb: float
    
    # Missing values
    missing_percentage: float
    features_with_missing: List[str]
    missing_pattern: str  # 'random', 'systematic', 'clustered'
    
    # Feature types
    numeric_features: List[str]
    categorical_features: List[str]
    datetime_features: List[str]
    text_features: List[str]
    
    # Data quality
    duplicate_rows: int
    outlier_percentage: float
    high_cardinality_cats: List[str]  # categorical features with >50 unique values
    
    # Distribution characteristics
    skewed_features: List[str]
    sparse_features: List[str]  # features with >90% zeros
    correlated_feature_pairs: List[Tuple[str, str, float]]
    
    # Target analysis (if provided)
    target_type: Optional[str] = None  # 'binary', 'multiclass', 'continuous'
    target_balance: Optional[Dict[str, float]] = None
    target_missing: Optional[float] = None


@dataclass
class ProcessingRecommendation:
    """Recommendation for a specific preprocessing step."""
    
    step_name: str
    processor_class: str
    parameters: Dict[str, Any]
    reasoning: str
    confidence: float  # 0.0 to 1.0
    priority: int  # 1 (highest) to 5 (lowest)


class IntelligentPipelineSelector:
    """
    Intelligent selector that analyzes data and recommends optimal preprocessing pipeline.
    
    Uses statistical analysis, data profiling, and ML best practices to automatically
    determine the most suitable preprocessing steps for any dataset.
    """
    
    def __init__(self, target_column: Optional[str] = None, task_type: Optional[str] = None):
        """
        Initialize the intelligent pipeline selector.
        
        Args:
            target_column: Name of target column (for supervised learning)
            task_type: 'classification' or 'regression' (auto-detected if None)
        """
        self.target_column = target_column
        self.task_type = task_type
        self.data_characteristics: Optional[DataCharacteristics] = None
        self.recommendations: List[ProcessingRecommendation] = []
    
    def analyze_data(self, df: pd.DataFrame) -> DataCharacteristics:
        """
        Perform comprehensive data analysis to understand characteristics.
        
        Args:
            df: Input DataFrame to analyze
            
        Returns:
            DataCharacteristics object with analysis results
        """
        print("🔍 Analyzing data characteristics...")
        
        # Basic info
        n_rows, n_features = df.shape
        memory_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Missing values analysis
        missing_counts = df.isnull().sum()
        missing_percentage = (missing_counts.sum() / (n_rows * n_features)) * 100
        features_with_missing = missing_counts[missing_counts > 0].index.tolist()
        missing_pattern = self._analyze_missing_pattern(df)
        
        # Feature type detection
        numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_features = self._detect_datetime_features(df)
        text_features = self._detect_text_features(df)
        
        # Data quality analysis
        duplicate_rows = df.duplicated().sum()
        outlier_percentage = self._calculate_outlier_percentage(df[numeric_features])
        high_cardinality_cats = self._detect_high_cardinality_categorical(df)
        
        # Distribution analysis
        skewed_features = self._detect_skewed_features(df[numeric_features])
        sparse_features = self._detect_sparse_features(df[numeric_features])
        correlated_pairs = self._detect_correlated_features(df[numeric_features])
        
        # Target analysis
        target_type = None
        target_balance = None
        target_missing = None
        
        if self.target_column and self.target_column in df.columns:
            target_type = self._analyze_target_type(df[self.target_column])
            if target_type in ['binary', 'multiclass']:
                target_balance = self._calculate_target_balance(df[self.target_column])
            target_missing = (df[self.target_column].isnull().sum() / len(df)) * 100
        
        characteristics = DataCharacteristics(
            n_rows=n_rows,
            n_features=n_features,
            memory_usage_mb=memory_usage_mb,
            missing_percentage=missing_percentage,
            features_with_missing=features_with_missing,
            missing_pattern=missing_pattern,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            datetime_features=datetime_features,
            text_features=text_features,
            duplicate_rows=duplicate_rows,
            outlier_percentage=outlier_percentage,
            high_cardinality_cats=high_cardinality_cats,
            skewed_features=skewed_features,
            sparse_features=sparse_features,
            correlated_feature_pairs=correlated_pairs,
            target_type=target_type,
            target_balance=target_balance,
            target_missing=target_missing
        )
        
        self.data_characteristics = characteristics
        print(f"✅ Data analysis complete: {n_rows} rows, {n_features} features")
        return characteristics
    
    def generate_recommendations(self) -> List[ProcessingRecommendation]:
        """
        Generate intelligent preprocessing recommendations based on data analysis.
        
        Returns:
            List of ProcessingRecommendation objects
        """
        if self.data_characteristics is None:
            raise PreprocessingError("Must analyze data first using analyze_data()")
        
        print("🧠 Generating intelligent preprocessing recommendations...")
        recommendations = []
        
        # 1. DateTime processing (highest priority if datetime features exist)
        if self.data_characteristics.datetime_features:
            recommendations.append(self._recommend_datetime_processing())
        
        # 2. Missing value handling
        if self.data_characteristics.features_with_missing:
            recommendations.append(self._recommend_missing_value_handling())
        
        # 3. Outlier handling
        if self.data_characteristics.outlier_percentage > 5.0:
            recommendations.append(self._recommend_outlier_handling())
        
        # 4. Feature engineering
        if self._should_recommend_feature_engineering():
            recommendations.append(self._recommend_feature_engineering())
        
        # 5. Categorical encoding
        if self.data_characteristics.categorical_features:
            recommendations.append(self._recommend_categorical_encoding())
        
        # 6. Feature scaling
        if self.data_characteristics.numeric_features:
            recommendations.append(self._recommend_feature_scaling())
        
        # 7. Feature selection
        if self._should_recommend_feature_selection():
            recommendations.append(self._recommend_feature_selection())
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.priority)
        self.recommendations = recommendations
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        return recommendations
        
    def build_intelligent_pipeline(self) -> DataPipeline:
        """Build an optimized pipeline based on intelligent recommendations."""
        if not self.recommendations:
            self.generate_recommendations()
        
        print("🔧 Building intelligent pipeline...")
        
        # DEBUG: Print recommendations before sorting
        print("DEBUG - Recommendations before sorting:")
        for rec in self.recommendations:
            print(f"  {rec.step_name}: priority={rec.priority}")
        
        pipeline = DataPipeline()
        
        for rec in self.recommendations:
            if rec.confidence >= 0.7:
                processor_class = self._get_processor_class(rec.processor_class)
                processor = processor_class(**rec.parameters)
                pipeline.add_step(rec.step_name, processor)
                print(f"  ✅ Added {rec.step_name}: {rec.reasoning}")
            else:
                print(f"  ⚠️  Skipped {rec.step_name} (low confidence: {rec.confidence:.2f})")
        
        print(f"🚀 Intelligent pipeline built with {len(pipeline)} steps")
        return pipeline
    def explain_recommendations(self) -> str:
        """
        Generate detailed explanation of why specific steps were recommended.
        
        Returns:
            Detailed explanation string
        """
        if not self.recommendations:
            return "No recommendations generated yet. Run generate_recommendations() first."
        
        explanation = "🧠 INTELLIGENT PIPELINE RECOMMENDATIONS\n"
        explanation += "=" * 50 + "\n\n"
        
        explanation += f"📊 DATASET ANALYSIS:\n"
        explanation += f"  • Size: {self.data_characteristics.n_rows:,} rows × {self.data_characteristics.n_features} features\n"
        explanation += f"  • Memory: {self.data_characteristics.memory_usage_mb:.1f} MB\n"
        explanation += f"  • Missing data: {self.data_characteristics.missing_percentage:.1f}%\n"
        explanation += f"  • Outliers: {self.data_characteristics.outlier_percentage:.1f}%\n"
        explanation += f"  • Target type: {self.data_characteristics.target_type or 'Unknown'}\n\n"
        
        explanation += f"🔧 RECOMMENDED PREPROCESSING STEPS:\n"
        for i, rec in enumerate(self.recommendations, 1):
            confidence_emoji = "🟢" if rec.confidence >= 0.8 else "🟡" if rec.confidence >= 0.6 else "🔴"
            explanation += f"\n{i}. {rec.step_name.upper()} {confidence_emoji}\n"
            explanation += f"   Processor: {rec.processor_class}\n"
            explanation += f"   Confidence: {rec.confidence:.1%}\n"
            explanation += f"   Reasoning: {rec.reasoning}\n"
            explanation += f"   Parameters: {rec.parameters}\n"
        
        return explanation
    
    # Helper methods for data analysis
    
    def _analyze_missing_pattern(self, df: pd.DataFrame) -> str:
        """Analyze the pattern of missing values."""
        missing_counts = df.isnull().sum()
        if missing_counts.sum() == 0:
            return 'none'
        
        # Check if missing values are concentrated in few columns
        features_with_missing = missing_counts[missing_counts > 0]
        if len(features_with_missing) / len(df.columns) < 0.3:
            return 'clustered'
        
        # Check if missing values follow a pattern (e.g., all missing in same rows)
        missing_mask = df.isnull()
        if missing_mask.sum(axis=1).std() > missing_mask.sum(axis=1).mean():
            return 'systematic'
        
        return 'random'
    
    def _detect_datetime_features(self, df: pd.DataFrame) -> List[str]:
        """Detect datetime features in the dataset."""
        datetime_features = []
        
        # Check existing datetime columns
        datetime_features.extend(df.select_dtypes(include=['datetime64']).columns.tolist())
        
        # Try to parse object columns as datetime
        for col in df.select_dtypes(include=['object']).columns:
            if col in datetime_features:
                continue
            
            sample = df[col].dropna().head(100)
            if len(sample) == 0:
                continue
                
            try:
                pd.to_datetime(sample, errors='raise')
                datetime_features.append(col)
            except:
                # Check for common date patterns
                date_indicators = ['date', 'time', 'created', 'updated', 'timestamp']
                if any(indicator in col.lower() for indicator in date_indicators):
                    try:
                        pd.to_datetime(sample, errors='coerce', infer_datetime_format=True)
                        if not pd.to_datetime(sample, errors='coerce').isna().all():
                            datetime_features.append(col)
                    except:
                        pass
        
        return datetime_features
    
    def _detect_text_features(self, df: pd.DataFrame) -> List[str]:
        """Detect text features that might need special processing."""
        text_features = []
        
        for col in df.select_dtypes(include=['object']).columns:
            if col in self._detect_datetime_features(df):
                continue
            
            sample = df[col].dropna().head(100)
            if len(sample) == 0:
                continue
            
            # Check average string length
            avg_length = sample.astype(str).str.len().mean()
            if avg_length > 50:  # Likely text if average length > 50 characters
                text_features.append(col)
            
            # Check for common text indicators
            text_indicators = ['description', 'comment', 'review', 'text', 'content']
            if any(indicator in col.lower() for indicator in text_indicators):
                text_features.append(col)
        
        return text_features
    
    def _calculate_outlier_percentage(self, df: pd.DataFrame) -> float:
        """Calculate percentage of outliers using IQR method."""
        if df.empty:
            return 0.0
        
        outlier_count = 0
        total_values = 0
        
        for col in df.columns:
            data = df[col].dropna()
            if len(data) == 0:
                continue
            
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            outliers = ((data < Q1 - 1.5 * IQR) | (data > Q3 + 1.5 * IQR)).sum()
            outlier_count += outliers
            total_values += len(data)
        
        return (outlier_count / total_values * 100) if total_values > 0 else 0.0
    
    def _detect_high_cardinality_categorical(self, df: pd.DataFrame) -> List[str]:
        """Detect categorical features with high cardinality."""
        high_card_features = []
        
        for col in df.select_dtypes(include=['object', 'category']).columns:
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio > 0.7 or df[col].nunique() > 50:
                high_card_features.append(col)
        
        return high_card_features
    
    def _detect_skewed_features(self, df: pd.DataFrame) -> List[str]:
        """Detect heavily skewed numerical features."""
        skewed_features = []
        
        for col in df.columns:
            try:
                skewness = df[col].skew()
                if abs(skewness) > 1.0:  # Highly skewed
                    skewed_features.append(col)
            except:
                pass
        
        return skewed_features
    
    def _detect_sparse_features(self, df: pd.DataFrame) -> List[str]:
        """Detect sparse features (mostly zeros)."""
        sparse_features = []
        
        for col in df.columns:
            zero_ratio = (df[col] == 0).sum() / len(df)
            if zero_ratio > 0.9:
                sparse_features.append(col)
        
        return sparse_features
    
    def _detect_correlated_features(self, df: pd.DataFrame, threshold: float = 0.95) -> List[Tuple[str, str, float]]:
        """Detect highly correlated feature pairs."""
        if df.empty or len(df.columns) < 2:
            return []
        
        corr_matrix = df.corr().abs()
        correlated_pairs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] >= threshold:
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    correlated_pairs.append((col1, col2, corr_matrix.iloc[i, j]))
        
        return correlated_pairs
    
    def _analyze_target_type(self, target: pd.Series) -> str:
        """Analyze target variable type."""
        target_clean = target.dropna()
        
        if target_clean.dtype in ['object', 'category']:
            unique_values = target_clean.nunique()
            if unique_values == 2:
                return 'binary'
            elif unique_values <= 20:
                return 'multiclass'
            else:
                return 'text'
        elif np.issubdtype(target_clean.dtype, np.integer):
            unique_values = target_clean.nunique()
            if unique_values == 2:
                return 'binary'
            elif unique_values <= 20 and target_clean.min() >= 0:
                return 'multiclass'
            else:
                return 'continuous'
        else:
            return 'continuous'
    
    def _calculate_target_balance(self, target: pd.Series) -> Dict[str, float]:
        """Calculate target class balance."""
        value_counts = target.value_counts()
        total = value_counts.sum()
        return {str(k): v / total for k, v in value_counts.items()}
    
    # Recommendation methods
    
    def _recommend_datetime_processing(self) -> ProcessingRecommendation:
        """Recommend datetime processing configuration."""
        return ProcessingRecommendation(
            step_name='datetime_processing',
            processor_class='DateTimeProcessor',
            parameters={
                'datetime_columns': self.data_characteristics.datetime_features,
                'extract_components': True,
                'extract_cyclical': True,
                'drop_original': True
            },
            reasoning=f"Found {len(self.data_characteristics.datetime_features)} datetime features that need temporal feature extraction",
            confidence=0.95,
            priority=1
        )
    
    def _recommend_missing_value_handling(self) -> ProcessingRecommendation:
        """Recommend missing value handling strategy."""
        missing_pct = self.data_characteristics.missing_percentage
        pattern = self.data_characteristics.missing_pattern
        
        # Choose strategy based on missing data characteristics
        if missing_pct < 5:
            numeric_strategy = 'median'
            confidence = 0.9
        elif missing_pct < 15 and pattern == 'random':
            numeric_strategy = 'knn'
            confidence = 0.85
        else:
            numeric_strategy = 'median'
            confidence = 0.75
        
        return ProcessingRecommendation(
            step_name='missing_value_handling',
            processor_class='MissingValueHandler',
            parameters={
                'numeric_strategy': numeric_strategy,
                'categorical_strategy': 'most_frequent',
                'n_neighbors': 5 if numeric_strategy == 'knn' else None
            },
            reasoning=f"Missing data: {missing_pct:.1f}% with {pattern} pattern. {numeric_strategy.upper()} imputation recommended.",
            confidence=confidence,
            priority=3
        )
    
    def _recommend_outlier_handling(self) -> ProcessingRecommendation:
        """Recommend outlier handling strategy."""
        outlier_pct = self.data_characteristics.outlier_percentage
        
        if outlier_pct > 20:
            method = 'iqr'
            treatment = 'cap'
            confidence = 0.8
        elif outlier_pct > 10:
            method = 'iqr'
            treatment = 'cap'
            confidence = 0.85
        else:
            method = 'iqr'
            treatment = 'cap'
            confidence = 0.9
        
        return ProcessingRecommendation(
            step_name='outlier_handling',
            processor_class='OutlierHandler',
            parameters={
                'method': method,
                'treatment': treatment,
                'threshold': 1.5
            },
            reasoning=f"High outlier percentage ({outlier_pct:.1f}%) detected. IQR capping recommended.",
            confidence=confidence,
            priority=1
        )
    
    def _recommend_feature_engineering(self) -> ProcessingRecommendation:
        """Recommend feature engineering steps."""
        skewed_count = len(self.data_characteristics.skewed_features)
        
        log_transform = skewed_count > 0
        confidence = 0.8 if skewed_count > 2 else 0.6
        
        return ProcessingRecommendation(
            step_name='feature_engineering',
            processor_class='FeatureEngineering',
            parameters={
                'log_transform': log_transform,
                'sqrt_transform': skewed_count > 0,
                'polynomial_degree': 2 if self.data_characteristics.n_features < 20 else 1
            },
            reasoning=f"Found {skewed_count} skewed features. Log/sqrt transforms recommended.",
            confidence=confidence,
            priority=2
        )
    
    def _recommend_categorical_encoding(self) -> ProcessingRecommendation:
        """Recommend categorical encoding strategy."""
        n_categorical = len(self.data_characteristics.categorical_features)
        high_cardinality = len(self.data_characteristics.high_cardinality_cats)
        
        if high_cardinality > 0:
            method = 'label'  # Label encoding for high cardinality
            confidence = 0.8
            reasoning = f"High cardinality categorical features detected. Label encoding recommended."
        elif n_categorical <= 10:
            method = 'onehot'
            confidence = 0.9
            reasoning = f"Low-cardinality categorical features. One-hot encoding recommended."
        else:
            method = 'label'
            confidence = 0.7
            reasoning = f"Many categorical features. Label encoding to prevent dimensionality explosion."
        
        return ProcessingRecommendation(
            step_name='categorical_encoding',
            processor_class='CategoricalEncoder',
            parameters={
                'method': method,
                'handle_unknown': 'ignore',
                'max_categories': 50
            },
            reasoning=reasoning,
            confidence=confidence,
            priority=5
        )
    
    def _recommend_feature_scaling(self) -> ProcessingRecommendation:
        """Recommend feature scaling method."""
        outlier_pct = self.data_characteristics.outlier_percentage
        skewed_count = len(self.data_characteristics.skewed_features)
        
        if outlier_pct > 10 or skewed_count > 3:
            method = 'robust'
            confidence = 0.9
            reasoning = "Outliers and skewed features detected. Robust scaling recommended."
        else:
            method = 'standard'
            confidence = 0.85
            reasoning = "Clean numerical data. Standard scaling recommended."
        
        return ProcessingRecommendation(
            step_name='feature_scaling',
            processor_class='FeatureScaler',
            parameters={'method': method},
            reasoning=reasoning,
            confidence=confidence,
            priority=6
        )
    
    def _recommend_feature_selection(self) -> ProcessingRecommendation:
        """Recommend feature selection if needed."""
        n_features = self.data_characteristics.n_features
        correlated_pairs = len(self.data_characteristics.correlated_feature_pairs)
        
        if n_features > 100:
            k = min(50, n_features // 2)
            confidence = 0.8
        elif correlated_pairs > 5:
            k = n_features - correlated_pairs
            confidence = 0.7
        else:
            k = min(20, n_features)
            confidence = 0.6
        
        return ProcessingRecommendation(
            step_name='feature_selection',
            processor_class='FeatureSelector',
            parameters={
                'method': 'mutual_info',
                'k': k
            },
            reasoning=f"High dimensionality ({n_features} features) or correlation detected. Feature selection recommended.",
            confidence=confidence,
            priority=7
        )
    
    def _should_recommend_feature_engineering(self) -> bool:
        """Determine if feature engineering should be recommended."""
        return (len(self.data_characteristics.skewed_features) > 0 or 
                self.data_characteristics.n_features < 50)
    
    def _should_recommend_feature_selection(self) -> bool:
        """Determine if feature selection should be recommended."""
        return (self.data_characteristics.n_features > 20 or 
                len(self.data_characteristics.correlated_feature_pairs) > 3)
    
    def _get_processor_class(self, class_name: str):
        """Get processor class by name."""
        class_map = {
            'MissingValueHandler': MissingValueHandler,
            'FeatureScaler': FeatureScaler,
            'CategoricalEncoder': CategoricalEncoder,
            'OutlierHandler': OutlierHandler,
            'DateTimeProcessor': DateTimeProcessor,
            'FeatureEngineering': FeatureEngineering,
            'FeatureSelector': FeatureSelector
        }
        return class_map[class_name]


# Convenience function for easy usage
def create_intelligent_pipeline(df: pd.DataFrame, target_column: Optional[str] = None) -> DataPipeline:
    """
    Create an intelligent pipeline with automatic preprocessing step selection.
    
    Args:
        df: Input DataFrame
        target_column: Name of target column (optional)
        
    Returns:
        Optimized DataPipeline
    """
    selector = IntelligentPipelineSelector(target_column=target_column)
    selector.analyze_data(df)
    pipeline = selector.build_intelligent_pipeline()
    
    print(selector.explain_recommendations())
    
    return pipeline