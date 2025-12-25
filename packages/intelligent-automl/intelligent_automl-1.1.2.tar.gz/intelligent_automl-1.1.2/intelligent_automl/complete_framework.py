# intelligent_automl/complete_framework.py

"""
Complete Intelligent AutoML Framework with Multi-Metric Evaluation

This is the main orchestrator that combines all components of the framework
to provide a complete, production-ready automated machine learning solution
with comprehensive multi-metric evaluation and analysis.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional, Union
import time
import os
import warnings
from pathlib import Path

# Core framework components
from .data.loaders import load_data
from .data.pipeline import DataPipeline
from .intelligence.pipeline_selector import create_intelligent_pipeline
from .core.exceptions import AutoMLError, DataLoadError, PreprocessingError, ModelTrainingError
from .utils.logging import FrameworkLogger

# Enhanced components with multi-metric support
from .models.auto_trainer import EnhancedAutoModelTrainer
from .core.config import AutoMLConfig, EvaluationConfig, OptimizationConfig
from .evaluation.multi_metric_evaluator import MultiMetricEvaluator











def safe_json_serializer(obj):
    """Safe JSON serializer that handles numpy, pandas, and other problematic types."""
    import numpy as np
    import pandas as pd
    from datetime import datetime, date
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Timedelta):
        return str(obj)
    elif hasattr(obj, 'dtype') and hasattr(obj.dtype, 'name'):
        if 'int' in str(obj.dtype):
            return int(obj)
        elif 'float' in str(obj.dtype):
            return float(obj)
        else:
            return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif hasattr(obj, 'to_dict') and callable(obj.to_dict):
        try:
            return obj.to_dict()
        except:
            return str(obj)
    elif hasattr(obj, '__dict__'):
        return str(obj)
    elif isinstance(obj, set):
        return list(obj)
    else:
        return str(obj)



class IntelligentAutoMLFramework:
    """
    Complete Intelligent AutoML Framework with comprehensive multi-metric evaluation.
    
    This framework provides end-to-end automated machine learning capabilities
    including intelligent data analysis, automatic preprocessing pipeline selection,
    comprehensive multi-metric model evaluation, and production-ready deployment.
    
    Features:
    - Automatic data analysis and preprocessing
    - Intelligent pipeline selection
    - Comprehensive multi-metric evaluation
    - Multi-objective optimization with Pareto ranking
    - Production-ready model deployment
    - Detailed performance analysis and reporting
    """
    
    def __init__(self, verbose: bool = True, log_level: str = 'INFO'):
        """
        Initialize the Intelligent AutoML Framework.
        
        Args:
            verbose: Whether to print detailed progress information
            log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        """
        self.verbose = verbose
        self.log_level = log_level
        
        # Initialize logger
        self.logger = FrameworkLogger(log_level=log_level)
        
        # Framework state
        self.data: Optional[pd.DataFrame] = None
        self.target_column: Optional[str] = None
        self.processed_data: Optional[pd.DataFrame] = None
        self.pipeline: Optional[DataPipeline] = None
        self.model: Optional[Any] = None
        self.model_name: Optional[str] = None
        self.trainer: Optional[EnhancedAutoModelTrainer] = None
        
        # Results storage
        self.results: Dict[str, Any] = {}
        
        # Multi-metric evaluator
        self.metric_evaluator = MultiMetricEvaluator()
        
        if self.verbose:
            print("🧠 Intelligent AutoML Framework initialized!")
            print("🎯 Ready for comprehensive multi-metric evaluation!")
    
    def load_data(self, file_path: str, target_column: str) -> pd.DataFrame:
        """
        Load and validate data from file.
        
        Args:
            file_path: Path to data file
            target_column: Name of target column
            
        Returns:
            Loaded DataFrame
        """
        if self.verbose:
            print(f"\n📂 Loading data from {file_path}...")
        
        try:
            # Load data using intelligent loader
            self.data = load_data(file_path)
            self.target_column = target_column
            
            # Validate target column
            if target_column not in self.data.columns:
                raise DataLoadError(f"Target column '{target_column}' not found in data")
            
            # Basic validation
            if self.data.empty:
                raise DataLoadError("Loaded data is empty")
            
            if self.verbose:
                print(f"✅ Data loaded successfully!")
                print(f"📊 Shape: {self.data.shape[0]} rows × {self.data.shape[1]} columns")
                print(f"🎯 Target: {target_column}")
                print(f"💾 Memory usage: {self.data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            # Store basic info in results
            self.results['data_loading'] = {
                'file_path': file_path,
                'target_column': target_column,
                'shape': self.data.shape,
                'columns': list(self.data.columns),
                'dtypes': self.data.dtypes.to_dict(),
                'memory_usage_mb': self.data.memory_usage(deep=True).sum() / 1024**2
            }
            
            return self.data
            
        except Exception as e:
            self.logger.log_error('data_loading', 'load_data', e)
            raise DataLoadError(f"Failed to load data: {str(e)}") from e
    
    def analyze_data(self) -> Dict[str, Any]:
        """
        Analyze data characteristics and quality.
        
        Returns:
            Data analysis profile
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if self.verbose:
            print(f"\n🔍 Analyzing data characteristics...")
        
        try:
            # Basic analysis
            analysis = {
                'basic_info': {
                    'shape': self.data.shape,
                    'columns': list(self.data.columns),
                    'dtypes': self.data.dtypes.value_counts().to_dict()
                },
                'data_quality': {
                    'missing_values': self.data.isnull().sum().to_dict(),
                    'missing_percentage': (self.data.isnull().sum() / len(self.data) * 100).to_dict(),
                    'duplicate_rows': self.data.duplicated().sum(),
                    'completeness': (1 - self.data.isnull().sum().sum() / (self.data.shape[0] * self.data.shape[1])) * 100
                },
                'target_analysis': self._analyze_target(),
                'feature_analysis': self._analyze_features()
            }
            
            if self.verbose:
                print(f"✅ Analysis complete!")
                print(f"📊 Data quality: {analysis['data_quality']['completeness']:.1f}% complete")
                print(f"🎯 Target type: {analysis['target_analysis']['type']}")
                print(f"📈 Features: {len(analysis['feature_analysis']['numeric'])} numeric, {len(analysis['feature_analysis']['categorical'])} categorical")
            
            self.results['data_analysis'] = analysis
            return analysis
            
        except Exception as e:
            self.logger.log_error('data_analysis', 'analyze_data', e)
            raise
    
    def _analyze_target(self) -> Dict[str, Any]:
        """Analyze target variable characteristics."""
        if self.target_column is None:
            return {}
        
        target = self.data[self.target_column]
        
        # Determine target type
        unique_values = target.nunique()
        total_values = len(target)
        
        if unique_values <= 20 and unique_values / total_values < 0.05:
            target_type = 'classification'
        elif target.dtype in ['int64', 'int32'] and unique_values <= 50:
            target_type = 'classification'
        elif target.dtype in ['object', 'category']:
            target_type = 'classification'
        else:
            target_type = 'regression'
        
        analysis = {
            'type': target_type,
            'unique_values': unique_values,
            'missing_count': target.isnull().sum(),
            'missing_percentage': target.isnull().sum() / len(target) * 100
        }
        
        if target_type == 'classification':
            analysis['class_distribution'] = target.value_counts().to_dict()
            analysis['class_balance'] = target.value_counts(normalize=True).to_dict()
        else:
            analysis['statistics'] = {
                'mean': target.mean(),
                'std': target.std(),
                'min': target.min(),
                'max': target.max(),
                'median': target.median()
            }
        
        return analysis
    
    def _analyze_features(self) -> Dict[str, Any]:
        """Analyze feature characteristics."""
        features = self.data.drop(columns=[self.target_column])
        
        numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = features.select_dtypes(include=['object', 'category']).columns.tolist()
        
        analysis = {
            'numeric': numeric_features,
            'categorical': categorical_features,
            'total_features': len(features.columns),
            'feature_correlations': self._calculate_feature_correlations(features[numeric_features]) if numeric_features else {}
        }
        
        return analysis
    
    def _calculate_feature_correlations(self, numeric_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate feature correlations for numeric data."""
        if numeric_data.empty:
            return {}
        
        corr_matrix = numeric_data.corr()
        high_corr_pairs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.8:  # High correlation threshold
                    high_corr_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': corr_val
                    })
        
        return {
            'high_correlation_pairs': high_corr_pairs,
            'max_correlation': corr_matrix.abs().max().max(),
            'mean_correlation': corr_matrix.abs().mean().mean()
        }
    
    def create_pipeline(self) -> DataPipeline:
        """
        Create intelligent preprocessing pipeline.
        
        Returns:
            Configured DataPipeline
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if self.verbose:
            print(f"\n🧠 Creating intelligent preprocessing pipeline...")
        
        try:
            # Create intelligent pipeline
            self.pipeline = create_intelligent_pipeline(self.data, target_column=self.target_column)
            
            if self.verbose:
                print(f"✅ Pipeline created with {len(self.pipeline)} steps")
                print(f"🔧 Steps: {', '.join(self.pipeline.get_step_names())}")
            
            return self.pipeline
            
        except Exception as e:
            self.logger.log_error('pipeline_creation', 'create_pipeline', e)
            raise
    
    def preprocess_data(self) -> pd.DataFrame:
        """
        Preprocess data using intelligent pipeline.
        
        Returns:
            Preprocessed DataFrame
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if self.verbose:
            print(f"\n⚙️ Preprocessing data with intelligent pipeline...")
        
        try:
            # Create pipeline if not exists
            if self.pipeline is None:
                self.create_pipeline()
            
            start_time = time.time()
            
            # Separate features and target
            features = self.data.drop(columns=[self.target_column])
            target = self.data[self.target_column]
            
            # Apply preprocessing pipeline
            processed_features = self.pipeline.fit_transform(features)
            
            # Combine processed features with target
            self.processed_data = processed_features.copy()
            self.processed_data[self.target_column] = target.values
            
            processing_time = time.time() - start_time
            
            if self.verbose:
                print(f"✅ Preprocessing complete!")
                print(f"📊 Features: {features.shape[1]} → {processed_features.shape[1]}")
                print(f"🕒 Processing time: {processing_time:.2f}s")
                print(f"🎯 Data quality: {(1 - self.processed_data.isnull().sum().sum() / (self.processed_data.shape[0] * self.processed_data.shape[1])) * 100:.1f}% complete")
            
            # Store preprocessing results
            self.results['preprocessing'] = {
                'original_features': features.shape[1],
                'final_features': processed_features.shape[1],
                'processing_time': processing_time,
                'pipeline_steps': self.pipeline.get_step_names(),
                'data_quality_improvement': {
                    'missing_before': self.data.isnull().sum().sum(),
                    'missing_after': self.processed_data.isnull().sum().sum()
                }
            }
            
            return self.processed_data
            
        except Exception as e:
            self.logger.log_error('preprocessing', 'preprocess_data', e)
            raise PreprocessingError(f"Preprocessing failed: {str(e)}") from e
    
    def _detect_task_type(self, y: pd.Series) -> str:
        """Auto-detect task type from target variable."""
        unique_values = y.nunique()
        total_values = len(y)
        
        # Heuristics for task detection
        if unique_values <= 20 and unique_values / total_values < 0.05:
            return 'classification'
        elif y.dtype in ['int64', 'int32'] and unique_values <= 50:
            return 'classification'
        elif y.dtype in ['object', 'category']:
            return 'classification'
        else:
            return 'regression'
    
    def train_models(self, **kwargs) -> EnhancedAutoModelTrainer:
        """
        Enhanced model training with comprehensive multi-metric evaluation.
        
        Args:
            **kwargs: Training configuration options including:
                - models_to_try: List of model names to train
                - multi_objective: Enable multi-objective optimization
                - optimization_metrics: List of metrics for optimization
                - metric_weights: Weights for multi-objective optimization
                - n_trials: Number of optimization trials
                - cv_folds: Cross-validation folds
                - time_limit_minutes: Training time limit
        
        Returns:
            Trained EnhancedAutoModelTrainer instance
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Call preprocess_data() first.")
        
        if self.verbose:
            print(f"\n🤖 Training models with comprehensive evaluation...")
        
        try:
            # Determine task type
            y = self.data[self.target_column]
            task_type = self._detect_task_type(y)
            
            # Configure comprehensive evaluation
            eval_config = EvaluationConfig(
                enable_comprehensive_metrics=True,
                enable_probabilistic_metrics=True if task_type == 'classification' else False,
                cross_validation=True,
                cv_folds=kwargs.get('cv_folds', 5),
                save_predictions=True,
                save_feature_importance=True,
                save_confusion_matrix=True if task_type == 'classification' else False,
                save_residual_plots=True if task_type == 'regression' else False
            )
            
            # Configure optimization
            multi_objective = kwargs.get('multi_objective', False)
            optimization_metrics = kwargs.get('optimization_metrics', [])
            
            if multi_objective and not optimization_metrics:
                # Set default multi-objective metrics based on task
                if task_type == 'classification':
                    optimization_metrics = ['f1_weighted', 'precision_weighted', 'accuracy']
                else:
                    optimization_metrics = ['r2', 'mae', 'rmse']
            
            opt_config = OptimizationConfig(
                enabled=True,
                method='optuna',
                n_trials=kwargs.get('n_trials', 50),
                multi_objective=multi_objective,
                optimization_metrics=optimization_metrics,
                metric_weights=kwargs.get('metric_weights', {})
            )
            
            # Create comprehensive config
            config = AutoMLConfig(
                data=None,
                model=None,
                training=None,
                evaluation=eval_config,
                optimization=opt_config,
                task_type=task_type,
                verbose=self.verbose
            )
            
            # Initialize enhanced trainer
            models_to_try = kwargs.get('models_to_try', ['random_forest', 'logistic_regression', 'svm'])
            trainer = EnhancedAutoModelTrainer(
                config=config,
                models=models_to_try,
                verbose=self.verbose,
                random_state=42
            )
            
            # Prepare features and target
            features = self.processed_data.drop(columns=[self.target_column])
            target = self.processed_data[self.target_column]
            
            if self.verbose:
                print(f"📊 Task Type: {task_type}")
                print(f"📈 Models: {models_to_try}")
                print(f"🎯 Evaluation Metrics: {eval_config.get_metric_names()}")
                if multi_objective:
                    print(f"🎯 Multi-Objective Metrics: {optimization_metrics}")
            
            # Train with comprehensive evaluation
            trainer.fit(features, target)
            
            # Store results
            self.model = trainer.best_model
            self.model_name = trainer.best_model_name
            self.trainer = trainer  # Store for detailed analysis
            
            # Get comprehensive results
            training_summary = trainer.get_training_summary()
            model_comparison = trainer.get_model_comparison()
            
            # Store comprehensive results
            self.results['model_training'] = {
                'task_type': task_type,
                'best_model': trainer.best_model_name,
                'best_score': training_summary['best_score'],
                'models_trained': training_summary['models_trained'],
                'total_training_time': training_summary['total_training_time'],
                'metrics_evaluated': training_summary['metrics_evaluated'],
                'model_performances': training_summary['model_performances'],
                'comprehensive_comparison': model_comparison.to_dict('records'),
                'optimization_type': training_summary.get('optimization_type', 'single_objective')
            }
            
            # Add multi-objective info if applicable
            if training_summary.get('optimization_type') == 'multi_objective':
                self.results['model_training']['pareto_front_size'] = training_summary.get('pareto_front_size', 0)
                self.results['model_training']['optimization_metrics'] = training_summary.get('optimization_metrics', [])
            
            if self.verbose:
                print(f"✅ Training complete!")
                print(f"🏆 Best model: {trainer.best_model_name}")
                print(f"📊 Best score: {training_summary['best_score']:.4f}")
                print(f"📈 Models trained: {training_summary['models_trained']}")
                print(f"🎯 Metrics evaluated: {len(training_summary['metrics_evaluated'])}")
                
                # Show top metrics for best model
                best_performance = trainer.model_performances[trainer.best_model_name]
                print(f"\n🔍 Top metrics for {trainer.best_model_name}:")
                for metric in best_performance.val_metrics.get_best_metrics(5):
                    direction = "↗" if metric.higher_is_better else "↘"
                    print(f"  • {metric.name}: {metric.value:.4f} {direction}")
            
            return trainer
            
        except Exception as e:
            self.logger.log_error('model_training', 'train_models', e)
            raise ModelTrainingError(f"Model training failed: {str(e)}") from e
    
    def make_predictions(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.
        
        Args:
            X: Input features DataFrame
            
        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("No trained model available. Run complete pipeline first.")
        
        if self.pipeline is None:
            raise ValueError("No preprocessing pipeline available. Run complete pipeline first.")
        
        try:
            # Apply preprocessing pipeline
            processed_X = self.pipeline.transform(X)
            
            # Make predictions
            predictions = self.model.predict(processed_X)
            
            if self.verbose:
                print(f"🔮 Generated {len(predictions)} predictions")
            
            return predictions
            
        except Exception as e:
            self.logger.log_error('prediction', 'make_predictions', e)
            raise
    
    def get_prediction_probabilities(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities for classification tasks.
        
        Args:
            X: Input features DataFrame
            
        Returns:
            Prediction probabilities array
        """
        if self.model is None:
            raise ValueError("No trained model available. Run complete pipeline first.")
        
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError("Current model does not support probability predictions")
        
        try:
            # Apply preprocessing pipeline
            processed_X = self.pipeline.transform(X)
            
            # Get probabilities
            probabilities = self.model.predict_proba(processed_X)
            
            if self.verbose:
                print(f"🎯 Generated probability predictions for {len(probabilities)} samples")
            
            return probabilities
            
        except Exception as e:
            self.logger.log_error('prediction', 'get_prediction_probabilities', e)
            raise
    
    def get_model_comparison_report(self) -> Dict[str, Any]:
        """
        Get detailed model comparison with all metrics.
        
        Returns:
            Comprehensive model comparison report
        """
        if not hasattr(self, 'trainer') or not self.trainer:
            raise ValueError("No trainer available. Run complete pipeline first.")
        
        comparison_df = self.trainer.get_model_comparison()
        
        # Create structured report
        report = {
            'models_compared': len(comparison_df),
            'best_model': self.trainer.best_model_name,
            'comparison_table': comparison_df.to_dict('records'),
            'metrics_evaluated': list(comparison_df.columns),
            'rankings': {
                'by_primary_score': comparison_df.nlargest(5, 'primary_score')[['model', 'primary_score']].to_dict('records'),
                'fastest_training': comparison_df.nsmallest(3, 'training_time')[['model', 'training_time']].to_dict('records'),
                'most_memory_efficient': comparison_df.nsmallest(3, 'memory_usage')[['model', 'memory_usage']].to_dict('records')
            }
        }
        
        return report
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Enhanced comprehensive report with multi-metric analysis.
        
        Returns:
            Complete framework analysis report
        """
        if not self.results:
            raise ValueError("No results available. Run the complete pipeline first.")
        
        # Get basic report structure
        report = {
            'framework_info': {
                'version': '1.0.0',
                'evaluation_system': 'comprehensive_multi_metric',
                'components': ['data_loading', 'preprocessing', 'model_training', 'prediction'],
                'intelligent_features': [
                    'automatic_data_analysis',
                    'intelligent_pipeline_selection',
                    'smart_preprocessing',
                    'comprehensive_multi_metric_evaluation',
                    'multi_objective_optimization'
                ]
            },
            'data_info': {
                'shape': self.data.shape if self.data is not None else None,
                'target_column': self.target_column,
                'memory_usage_mb': self.data.memory_usage(deep=True).sum() / 1024**2 if self.data is not None else None
            },
            'results': self.results,
            'performance_summary': {
                'preprocessing_time': self.results.get('preprocessing', {}).get('processing_time', 0),
                'training_time': self.results.get('model_training', {}).get('total_training_time', 0),
                'best_score': self.results.get('model_training', {}).get('best_score', 0),
                'feature_expansion': self.results.get('preprocessing', {}).get('final_features', 0) / max(self.results.get('preprocessing', {}).get('original_features', 1), 1)
            }
        }
        
        # Add comprehensive multi-metric analysis
        if hasattr(self, 'trainer') and self.trainer:
            multi_metric_analysis = self._get_multi_metric_analysis()
            report['multi_metric_analysis'] = multi_metric_analysis
        
        return report
    
    def _get_multi_metric_analysis(self) -> Dict[str, Any]:
        """Generate detailed multi-metric analysis."""
        if not hasattr(self, 'trainer') or not self.trainer:
            return {}
        
        analysis = {
            'evaluation_type': 'comprehensive_multi_metric',
            'models_compared': len(self.trainer.model_performances),
            'metrics_per_model': {},
            'best_model_details': {},
            'model_rankings': {}
        }
        
        # Detailed metrics for each model
        for model_name, performance in self.trainer.model_performances.items():
            analysis['metrics_per_model'][model_name] = {
                'primary_score': performance.get_primary_score(),
                'all_metrics': {name: metric.value for name, metric in performance.val_metrics.all_metrics.items()},
                'training_time': performance.training_time,
                'memory_usage': performance.memory_usage,
                'pareto_rank': performance.pareto_rank,
                'composite_score': performance.composite_score
            }
        
        # Best model detailed analysis
        best_model_name = self.trainer.best_model_name
        best_performance = self.trainer.model_performances[best_model_name]
        
        analysis['best_model_details'] = {
            'name': best_model_name,
            'primary_metric': best_performance.val_metrics.primary_metric,
            'primary_score': best_performance.get_primary_score(),
            'top_5_metrics': [
                {
                    'name': metric.name,
                    'value': metric.value,
                    'higher_is_better': metric.higher_is_better,
                    'category': metric.category
                }
                for metric in best_performance.val_metrics.get_best_metrics(5)
            ],
            'feature_importance': best_performance.feature_importance,
            'cross_validation_available': best_performance.cv_metrics is not None
        }
        
        # Model rankings
        comparison_df = self.trainer.get_model_comparison()
        analysis['model_rankings'] = {
            'by_primary_score': comparison_df.nlargest(5, 'primary_score')[['model', 'primary_score']].to_dict('records'),
            'by_training_time': comparison_df.nsmallest(3, 'training_time')[['model', 'training_time']].to_dict('records'),
            'by_memory_usage': comparison_df.nsmallest(3, 'memory_usage')[['model', 'memory_usage']].to_dict('records')
        }
        
        return analysis
    
    def save_model(self, output_dir: str, model_name: Optional[str] = None):
        """Save trained model and pipeline to directory."""
        if self.model is None:
            raise ValueError("No trained model available. Run complete pipeline first.")
        
        try:
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Save model using trainer
            if hasattr(self, 'trainer') and self.trainer:
                try:
                    model_path = os.path.join(output_dir, 'best_model.joblib')
                    self.trainer.save_model(model_path, model_name)
                    if self.verbose:
                        print(f"✅ Model saved: {model_path}")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️ Could not save model: {str(e)}")
            
            # Save pipeline
            if self.pipeline:
                try:
                    pipeline_path = os.path.join(output_dir, 'preprocessing_pipeline.joblib')
                    self.pipeline.save(pipeline_path)
                    if self.verbose:
                        print(f"✅ Pipeline saved: {pipeline_path}")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️ Could not save pipeline: {str(e)}")
            
            # Save comprehensive report
            try:
                report = self.get_comprehensive_report()
                
                # Try simplified JSON first (without complex nested objects)
                try:
                    simplified_report = self._create_simplified_report()
                    report_path = os.path.join(output_dir, 'results_summary.json')
                    with open(report_path, 'w', encoding='utf-8') as f:
                        json.dump(simplified_report, f, indent=2, ensure_ascii=False, default=str)
                    if self.verbose:
                        print(f"✅ Results summary saved: {report_path}")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️ Could not save JSON summary: {str(e)}")
            
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Could not generate report: {str(e)}")
            
            # Save detailed text summary (without emojis to avoid encoding issues)
            try:
                summary_path = os.path.join(output_dir, 'summary.txt')
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write("INTELLIGENT AUTOML RESULTS SUMMARY\n")
                    f.write("=" * 50 + "\n\n")
                    
                    if hasattr(self, 'trainer') and self.trainer:
                        f.write(f"Best Model: {self.trainer.best_model_name}\n")
                        best_perf = self.trainer.model_performances[self.trainer.best_model_name]
                        f.write(f"Best Score: {best_perf.get_primary_score():.4f}\n")
                        f.write(f"Task Type: {self.trainer.task_type}\n")
                        f.write(f"Models Trained: {len(self.trainer.model_performances)}\n\n")
                        
                        f.write("All Model Scores:\n")
                        for name, perf in self.trainer.model_performances.items():
                            f.write(f"  - {name}: {perf.get_primary_score():.4f}\n")
                        
                        f.write(f"\nTop Metrics for {self.trainer.best_model_name}:\n")
                        for metric in best_perf.val_metrics.get_best_metrics(10):
                            direction = "higher_better" if metric.higher_is_better else "lower_better"
                            f.write(f"  - {metric.name}: {metric.value:.4f} ({direction})\n")
                        
                        # Add training details
                        f.write(f"\nTraining Details:\n")
                        f.write(f"  - Training time: {best_perf.training_time:.2f} seconds\n")
                        f.write(f"  - Memory usage: {best_perf.memory_usage:.2f} MB\n")
                        
                        # Add data details
                        if hasattr(self, 'results') and 'data_loading' in self.results:
                            data_info = self.results['data_loading']
                            f.write(f"\nData Information:\n")
                            f.write(f"  - Original shape: {data_info['shape']}\n")
                            f.write(f"  - Target column: {data_info['target_column']}\n")
                            f.write(f"  - Memory usage: {data_info['memory_usage_mb']:.2f} MB\n")
                        
                        if hasattr(self, 'results') and 'preprocessing' in self.results:
                            prep_info = self.results['preprocessing']
                            f.write(f"\nPreprocessing Results:\n")
                            f.write(f"  - Features before: {prep_info['original_features']}\n")
                            f.write(f"  - Features after: {prep_info['final_features']}\n")
                            f.write(f"  - Processing time: {prep_info['processing_time']:.2f} seconds\n")
                            f.write(f"  - Pipeline steps: {', '.join(prep_info['pipeline_steps'])}\n")
                
                if self.verbose:
                    print(f"✅ Summary saved: {summary_path}")
                    
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Could not save summary: {str(e)}")
            
            # Save model comparison CSV
            try:
                if hasattr(self, 'trainer') and self.trainer:
                    comparison_df = self.trainer.get_model_comparison()
                    csv_path = os.path.join(output_dir, 'model_comparison.csv')
                    comparison_df.to_csv(csv_path, index=False)
                    if self.verbose:
                        print(f"✅ Model comparison saved: {csv_path}")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Could not save model comparison: {str(e)}")
            
            if self.verbose:
                print(f"\n💾 Results saved to: {output_dir}")
                
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error in save_model: {str(e)}")


    def _create_simplified_report(self):
        """Create a simplified report that's easy to serialize."""
        from datetime import datetime
        
        simplified = {
            "framework_version": "1.0.0",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task_completed": True
        }
        
        try:
            if hasattr(self, 'trainer') and self.trainer:
                simplified["model_results"] = {
                    "best_model": str(self.trainer.best_model_name),
                    "best_score": float(self.trainer.model_performances[self.trainer.best_model_name].get_primary_score()),
                    "task_type": str(self.trainer.task_type),
                    "models_trained": int(len(self.trainer.model_performances)),
                    "total_training_time": float(sum(p.training_time for p in self.trainer.model_performances.values()))
                }
                
                # Add all model scores
                simplified["all_model_scores"] = {}
                for name, perf in self.trainer.model_performances.items():
                    simplified["all_model_scores"][str(name)] = float(perf.get_primary_score())
                
                # Add best model metrics (simplified)
                best_perf = self.trainer.model_performances[self.trainer.best_model_name]
                simplified["best_model_metrics"] = {}
                for metric_name, metric in best_perf.val_metrics.all_metrics.items():
                    simplified["best_model_metrics"][str(metric_name)] = {
                        "value": float(metric.value),
                        "higher_is_better": bool(metric.higher_is_better),
                        "category": str(metric.category)
                    }
        except Exception as e:
            simplified["model_results_error"] = str(e)
        
        try:
            if hasattr(self, 'results'):
                if 'data_loading' in self.results:
                    data_info = self.results['data_loading']
                    simplified["data_info"] = {
                        "rows": int(data_info['shape'][0]),
                        "columns": int(data_info['shape'][1]),
                        "target_column": str(data_info['target_column']),
                        "memory_usage_mb": float(data_info['memory_usage_mb'])
                    }
                
                if 'preprocessing' in self.results:
                    prep_info = self.results['preprocessing']
                    simplified["preprocessing_info"] = {
                        "original_features": int(prep_info['original_features']),
                        "final_features": int(prep_info['final_features']),
                        "processing_time": float(prep_info['processing_time']),
                        "pipeline_steps": [str(step) for step in prep_info['pipeline_steps']]
                    }
        except Exception as e:
            simplified["data_info_error"] = str(e)
        
        return simplified




    def _clean_report_for_json(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Clean report data to make it JSON serializable."""
        import copy
        
        # Make a deep copy to avoid modifying original
        cleaned = copy.deepcopy(report)
        
        # Clean problematic nested data
        if 'results' in cleaned and 'data_loading' in cleaned['results']:
            data_loading = cleaned['results']['data_loading']
            
            # Convert dtypes dict to strings
            if 'dtypes' in data_loading:
                cleaned_dtypes = {}
                for col, dtype in data_loading['dtypes'].items():
                    cleaned_dtypes[str(col)] = str(dtype)
                data_loading['dtypes'] = cleaned_dtypes
        
        # Clean multi_metric_analysis if present
        if 'multi_metric_analysis' in cleaned:
            analysis = cleaned['multi_metric_analysis']
            
            # Clean metrics_per_model
            if 'metrics_per_model' in analysis:
                for model_name, model_data in analysis['metrics_per_model'].items():
                    if 'all_metrics' in model_data:
                        # Convert all metric values to native Python types
                        cleaned_metrics = {}
                        for metric_name, value in model_data['all_metrics'].items():
                            cleaned_metrics[str(metric_name)] = float(value) if value is not None else None
                        model_data['all_metrics'] = cleaned_metrics
        
        return cleaned
 
    def load_model(self, model_dir: str):
        """
        Load trained model and pipeline from directory.
        
        Args:
            model_dir: Directory containing saved model
        """
        try:
            # Load model
            model_path = os.path.join(model_dir, 'best_model.joblib')
            if os.path.exists(model_path):
                if hasattr(self, 'trainer'):
                    self.trainer.load_model(model_path)
                    self.model = self.trainer.best_model
                    self.model_name = self.trainer.best_model_name
            
            # Load pipeline
            pipeline_path = os.path.join(model_dir, 'preprocessing_pipeline.joblib')
            if os.path.exists(pipeline_path):
                from .data.pipeline import DataPipeline
                self.pipeline = DataPipeline.load(pipeline_path)
            
            if self.verbose:
                print(f"📂 Model and pipeline loaded from {model_dir}")
            
        except Exception as e:
            self.logger.log_error('persistence', 'load_model', e)
            raise
    
    def run_complete_pipeline(self, file_path: str, target_column: str, 
                            output_dir: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Run the complete AutoML pipeline from start to finish.
        
        Args:
            file_path: Path to data file
            target_column: Target column name
            output_dir: Optional output directory for saving results
            **kwargs: Additional arguments for training (multi_objective, optimization_metrics, etc.)
            
        Returns:
            Complete results dictionary
        """
        if self.verbose:
            print("🚀 Running Complete Intelligent AutoML Pipeline")
            print("=" * 60)
        
        try:
            # Step 1: Load and validate data
            self.load_data(file_path, target_column)
            
            # Step 2: Analyze data
            self.analyze_data()
            
            # Step 3: Create and apply preprocessing pipeline
            self.preprocess_data()
            
            # Step 4: Train models with comprehensive evaluation
            self.train_models(**kwargs)
            
            # Step 5: Save results if requested
            if output_dir:
                self.save_model(output_dir)
            
            # Step 6: Generate comprehensive report
            report = self.get_comprehensive_report()
            
            if self.verbose:
                print("\n" + "=" * 60)
                print("🎉 COMPLETE PIPELINE FINISHED!")
                print("=" * 60)
                print(f"📊 Dataset: {report['data_info']['shape'][0]} rows × {report['data_info']['shape'][1]} columns")
                print(f"🧠 Intelligence applied: {len(report['framework_info']['intelligent_features'])} features")
                print(f"🔧 Preprocessing: {report['results']['preprocessing']['original_features']} → {report['results']['preprocessing']['final_features']} features")
                print(f"🏆 Best model: {report['results']['model_training']['best_model']}")
                print(f"📈 Best score: {report['results']['model_training']['best_score']:.4f}")
                print(f"⚡ Total time: {report['performance_summary']['preprocessing_time'] + report['performance_summary']['training_time']:.1f}s")
                
                # Show multi-metric summary
                if 'multi_metric_analysis' in report:
                    analysis = report['multi_metric_analysis']
                    print(f"🎯 Metrics evaluated: {len(analysis['best_model_details']['top_5_metrics'])}")
                    print(f"📊 Models compared: {analysis['models_compared']}")
                    if report['results']['model_training']['optimization_type'] == 'multi_objective':
                        print(f"🔄 Multi-objective optimization: {len(report['results']['model_training']['optimization_metrics'])} metrics")
                
                if output_dir:
                    print(f"💾 Results saved to: {output_dir}")
                
                print("\n🧠 Your data has been intelligently processed with comprehensive evaluation!")
                print("🚀 Framework is ready for production use!")
            
            return report
            
        except Exception as e:
            self.logger.log_error('complete_pipeline', 'run_complete_pipeline', e)
            raise


# Demo and testing functions
def demo_complete_framework():
    """Demonstrate the complete framework with multi-metric evaluation."""
    print("🎭 INTELLIGENT AUTOML FRAMEWORK DEMO WITH MULTI-METRIC EVALUATION")
    print("=" * 80)
    
    # Create sample dataset
    np.random.seed(42)
    sample_data = pd.DataFrame({
        'age': np.random.normal(35, 10, 1000),
        'income': np.random.exponential(50000, 1000),
        'city': np.random.choice(['NYC', 'LA', 'Chicago', 'Houston', 'Phoenix'], 1000),
        'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], 1000),
        'signup_date': pd.date_range('2020-01-01', periods=1000, freq='H'),
        'is_customer': np.random.choice([0, 1], 1000, p=[0.7, 0.3])
    })
    
    # Add realistic data issues
    sample_data.loc[::10, 'age'] = np.nan
    sample_data.loc[::15, 'income'] = np.nan
    sample_data.loc[::20, 'city'] = np.nan
    
    # Save sample data
    sample_data.to_csv('demo_data.csv', index=False)
    
    print("📊 Created sample dataset with 1000 rows and realistic data issues")
    print("🎯 Target: is_customer (binary classification)")
    print("⚠️  Issues: Missing values, mixed data types, datetime features")
    
    # Initialize framework
    framework = IntelligentAutoMLFramework(verbose=True)
    
    # Run complete pipeline with multi-objective optimization
    results = framework.run_complete_pipeline(
        file_path='demo_data.csv',
        target_column='is_customer',
        output_dir='demo_results',
        models_to_try=['random_forest', 'logistic_regression'],
        multi_objective=True,
        optimization_metrics=['f1_weighted', 'precision_weighted', 'accuracy'],
        metric_weights={'f1_weighted': 0.5, 'precision_weighted': 0.3, 'accuracy': 0.2},
        n_trials=30
    )
    
    # Test predictions on new data
    print("\n🔮 Testing predictions on new data...")
    new_data = pd.DataFrame({
        'age': [25, 45, 35],
        'income': [45000, 85000, 65000],
        'city': ['NYC', 'LA', 'Chicago'],
        'education': ['Bachelor', 'Master', 'PhD'],
        'signup_date': pd.date_range('2024-01-01', periods=3)
    })
    
    predictions = framework.make_predictions(new_data)
    probabilities = framework.get_prediction_probabilities(new_data)
    
    print(f"✅ Predictions: {predictions}")
    print(f"🎯 Probabilities: {probabilities[:, 1]}")  # Probability of positive class
    
    # Show comprehensive results
    print("\n🎯 COMPREHENSIVE MULTI-METRIC RESULTS:")
    if 'multi_metric_analysis' in results:
        analysis = results['multi_metric_analysis']
        print(f"🏆 Best model: {analysis['best_model_details']['name']}")
        print(f"📊 Primary score: {analysis['best_model_details']['primary_score']:.4f}")
        
        print(f"\n🎯 Top 5 metrics:")
        for metric in analysis['best_model_details']['top_5_metrics']:
            direction = "↗" if metric['higher_is_better'] else "↘"
            print(f"  • {metric['name']}: {metric['value']:.4f} {direction} ({metric['category']})")
        
        print(f"\n📊 Model comparison:")
        for model_data in analysis['model_rankings']['by_primary_score'][:3]:
            print(f"  • {model_data['model']}: {model_data['primary_score']:.4f}")
    
    # Clean up
    import os
    os.remove('demo_data.csv')
    print("\n🗑️  Demo files cleaned up")


def run_framework_tests():
    """Run basic framework tests."""
    print("🧪 RUNNING FRAMEWORK TESTS")
    print("=" * 50)
    
    try:
        # Test 1: Basic functionality
        print("Test 1: Basic functionality...")
        framework = IntelligentAutoMLFramework(verbose=False)
        
        # Create test data
        test_data = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': ['A', 'B', 'C', 'D', 'E'],
            'target': [0, 1, 0, 1, 0]
        })
        test_data.to_csv('test_data.csv', index=False)
        
        # Run pipeline
        results = framework.run_complete_pipeline(
            'test_data.csv', 
            'target',
            models_to_try=['random_forest']
        )
        
        assert results['results']['model_training']['best_score'] > 0
        print("✅ Test 1 passed")
        
        # Test 2: Model persistence
        print("Test 2: Model persistence...")
        framework.save_model('test_model')
        
        new_framework = IntelligentAutoMLFramework(verbose=False)
        new_framework.load_model('test_model')
        
        test_predictions = new_framework.make_predictions(test_data.drop('target', axis=1))
        assert len(test_predictions) == len(test_data)
        print("✅ Test 2 passed")
        
        # Test 3: Multi-metric evaluation
        print("Test 3: Multi-metric evaluation...")
        framework_multi = IntelligentAutoMLFramework(verbose=False)
        results_multi = framework_multi.run_complete_pipeline(
            'test_data.csv',
            'target',
            multi_objective=True,
            optimization_metrics=['accuracy', 'f1_weighted'],
            models_to_try=['random_forest']
        )
        
        assert 'multi_metric_analysis' in results_multi
        assert results_multi['results']['model_training']['optimization_type'] == 'multi_objective'
        print("✅ Test 3 passed")
        
        print("\n🎉 All tests passed! Framework is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    
    finally:
        # Cleanup
        import os
        import shutil
        for item in ['test_data.csv', 'test_model', 'demo_results']:
            if os.path.exists(item):
                if os.path.isfile(item):
                    os.remove(item)
                else:
                    shutil.rmtree(item)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_framework_tests()
    else:
        demo_complete_framework()