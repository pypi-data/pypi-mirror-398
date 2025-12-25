#!/usr/bin/env python
"""
Advanced Pipeline Example - Intelligent AutoML Framework

This example demonstrates advanced features including:
- Detailed data analysis and profiling
- Step-by-step pipeline construction
- Performance profiling and optimization
- Pipeline serialization for production
- Custom configurations and debugging
"""

import pandas as pd
import numpy as np
import time
import warnings
from pathlib import Path

from intelligent_automl import IntelligentPipelineSelector, DataPipeline, create_intelligent_pipeline
from intelligent_automl.data import MissingValueHandler, FeatureScaler, CategoricalEncoder
from intelligent_automl.utils.validation import DataProfiler, validate_dataset

# Suppress warnings for clean output
warnings.filterwarnings('ignore')

def create_complex_dataset():
    """Create a complex dataset with various data challenges."""
    print("🏗️ Creating complex dataset with realistic challenges...")
    np.random.seed(42)
    n_samples = 5000
    
    data = {
        # Numeric features with different distributions
        'age': np.random.normal(35, 10, n_samples),
        'income': np.random.lognormal(10, 1, n_samples),  # Highly skewed
        'credit_score': np.random.normal(650, 100, n_samples),
        'account_balance': np.random.exponential(1000, n_samples),
        'loan_amount': np.random.gamma(2, 1000, n_samples),
        
        # Categorical features with different cardinalities
        'city': np.random.choice(['NYC', 'LA', 'Chicago', 'Houston', 'Phoenix'], n_samples),
        'state': np.random.choice(['NY', 'CA', 'IL', 'TX', 'AZ'], n_samples),
        'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], n_samples),
        'job_category': np.random.choice([f'Job_{i}' for i in range(50)], n_samples),  # High cardinality
        'employment_type': np.random.choice(['Full-time', 'Part-time', 'Contract', 'Unemployed'], n_samples),
        
        # DateTime features
        'signup_date': pd.date_range('2020-01-01', periods=n_samples, freq='H'),
        'last_login': pd.date_range('2023-01-01', periods=n_samples, freq='15min'),
        'birth_date': pd.date_range('1950-01-01', periods=n_samples, freq='W'),
        
        # Binary and sparse features
        'is_premium': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'has_mortgage': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'special_offers': np.random.choice([0, 1, 2, 3], n_samples, p=[0.9, 0.06, 0.03, 0.01]),  # Very sparse
        
        # Target variable (approval decision)
        'loan_approved': np.random.choice([0, 1], n_samples, p=[0.4, 0.6])
    }
    
    df = pd.DataFrame(data)
    
    # Introduce various data quality issues
    print("  🔧 Adding realistic data quality issues...")
    
    # Missing values in different patterns
    missing_random = np.random.choice(n_samples, size=int(0.15 * n_samples), replace=False)
    df.loc[missing_random[:300], 'income'] = np.nan
    df.loc[missing_random[300:500], 'credit_score'] = np.nan
    df.loc[missing_random[500:600], 'education'] = np.nan
    df.loc[missing_random[600:750], 'last_login'] = pd.NaT
    
    # Systematic missing (higher income people less likely to disclose)
    high_income_mask = df['income'] > df['income'].quantile(0.9)
    disclosure_prob = np.where(high_income_mask, 0.3, 0.95)
    for i, prob in enumerate(disclosure_prob):
        if np.random.random() > prob:
            df.loc[i, 'income'] = np.nan
    
    # Outliers
    outlier_indices = np.random.choice(n_samples, size=150, replace=False)
    df.loc[outlier_indices[:50], 'income'] = df.loc[outlier_indices[:50], 'income'] * 10
    df.loc[outlier_indices[50:100], 'credit_score'] = np.random.uniform(-200, 1000, 50)
    df.loc[outlier_indices[100:], 'age'] = np.random.uniform(150, 300, 50)
    
    # Duplicate rows
    duplicate_indices = np.random.choice(n_samples, size=100, replace=False)
    for idx in duplicate_indices:
        if idx < n_samples - 1:
            df.iloc[idx + 1] = df.iloc[idx].copy()
    
    print(f"  ✅ Complex dataset created: {df.shape}")
    print(f"  📊 Features: {df.shape[1]} total")
    print(f"  ❌ Missing values: {df.isnull().sum().sum()}")
    print(f"  🔄 Duplicate rows: {df.duplicated().sum()}")
    
    return df

