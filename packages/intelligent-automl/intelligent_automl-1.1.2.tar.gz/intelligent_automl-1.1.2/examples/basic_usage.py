#!/usr/bin/env python
"""
Basic Usage Example - Intelligent AutoML Framework

This example shows the simplest way to use the intelligent AutoML framework
with a sample dataset. Perfect for getting started!
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from intelligent_automl import create_intelligent_pipeline, IntelligentAutoMLFramework

def create_sample_data():
    """Create a sample dataset for demonstration."""
    print("📊 Creating sample dataset...")
    np.random.seed(42)
    
    data = {
        'age': np.random.normal(35, 10, 1000),
        'income': np.random.exponential(50000, 1000),
        'city': np.random.choice(['NYC', 'LA', 'Chicago', 'Houston'], 1000),
        'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], 1000),
        'signup_date': pd.date_range('2020-01-01', periods=1000, freq='D'),
        'is_premium': np.random.choice([0, 1], 1000, p=[0.8, 0.2]),
        'target': np.random.choice([0, 1], 1000, p=[0.7, 0.3])
    }
    
    df = pd.DataFrame(data)
    
    # Add some missing values to make it realistic
    missing_indices = np.random.choice(1000, size=100, replace=False)
    df.loc[missing_indices[:50], 'age'] = np.nan
    df.loc[missing_indices[50:], 'income'] = np.nan
    
    print(f"✅ Dataset created: {df.shape[0]} rows × {df.shape[1]} columns")
    return df

def example_1_simple_pipeline():
    """Example 1: Simple intelligent pipeline creation."""
    print("\n" + "="*60)
    print("🧠 EXAMPLE 1: Simple Intelligent Pipeline")
    print("="*60)
    
    # Create sample data
    df = create_sample_data()
    print(f"📋 Columns: {list(df.columns)}")
    print(f"❌ Missing values: {df.isnull().sum().sum()}")
    
    # Create intelligent pipeline with just one line!
    print("\n🧠 Creating intelligent pipeline...")
    pipeline = create_intelligent_pipeline(df, target_column='target')
    
    # Process data
    print("⚙️ Processing data...")
    features = df.drop('target', axis=1)
    processed_features = pipeline.fit_transform(features)
    
    # Results
    print(f"\n✅ Processing complete!")
    print(f"📈 Features: {features.shape[1]} → {processed_features.shape[1]}")
    print(f"🎯 Missing values after: {processed_features.isnull().sum().sum()}")
    print(f"🚀 Pipeline steps: {', '.join(pipeline.get_step_names())}")
    
    return df, pipeline

def example_2_complete_automl():
    """Example 2: Complete AutoML pipeline with model training."""
    print("\n" + "="*60)
    print("🤖 EXAMPLE 2: Complete AutoML Pipeline")
    print("="*60)
    
    # Create and save sample data
    df = create_sample_data()
    df.to_csv('sample_data.csv', index=False)
    print("💾 Saved sample data to 'sample_data.csv'")
    
    # Initialize complete AutoML framework
    print("\n🚀 Initializing AutoML framework...")
    framework = IntelligentAutoMLFramework(verbose=True)
    
    # Run complete pipeline
    print("🔄 Running complete AutoML pipeline...")
    results = framework.run_complete_pipeline(
        'sample_data.csv',
        'target',
        models_to_try=['random_forest', 'logistic_regression'],
        time_limit_minutes=1  # Quick demo
    )
    
    # Show results
    print(f"\n🏆 RESULTS:")
    model_results = results['results']['model_training']
    print(f"  • Best model: {model_results['best_model']}")
    print(f"  • Best score: {model_results['best_score']:.4f}")
    print(f"  • Models trained: {model_results['models_trained']}")
    
    # Cleanup
    import os
    if os.path.exists('sample_data.csv'):
        os.remove('sample_data.csv')
    
    return results

def example_3_custom_data():
    """Example 3: Using with your own data structure."""
    print("\n" + "="*60)
    print("📊 EXAMPLE 3: Custom Data Processing")
    print("="*60)
    
    # Create more complex dataset
    print("🏗️ Creating complex dataset...")
    np.random.seed(123)
    
    complex_data = {
        # Numeric features with different distributions
        'customer_age': np.random.gamma(2, 20, 2000),  # Skewed
        'annual_income': np.random.lognormal(10, 1, 2000),  # Very skewed
        'credit_score': np.random.normal(650, 100, 2000),
        'account_balance': np.random.exponential(5000, 2000),
        
        # Categorical features
        'country': np.random.choice(['USA', 'UK', 'Canada', 'Australia', 'Germany'], 2000),
        'job_title': np.random.choice([f'Job_{i}' for i in range(20)], 2000),  # High cardinality
        'subscription_type': np.random.choice(['Basic', 'Premium', 'Enterprise'], 2000),
        
        # Date features
        'registration_date': pd.date_range('2018-01-01', periods=2000, freq='12H'),
        'last_activity': pd.date_range('2023-01-01', periods=2000, freq='6H'),
        
        # Target
        'will_churn': np.random.choice([0, 1], 2000, p=[0.75, 0.25])
    }
    
    df = pd.DataFrame(complex_data)
    
    # Add realistic missing patterns
    # Income missing for privacy-conscious high earners
    high_income = df['annual_income'] > df['annual_income'].quantile(0.8)
    df.loc[high_income & (np.random.random(2000) < 0.3), 'annual_income'] = np.nan
    
    # Random missing in other columns
    df.loc[np.random.choice(2000, 200, replace=False), 'credit_score'] = np.nan
    df.loc[np.random.choice(2000, 150, replace=False), 'job_title'] = np.nan
    
    print(f"✅ Complex dataset: {df.shape}")
    print(f"📊 Features: {df.shape[1]-1}")
    print(f"❌ Missing values: {df.isnull().sum().sum()}")
    print(f"📈 Data types: {df.dtypes.value_counts().to_dict()}")
    
    # Process with intelligent pipeline
    print("\n🧠 Applying intelligent preprocessing...")
    pipeline = create_intelligent_pipeline(df, target_column='will_churn')
    
    features = df.drop('will_churn', axis=1)
    processed = pipeline.fit_transform(features)
    
    print(f"\n🎉 TRANSFORMATION RESULTS:")
    print(f"  📈 Feature expansion: {features.shape[1]} → {processed.shape[1]} ({processed.shape[1]/features.shape[1]:.1f}x)")
    print(f"  🎯 Missing values: {features.isnull().sum().sum()} → {processed.isnull().sum().sum()}")
    print(f"  💾 Memory usage: {processed.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print(f"  🔧 Pipeline steps: {len(pipeline)}")
    
    # Show what happened to each data type
    print(f"\n🔍 PROCESSING DETAILS:")
    for step_name in pipeline.get_step_names():
        print(f"  ✅ {step_name}")
    
    return df, processed

def example_4_performance_comparison():
    """Example 4: Performance comparison with manual preprocessing."""
    print("\n" + "="*60)
    print("⚡ EXAMPLE 4: Performance Comparison")
    print("="*60)
    
    # Create performance test dataset
    print("🏗️ Creating performance test dataset...")
    np.random.seed(456)
    
    # Larger dataset for performance testing
    n_samples = 10000
    perf_data = {
        'numeric_1': np.random.normal(0, 1, n_samples),
        'numeric_2': np.random.exponential(1, n_samples),
        'numeric_3': np.random.gamma(2, 2, n_samples),
        'category_1': np.random.choice(['A', 'B', 'C', 'D'], n_samples),
        'category_2': np.random.choice([f'Cat_{i}' for i in range(10)], n_samples),
        'date_col': pd.date_range('2020-01-01', periods=n_samples, freq='H'),
        'target': np.random.choice([0, 1], n_samples)
    }
    
    df = pd.DataFrame(perf_data)
    
    # Add missing values
    missing_mask = np.random.random(n_samples) < 0.1
    df.loc[missing_mask, 'numeric_1'] = np.nan
    df.loc[np.random.random(n_samples) < 0.05, 'category_1'] = np.nan
    
    print(f"✅ Performance dataset: {df.shape}")
    
    # Test intelligent pipeline
    print("\n🧠 Testing intelligent pipeline...")
    import time
    
    start_time = time.time()
    intelligent_pipeline = create_intelligent_pipeline(df, target_column='target')
    features = df.drop('target', axis=1)
    intelligent_result = intelligent_pipeline.fit_transform(features)
    intelligent_time = time.time() - start_time
    
    # Test manual pipeline (basic approach)
    print("🔧 Testing manual pipeline...")
    from intelligent_automl.data import MissingValueHandler, FeatureScaler, CategoricalEncoder, DataPipeline
    
    start_time = time.time()
    manual_pipeline = (DataPipeline()
                      .add_step('missing', MissingValueHandler())
                      .add_step('encoding', CategoricalEncoder())
                      .add_step('scaling', FeatureScaler()))
    
    manual_result = manual_pipeline.fit_transform(features)
    manual_time = time.time() - start_time
    
    # Performance comparison
    print(f"\n📊 PERFORMANCE COMPARISON:")
    print(f"  🧠 Intelligent Pipeline:")
    print(f"    • Time: {intelligent_time:.3f} seconds")
    print(f"    • Features: {features.shape[1]} → {intelligent_result.shape[1]}")
    print(f"    • Throughput: {len(features) / intelligent_time:.0f} rows/sec")
    print(f"    • Steps: {len(intelligent_pipeline)}")
    
    print(f"  🔧 Manual Pipeline:")
    print(f"    • Time: {manual_time:.3f} seconds")
    print(f"    • Features: {features.shape[1]} → {manual_result.shape[1]}")
    print(f"    • Throughput: {len(features) / manual_time:.0f} rows/sec")
    print(f"    • Steps: {len(manual_pipeline)}")
    
    # Improvement metrics
    speed_ratio = manual_time / intelligent_time if intelligent_time > 0 else float('inf')
    feature_ratio = intelligent_result.shape[1] / manual_result.shape[1]
    
    print(f"\n🏆 INTELLIGENT ADVANTAGE:")
    print(f"  ⚡ Speed: {speed_ratio:.1f}x {'faster' if speed_ratio > 1 else 'slower'}")
    print(f"  📈 Feature engineering: {feature_ratio:.1f}x more features")
    print(f"  🧠 Zero configuration vs manual setup")
    print(f"  🎯 Automatically optimized for your data")

def main():
    """Run all basic usage examples."""
    print("🧠 INTELLIGENT AUTOML FRAMEWORK - BASIC USAGE EXAMPLES")
    print("=" * 80)
    print("Learn how to use the framework with simple, practical examples\n")
    
    try:
        # Run all examples
        example_1_simple_pipeline()
        example_2_complete_automl()
        example_3_custom_data()
        example_4_performance_comparison()
        
        print("\n" + "="*80)
        print("🎉 ALL BASIC EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("✅ Simple intelligent pipeline creation")
        print("✅ Complete AutoML pipeline with model training")
        print("✅ Custom data processing with complex datasets")
        print("✅ Performance comparison with manual approaches")
        
        print("\n🎯 KEY TAKEAWAYS:")
        print("  🧠 One line creates an optimized preprocessing pipeline")
        print("  ⚡ Automatic feature engineering saves hours of work")
        print("  🎯 Perfect data quality with zero missing values")
        print("  🚀 Ready for production use immediately")
        
        print("\n📚 NEXT STEPS:")
        print("  • Try with your own datasets")
        print("  • Explore advanced_pipeline.py for more features")
        print("  • Check out the Jupyter notebooks for interactive examples")
        
    except Exception as e:
        print(f"\n❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