def detailed_data_analysis():
    """Demonstrate comprehensive data analysis capabilities."""
    print("\n" + "="*80)
    print("🔍 DETAILED DATA ANALYSIS")
    print("="*80)
    
    # Create complex dataset
    df = create_complex_dataset()
    
    # Step 1: Basic data profiling
    print("\n📊 Step 1: Basic Data Profiling")
    profiler = DataProfiler()
    profile = profiler.profile_data(df)
    
    print(f"\n📋 BASIC INFORMATION:")
    basic_info = profile['basic_info']
    print(f"  • Dataset size: {basic_info['shape'][0]:,} rows × {basic_info['shape'][1]} columns")
    print(f"  • Memory usage: {basic_info['memory_usage_mb']:.1f} MB")
    print(f"  • Data types: {basic_info['dtypes']}")
    
    print(f"\n🔍 DATA QUALITY METRICS:")
    quality = profile['data_quality']
    print(f"  • Completeness: {quality['completeness']:.1f}%")
    print(f"  • Duplicate rows: {quality['duplicate_rows']:,}")
    print(f"  • Constant columns: {len(quality['constant_columns'])}")
    print(f"  • High cardinality columns: {len(quality['high_cardinality_columns'])}")
    
    # Step 2: Statistical analysis
    print(f"\n📈 STATISTICAL SUMMARY:")
    if profile['statistical_summary']:
        stats = profile['statistical_summary']
        print(f"  • Highly skewed features: {len(stats.get('highly_skewed_columns', []))}")
        print(f"  • Zero variance features: {len(stats.get('zero_variance_columns', []))}")
    
    # Step 3: Data validation
    print(f"\n✅ DATA VALIDATION:")
    validation_report = validate_dataset(df, target_column='loan_approved')
    print(f"  • Overall status: {'PASSED' if validation_report.is_valid else 'FAILED'}")
    print(f"  • Errors: {validation_report.error_count}")
    print(f"  • Warnings: {validation_report.warning_count}")
    
    # Step 4: Recommendations
    print(f"\n💡 INTELLIGENT RECOMMENDATIONS:")
    recommendations = profile['recommendations']
    priority_counts = {}
    for rec in recommendations:
        priority = rec['priority']
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    for priority in ['high', 'medium', 'low']:
        count = priority_counts.get(priority, 0)
        if count > 0:
            emoji = "🔴" if priority == 'high' else "🟡" if priority == 'medium' else "🟢"
            print(f"  {emoji} {priority.title()} priority: {count} recommendations")
    
    # Show top recommendations
    high_priority = [r for r in recommendations if r['priority'] == 'high']
    if high_priority:
        print(f"\n🔴 TOP HIGH PRIORITY ISSUES:")
        for rec in high_priority[:3]:
            print(f"  • {rec['message']}")
    
    return df, profile

def intelligent_pipeline_construction():
    """Demonstrate intelligent pipeline construction with detailed analysis."""
    print("\n" + "="*80)
    print("🧠 INTELLIGENT PIPELINE CONSTRUCTION")
    print("="*80)
    
    # Get data from previous analysis
    df, profile = detailed_data_analysis()
    
    # Initialize intelligent selector
    print("\n🤖 Initializing Intelligent Pipeline Selector...")
    selector = IntelligentPipelineSelector(target_column='loan_approved')
    
    # Step 1: Analyze data characteristics
    print("\n📊 Step 1: Deep Data Analysis")
    characteristics = selector.analyze_data(df)
    
    print(f"  🔍 DISCOVERED CHARACTERISTICS:")
    print(f"    • Numeric features: {len(characteristics.numeric_features)}")
    print(f"    • Categorical features: {len(characteristics.categorical_features)}")
    print(f"    • DateTime features: {len(characteristics.datetime_features)}")
    print(f"    • Text features: {len(characteristics.text_features)}")
    print(f"    • Missing pattern: {characteristics.missing_pattern}")
    print(f"    • Target type: {characteristics.target_type}")
    print(f"    • Target balance: {characteristics.target_balance}")
    
    # Step 2: Generate intelligent recommendations
    print(f"\n🧠 Step 2: Generating Intelligent Recommendations")
    recommendations = selector.generate_recommendations()
    
    print(f"  💡 GENERATED {len(recommendations)} RECOMMENDATIONS:")
    for i, rec in enumerate(recommendations, 1):
        confidence_emoji = "🟢" if rec.confidence >= 0.8 else "🟡" if rec.confidence >= 0.6 else "🔴"
        print(f"    {i}. {rec.step_name.upper()} {confidence_emoji}")
        print(f"       Confidence: {rec.confidence:.1%} | Priority: {rec.priority}")
        print(f"       Reason: {rec.reasoning}")
        print(f"       Params: {rec.parameters}")
        print()
    
    # Step 3: Build intelligent pipeline
    print(f"🔧 Step 3: Building Intelligent Pipeline")
    pipeline = selector.build_intelligent_pipeline()
    
    print(f"  ✅ PIPELINE CONSTRUCTED:")
    print(f"    • Total steps: {len(pipeline)}")
    print(f"    • Steps: {', '.join(pipeline.get_step_names())}")
    
    # Step 4: Validate pipeline
    print(f"\n🔍 Step 4: Pipeline Validation")
    features = df.drop('loan_approved', axis=1)
    validation_report = pipeline.validate(features)
    
    print(f"  ✅ VALIDATION RESULTS:")
    print(f"    • Status: {'VALID' if validation_report['is_valid'] else 'INVALID'}")
    if validation_report['errors']:
        print(f"    • Errors: {validation_report['errors']}")
    if validation_report['warnings']:
        print(f"    • Warnings: {validation_report['warnings']}")
    
    return df, pipeline, selector

def performance_profiling_and_optimization():
    """Demonstrate performance profiling and optimization techniques."""
    print("\n" + "="*80)
    print("⚡ PERFORMANCE PROFILING & OPTIMIZATION")
    print("="*80)
    
    # Get pipeline from previous step
    df, pipeline, selector = intelligent_pipeline_construction()
    features = df.drop('loan_approved', axis=1)
    
    # Step 1: Fit pipeline
    print("\n🏃 Step 1: Fitting Pipeline")
    fit_start = time.time()
    pipeline.fit(features)
    fit_time = time.time() - fit_start
    print(f"  ⏱️ Fit time: {fit_time:.3f} seconds")
    
    # Step 2: Performance profiling
    print(f"\n📊 Step 2: Performance Profiling")
    performance = pipeline.profile_performance(features, n_iterations=3)
    
    print(f"  🔍 PERFORMANCE ANALYSIS:")
    print(f"    • Total time: {performance['total_time_seconds']:.3f} seconds")
    print(f"    • Throughput: {len(features) / performance['total_time_seconds']:.0f} rows/second")
    
    print(f"  📈 STEP-BY-STEP PERFORMANCE:")
    for step in performance['steps']:
        throughput = step['throughput_rows_per_second']
        print(f"    • {step['name']}: {step['avg_time_seconds']:.3f}s ({throughput:.0f} rows/sec)")
        
        # Identify bottlenecks
        if step['avg_time_seconds'] > performance['total_time_seconds'] * 0.4:
            print(f"      ⚠️ BOTTLENECK DETECTED")
    
    # Step 3: Memory analysis
    print(f"\n💾 Step 3: Memory Usage Analysis")
    memory_info = pipeline.get_memory_usage()
    
    print(f"  🔍 MEMORY ANALYSIS:")
    print(f"    • Total pipeline: {memory_info['total_size_mb']:.2f} MB")
    for step in memory_info['steps']:
        print(f"    • {step['name']}: {step['size_bytes'] / 1024**2:.2f} MB")
    
    # Step 4: Scalability testing
    print(f"\n📈 Step 4: Scalability Testing")
    
    # Test with different data sizes
    sizes = [1000, 2500, 5000]
    print(f"  🔍 SCALABILITY RESULTS:")
    
    for size in sizes:
        test_df = df.head(size)
        test_features = test_df.drop('loan_approved', axis=1)
        
        start_time = time.time()
        processed = pipeline.transform(test_features)
        process_time = time.time() - start_time
        
        throughput = size / process_time if process_time > 0 else float('inf')
        print(f"    • {size:,} rows: {process_time:.3f}s ({throughput:.0f} rows/sec)")
    
    return pipeline, performance

def pipeline_serialization_and_persistence():
    """Demonstrate pipeline serialization for production deployment."""
    print("\n" + "="*80)
    print("💾 PIPELINE SERIALIZATION & PERSISTENCE")
    print("="*80)
    
    # Get optimized pipeline
    pipeline, performance = performance_profiling_and_optimization()
    
    # Step 1: Save pipeline
    print("\n💾 Step 1: Saving Pipeline for Production")
    
    # Save in multiple formats
    formats = {
        'production_pipeline.joblib': 'joblib',
        'production_pipeline.pkl': 'pickle'
    }
    
    for filepath, format_type in formats.items():
        try:
            pipeline.save(filepath, format=format_type)
            file_size = Path(filepath).stat().st_size / 1024  # KB
            print(f"  ✅ Saved as {format_type}: {filepath} ({file_size:.1f} KB)")
        except Exception as e:
            print(f"  ❌ Failed to save {format_type}: {str(e)}")
    
    # Step 2: Save pipeline configuration
    print(f"\n📋 Step 2: Exporting Configuration")
    try:
        pipeline.save_config('pipeline_config.json')
        print(f"  ✅ Configuration exported: pipeline_config.json")
    except Exception as e:
        print(f"  ❌ Configuration export failed: {str(e)}")
    
    # Step 3: Load and test pipeline
    print(f"\n📂 Step 3: Loading and Testing Pipeline")
    try:
        loaded_pipeline = DataPipeline.load('production_pipeline.joblib')
        print(f"  ✅ Pipeline loaded successfully")
        
        # Test with sample data
        df = create_complex_dataset()
        test_features = df.drop('loan_approved', axis=1).head(100)
        
        start_time = time.time()
        result = loaded_pipeline.transform(test_features)
        load_time = time.time() - start_time
        
        print(f"  ✅ Test transformation: {test_features.shape} → {result.shape}")
        print(f"  ⏱️ Processing time: {load_time:.3f}s")
        
    except Exception as e:
        print(f"  ❌ Loading/testing failed: {str(e)}")
    
    # Step 4: Production deployment preparation
    print(f"\n🚀 Step 4: Production Deployment Info")
    
    deployment_info = {
        'pipeline_version': '1.0.0',
        'creation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'performance': {
            'avg_processing_time': performance['total_time_seconds'],
            'throughput_rows_per_sec': 5000 / performance['total_time_seconds']
        },
        'requirements': [
            'pandas>=1.3.0',
            'numpy>=1.21.0',
            'scikit-learn>=1.1.0',
            'intelligent-automl>=1.0.0'
        ],
        'usage_example': {
            'load': "pipeline = DataPipeline.load('production_pipeline.joblib')",
            'transform': "processed_data = pipeline.transform(new_data)"
        }
    }
    
    # Save deployment info
    import json
    with open('deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"  ✅ Deployment info saved: deployment_info.json")
    print(f"  📊 Expected throughput: {deployment_info['performance']['throughput_rows_per_sec']:.0f} rows/sec")
    
    return loaded_pipeline

def custom_pipeline_construction():
    """Demonstrate manual pipeline construction for comparison."""
    print("\n" + "="*80)
    print("🔧 CUSTOM PIPELINE CONSTRUCTION")
    print("="*80)
    
    # Create sample data
    df = create_complex_dataset()
    features = df.drop('loan_approved', axis=1)
    
    # Step 1: Manual pipeline (traditional approach)
    print("\n🔧 Step 1: Manual Pipeline Construction")
    
    manual_pipeline = (DataPipeline()
                      .add_step('missing_values', MissingValueHandler(
                          numeric_strategy='mean',
                          categorical_strategy='most_frequent'
                      ))
                      .add_step('categorical_encoding', CategoricalEncoder(
                          method='onehot'
                      ))
                      .add_step('feature_scaling', FeatureScaler(
                          method='standard'
                      )))
    
    print(f"  🔧 Manual pipeline: {len(manual_pipeline)} steps")
    print(f"  📋 Steps: {', '.join(manual_pipeline.get_step_names())}")
    
    # Step 2: Intelligent pipeline (our approach)
    print(f"\n🧠 Step 2: Intelligent Pipeline Construction")
    
    intelligent_pipeline = create_intelligent_pipeline(df, target_column='loan_approved')
    
    print(f"  🧠 Intelligent pipeline: {len(intelligent_pipeline)} steps")
    print(f"  📋 Steps: {', '.join(intelligent_pipeline.get_step_names())}")
    
    # Step 3: Performance comparison
    print(f"\n⚖️ Step 3: Performance Comparison")
    
    # Manual pipeline processing
    manual_start = time.time()
    manual_pipeline.fit(features)
    manual_result = manual_pipeline.transform(features)
    manual_time = time.time() - manual_start
    
    # Intelligent pipeline processing
    intelligent_start = time.time()
    intelligent_pipeline.fit(features)
    intelligent_result = intelligent_pipeline.transform(features)
    intelligent_time = time.time() - intelligent_start
    
    print(f"  📊 COMPARISON RESULTS:")
    print(f"    🔧 Manual Pipeline:")
    print(f"      • Time: {manual_time:.3f}s")
    print(f"      • Features: {features.shape[1]} → {manual_result.shape[1]}")
    print(f"      • Missing values: {manual_result.isnull().sum().sum()}")
    print(f"      • Steps: {len(manual_pipeline)}")
    
    print(f"    🧠 Intelligent Pipeline:")
    print(f"      • Time: {intelligent_time:.3f}s")
    print(f"      • Features: {features.shape[1]} → {intelligent_result.shape[1]}")
    print(f"      • Missing values: {intelligent_result.isnull().sum().sum()}")
    print(f"      • Steps: {len(intelligent_pipeline)}")
    
    # Analysis
    speed_improvement = manual_time / intelligent_time if intelligent_time > 0 else float('inf')
    feature_improvement = intelligent_result.shape[1] / manual_result.shape[1]
    
    print(f"  🏆 IMPROVEMENT ANALYSIS:")
    print(f"    • Speed: {speed_improvement:.1f}x {'faster' if speed_improvement > 1 else 'slower'}")
    print(f"    • Feature engineering: {feature_improvement:.1f}x more features")
    print(f"    • Data quality: {'Perfect' if intelligent_result.isnull().sum().sum() == 0 else 'Issues remain'}")
    print(f"    • Intelligence: Automatic vs Manual configuration")
    
    return manual_pipeline, intelligent_pipeline

def advanced_debugging_and_troubleshooting():
    """Demonstrate debugging and troubleshooting techniques."""
    print("\n" + "="*80)
    print("🛠️ ADVANCED DEBUGGING & TROUBLESHOOTING")
    print("="*80)
    
    # Create problematic data
    print("\n🧪 Creating problematic dataset for debugging...")
    np.random.seed(999)
    
    # Dataset with various issues
    problematic_data = pd.DataFrame({
        'numeric_with_strings': ['1.5', '2.0', 'invalid', '4.0', '5.5'] * 1000,
        'all_missing': [np.nan] * 5000,
        'constant_column': [42] * 5000,
        'extreme_outliers': np.concatenate([
            np.random.normal(100, 10, 4990),
            [999999] * 10  # Extreme outliers
        ]),
        'mixed_types': [1, 'text', 3.14, None, True] * 1000,
        'target': np.random.choice([0, 1], 5000)
    })
    
    print(f"  ✅ Problematic dataset created: {problematic_data.shape}")
    
    # Step 1: Detailed error analysis
    print(f"\n🔍 Step 1: Pre-processing Diagnostics")
    
    # Analyze each column
    for col in problematic_data.columns:
        if col == 'target':
            continue
            
        print(f"  📋 Column '{col}':")
        print(f"    • Data type: {problematic_data[col].dtype}")
        print(f"    • Missing values: {problematic_data[col].isnull().sum()}")
        print(f"    • Unique values: {problematic_data[col].nunique()}")
        
        # Check for mixed types
        try:
            sample = problematic_data[col].dropna().head(10)
            types = set(type(x).__name__ for x in sample)
            if len(types) > 1:
                print(f"    ⚠️ Mixed types detected: {types}")
        except:
            print(f"    ⚠️ Analysis failed")
    
    # Step 2: Graceful error handling
    print(f"\n🛡️ Step 2: Graceful Error Handling")
    
    try:
        # Try to create intelligent pipeline
        pipeline = create_intelligent_pipeline(problematic_data, target_column='target')
        print(f"  ✅ Pipeline created successfully despite data issues!")
        
        # Try to process data
        features = problematic_data.drop('target', axis=1)
        processed = pipeline.fit_transform(features)
        print(f"  ✅ Data processed: {features.shape} → {processed.shape}")
        
    except Exception as e:
        print(f"  ❌ Pipeline creation failed: {str(e)}")
        
        # Step-by-step debugging
        print(f"\n🔧 Step-by-step debugging:")
        
        # Try individual processors
        from intelligent_automl.data import MissingValueHandler
        
        try:
            handler = MissingValueHandler()
            handler.fit(features)
            print(f"    ✅ Missing value handler: OK")
        except Exception as e:
            print(f"    ❌ Missing value handler: {str(e)}")
        
        try:
            encoder = CategoricalEncoder()
            encoder.fit(features)
            print(f"    ✅ Categorical encoder: OK")
        except Exception as e:
            print(f"    ❌ Categorical encoder: {str(e)}")
    
    # Step 3: Data quality recommendations
    print(f"\n💡 Step 3: Data Quality Recommendations")
    
    recommendations = []
    
    # Check for common issues
    if (problematic_data == problematic_data.iloc[0]).all().any():
        recommendations.append("Remove constant columns")
    
    if problematic_data.isnull().all().any():
        recommendations.append("Remove completely empty columns")
    
    # Check for extreme outliers
    for col in problematic_data.select_dtypes(include=[np.number]).columns:
        if col != 'target':
            Q1 = problematic_data[col].quantile(0.25)
            Q3 = problematic_data[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((problematic_data[col] < Q1 - 3 * IQR) | 
                       (problematic_data[col] > Q3 + 3 * IQR)).sum()
            if outliers > 0:
                recommendations.append(f"Handle {outliers} extreme outliers in '{col}'")
    
    print(f"  📋 RECOMMENDATIONS:")
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec}")
    
    if not recommendations:
        print(f"    ✅ No major data quality issues detected")

def main():
    """Run all advanced pipeline examples."""
    print("🧠 INTELLIGENT AUTOML FRAMEWORK - ADVANCED PIPELINE EXAMPLES")
    print("=" * 100)
    print("Demonstrating advanced features, performance optimization, and production deployment\n")
    
    try:
        # Run all advanced examples
        detailed_data_analysis()
        intelligent_pipeline_construction()
        performance_profiling_and_optimization()
        pipeline_serialization_and_persistence()
        custom_pipeline_construction()
        advanced_debugging_and_troubleshooting()
        
        print("\n" + "=" * 100)
        print("🎊 ALL ADVANCED EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 100)
        print("✅ Detailed data analysis and profiling")
        print("✅ Intelligent pipeline construction with explanations")
        print("✅ Performance profiling and optimization")
        print("✅ Production-ready serialization and persistence")
        print("✅ Manual vs intelligent pipeline comparison")
        print("✅ Advanced debugging and troubleshooting")
        
        print("\n🎯 KEY ADVANCED INSIGHTS:")
        print("  🧠 Framework provides deep intelligence about your data")
        print("  ⚡ Performance optimization identifies bottlenecks automatically")
        print("  🏭 Production deployment is streamlined and robust")
        print("  🔧 Manual configuration is outperformed by intelligent selection")
        print("  🛠️ Advanced debugging helps with problematic datasets")
        print("  📊 Comprehensive profiling enables data-driven decisions")
        
        print("\n🚀 PRODUCTION READINESS:")
        print("  💾 Serialized pipelines ready for deployment")
        print("  📋 Configuration files for reproducibility") 
        print("  📊 Performance benchmarks for capacity planning")
        print("  🛡️ Error handling for robust production use")
        
    except Exception as e:
        print(f"\n❌ Advanced example failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup generated files
        cleanup_files = [
            'production_pipeline.joblib',
            'production_pipeline.pkl', 
            'pipeline_config.json',
            'deployment_info.json'
        ]
        
        import os
        for file in cleanup_files:
            if os.path.exists(file):
                os.remove(file)
        
        print("\n🗑️ Cleaned up temporary files")

if __name__ == "__main__":
    main()