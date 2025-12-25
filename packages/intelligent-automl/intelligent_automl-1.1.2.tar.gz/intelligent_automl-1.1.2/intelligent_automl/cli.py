#!/usr/bin/env python
"""
Command Line Interface for Intelligent AutoML Framework

This CLI provides dataset analysis and simple train/predict entrypoints.
It is designed to work with your packaged code and also degrade gracefully
if only a joblib-saved model is available.

Usage examples:
  intelligent-automl analyze data.csv -o report.txt -f txt
  intelligent-automl analyze data.csv -o report.json -f json
  intelligent-automl train data.csv --target sales --model-out model.pkl
  intelligent-automl predict model.pkl data.csv -o preds.csv
  intelligent-automl train-advanced config.json
"""

from __future__ import annotations

import json
import sys
import os
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import click
import numpy as np
import pandas as pd

# --- Use package version for --version ----
try:
    # This comes from intelligent_automl/version.py
    from intelligent_automl.version import __version__  # noqa: F401
except Exception:  # fallback if import fails during dev
    __version__ = "0.0.0"


# -----------------------------
# Utilities
# -----------------------------
def configure_logging(level: str = "INFO", log_file: Optional[str] = None, log_to_console: bool = True) -> None:
    logger = logging.getLogger()
    logger.setLevel(level.upper())

    # Clear existing handlers so reconfiguring doesn't duplicate logs
    for h in list(logger.handlers):
        logger.removeHandler(h)

    fmt = logging.Formatter("[%(levelname)s] %(message)s")

    if log_to_console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)


def load_data(path: str | os.PathLike) -> pd.DataFrame:
    """Load data with support for multiple formats."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Data file not found: {p}")
    
    # Support multiple formats
    suffix = p.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(p)
    elif suffix in ['.xlsx', '.xls']:
        return pd.read_excel(p)
    elif suffix == '.parquet':
        return pd.read_parquet(p)
    elif suffix == '.json':
        return pd.read_json(p)
    else:
        # Default to CSV
        return pd.read_csv(p)


def _ensure_parent(path: str | os.PathLike) -> None:
    parent = Path(path).parent
    if str(parent) and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def save_text(text: str, path: str | os.PathLike) -> None:
    _ensure_parent(path)
    Path(path).write_text(text, encoding="utf-8")


def save_json(data: Dict[str, Any], path: str | os.PathLike) -> None:
    _ensure_parent(path)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Enhanced lightweight profile with more insights."""
    info: Dict[str, Any] = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(map(str, df.columns)),
        "missing_by_column": {str(c): int(df[c].isna().sum()) for c in df.columns},
        "dtypes": {str(c): str(dt) for c, dt in df.dtypes.items()},
        "memory_bytes": int(df.memory_usage(deep=True).sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "total_missing": int(df.isna().sum().sum()),
        "missing_percentage": float((df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100)
    }

    # Categorize columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    info["column_types"] = {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols
    }

    # Numeric summary
    if numeric_cols:
        num = df[numeric_cols]
        desc = num.describe().to_dict()
        # Cast numpy types to plain python for JSON safety
        info["numeric_summary"] = {
            k: {kk: (float(vv) if np.isfinite(vv) else None) for kk, vv in v.items()} 
            for k, v in desc.items()
        }
        
        # Add skewness information
        info["skewness"] = {col: float(df[col].skew()) for col in numeric_cols if not df[col].isna().all()}

    # Categorical summary
    if categorical_cols:
        info["categorical_summary"] = {}
        for col in categorical_cols:
            unique_count = df[col].nunique()
            info["categorical_summary"][col] = {
                "unique_values": int(unique_count),
                "most_frequent": str(df[col].mode().iloc[0]) if not df[col].empty else None,
                "high_cardinality": unique_count > 50
            }

    return info


def _load_model_or_pipeline(path: str | os.PathLike, verbose: bool = False):
    """
    Attempts to load a trained model/pipeline. Prefers your internal loader
    if available, otherwise falls back to joblib.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Model file not found: {p}")

    # Try your internal API first (custom pipeline)
    try:
        from intelligent_automl.data.pipeline import DataPipeline  # Fixed import path
        if verbose:
            click.echo("Loading using intelligent_automl DataPipeline...")
        return DataPipeline.load(str(p))
    except Exception as e:
        if verbose:
            click.echo(f"Could not load with DataPipeline: {e}")

    # Try complete framework model
    try:
        from intelligent_automl import IntelligentAutoMLFramework
        framework = IntelligentAutoMLFramework()
        if verbose:
            click.echo("Loading using IntelligentAutoMLFramework...")
        framework.load_model(str(p))
        return framework
    except Exception as e:
        if verbose:
            click.echo(f"Could not load with framework: {e}")

    # Try generic joblib
    try:
        import joblib
        if verbose:
            click.echo("Loading using joblib...")
        return joblib.load(p)
    except Exception as e:
        raise RuntimeError(f"Could not load model/pipeline from {p}: {e}") from e


def _clean_prediction_data(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """Remove potential target columns to prevent data leakage."""
    potential_targets = ["target", "label", "y", "outcome", "class", "prediction"]
    cleaned_df = df.copy()
    
    for maybe_target in potential_targets:
        if maybe_target in cleaned_df.columns:
            if verbose:
                click.echo(f"⚠️  Dropping potential target column: {maybe_target}")
            cleaned_df = cleaned_df.drop(columns=[maybe_target])
    
    return cleaned_df


# -----------------------------
# Click group / global options
# -----------------------------
@click.group()
@click.version_option(version=__version__, prog_name="intelligent-automl")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--log-file", type=click.Path(dir_okay=True, writable=True), help="Log file path")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, log_file: Optional[str]) -> None:
    """
    Intelligent AutoML Framework CLI
    
    A comprehensive command-line interface for automated machine learning
    with intelligent preprocessing and multi-metric evaluation.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = bool(verbose)
    ctx.obj["log_file"] = log_file

    log_level = "INFO" if verbose else "WARNING"
    configure_logging(level=log_level, log_file=log_file, log_to_console=True)

    if verbose:
        click.echo("Intelligent AutoML Framework CLI")
        click.echo("Ready to intelligently process your data!\n")


# -----------------------------
# analyze
# -----------------------------
@cli.command()
@click.argument("data_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path for the report")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "txt"]), default="txt", help="Output format")
@click.option("--detailed", is_flag=True, help="Generate detailed analysis report")
@click.pass_context
def analyze(ctx: click.Context, data_file: str, output: Optional[str], fmt: str, detailed: bool) -> None:
    """
    Analyze a dataset and generate a comprehensive report.
    
    Provides insights into data quality, distributions, missing values,
    and recommendations for preprocessing steps.
    """
    verbose = ctx.obj.get("verbose", False)
    
    try:
        if verbose:
            click.echo(f"Analyzing dataset: {data_file}")
            click.echo("Loading data...")
        
        df = load_data(data_file)
        
        if verbose:
            click.echo("Generating profile...")
        
        report = _profile_dataframe(df)
        
        # Add intelligent insights if detailed analysis requested
        if detailed:
            if verbose:
                click.echo("Performing detailed analysis...")
            
            try:
                from intelligent_automl.intelligence.pipeline_selector import IntelligentPipelineSelector
                selector = IntelligentPipelineSelector()
                characteristics = selector.analyze_data(df)
                
                report["intelligent_insights"] = {
                    "data_characteristics": {
                        "outlier_percentage": characteristics.outlier_percentage,
                        "high_cardinality_features": characteristics.high_cardinality_cats,
                        "skewed_features": characteristics.skewed_features,
                        "sparse_features": characteristics.sparse_features,
                        "correlated_pairs": len(characteristics.correlated_feature_pairs)
                    },
                    "recommendations": [
                        {
                            "step": rec.step_name,
                            "reasoning": rec.reasoning,
                            "confidence": rec.confidence,
                            "priority": rec.priority
                        }
                        for rec in selector.generate_recommendations()
                    ]
                }
            except Exception as e:
                if verbose:
                    click.echo(f"Could not generate intelligent insights: {e}")
                report["intelligent_insights"] = {"error": str(e)}

        if output:
            if fmt == "json":
                save_json(report, output)
                click.echo(f"Saved JSON report to: {output}")
            else:
                # Enhanced human-friendly text
                lines = [
                    "=== DATASET ANALYSIS REPORT ===",
                    f"Dataset: {data_file}",
                    f"Rows: {report['rows']:,}",
                    f"Columns: {report['columns']}",
                    f"Memory Usage: {report['memory_bytes']:,} bytes ({report['memory_bytes']/1024/1024:.2f} MB)",
                    f"Duplicate Rows: {report['duplicate_rows']}",
                    f"Total Missing Values: {report['total_missing']} ({report['missing_percentage']:.2f}%)",
                    "",
                    "=== COLUMN INFORMATION ===",
                    f"Numeric Columns ({len(report['column_types']['numeric'])}): {', '.join(report['column_types']['numeric']) or 'None'}",
                    f"Categorical Columns ({len(report['column_types']['categorical'])}): {', '.join(report['column_types']['categorical']) or 'None'}",
                    f"DateTime Columns ({len(report['column_types']['datetime'])}): {', '.join(report['column_types']['datetime']) or 'None'}",
                    "",
                    "=== MISSING VALUES BY COLUMN ===",
                ]
                
                for col, miss in report["missing_by_column"].items():
                    pct = (miss / report['rows']) * 100 if report['rows'] > 0 else 0
                    lines.append(f"  {col}: {miss} ({pct:.1f}%)")
                
                if "numeric_summary" in report:
                    lines.append("\n=== NUMERIC SUMMARY ===")
                    for col, stats in report["numeric_summary"].items():
                        lines.append(f"\n[{col}]")
                        for stat, value in stats.items():
                            lines.append(f"  {stat}: {value}")
                
                if "categorical_summary" in report:
                    lines.append("\n=== CATEGORICAL SUMMARY ===")
                    for col, stats in report["categorical_summary"].items():
                        lines.append(f"\n[{col}]")
                        lines.append(f"  Unique Values: {stats['unique_values']}")
                        lines.append(f"  Most Frequent: {stats['most_frequent']}")
                        if stats['high_cardinality']:
                            lines.append("  ⚠️  HIGH CARDINALITY - Consider target encoding")
                
                if detailed and "intelligent_insights" in report:
                    lines.append("\n=== INTELLIGENT RECOMMENDATIONS ===")
                    if "recommendations" in report["intelligent_insights"]:
                        for rec in report["intelligent_insights"]["recommendations"]:
                            lines.append(f"\n{rec['step'].upper()} (Priority: {rec['priority']}, Confidence: {rec['confidence']:.2f})")
                            lines.append(f"  Reasoning: {rec['reasoning']}")
                
                save_text("\n".join(lines) + "\n", output)
                click.echo(f"Saved detailed text report to: {output}")
        else:
            # Brief summary to stdout
            click.echo(f"\nDataset Summary:")
            click.echo(f"  Rows: {report['rows']:,}")
            click.echo(f"  Columns: {report['columns']}")
            click.echo(f"  Missing: {report['missing_percentage']:.2f}%")
            click.echo(f"  Duplicates: {report['duplicate_rows']}")
            
            if detailed:
                click.echo(f"\nUse --output to save full analysis report")

    except Exception as e:
        if verbose:
            click.echo(f"Full error trace:\n{traceback.format_exc()}", err=True)
        else:
            click.echo(f"❌ analyze failed: {e} (use --verbose for details)", err=True)
        sys.exit(1)


# -----------------------------
# train (enhanced with framework integration)
# -----------------------------
@cli.command()
@click.argument("data_file", type=click.Path(exists=True))
@click.option("--target", "-t", required=True, help="Target column name")
@click.option("--model-out", "-m", required=True, help="Where to save the trained model/pipeline")
@click.option("--seed", type=int, default=42, show_default=True, help="Random seed for reproducibility")
@click.option("--models", help="Comma-separated list of models to try (e.g., 'random_forest,xgboost')")
@click.option("--trials", type=int, default=50, show_default=True, help="Number of optimization trials")
@click.option("--cv-folds", type=int, default=5, show_default=True, help="Cross-validation folds")
@click.option("--multi-objective", is_flag=True, help="Enable multi-objective optimization")
@click.pass_context
def train(ctx: click.Context, data_file: str, target: str, model_out: str, seed: int, 
          models: Optional[str], trials: int, cv_folds: int, multi_objective: bool) -> None:
    """
    Train a model using the Intelligent AutoML Framework.
    
    This command uses the full power of the framework including intelligent
    preprocessing, multi-metric evaluation, and hyperparameter optimization.
    """
    verbose = ctx.obj.get("verbose", False)
    
    try:
        if verbose:
            click.echo(f"Training on: {data_file}")
            click.echo(f"Target: {target}")
            click.echo(f"Output: {model_out}")
            click.echo("Loading data...")
        
        df = load_data(data_file)
        
        if target not in df.columns:
            click.echo(f"❌ Target column '{target}' not found in data.", err=True)
            click.echo(f"Available columns: {', '.join(df.columns)}", err=True)
            sys.exit(1)

        # Try to use the full framework first
        try:
            from intelligent_automl import IntelligentAutoMLFramework
            
            if verbose:
                click.echo("Using Intelligent AutoML Framework...")
            
            framework = IntelligentAutoMLFramework(verbose=verbose)
            
            # Prepare training parameters
            train_params = {
                'cv_folds': cv_folds,
                'n_trials': trials,
                'multi_objective': multi_objective
            }
            
            if models:
                train_params['models_to_try'] = [m.strip() for m in models.split(',')]
            
            if multi_objective:
                # Set default multi-objective metrics
                train_params['optimization_metrics'] = ['f1_weighted', 'precision_weighted', 'accuracy']
            
            # Save dataframe temporarily for framework
            temp_path = Path(data_file).parent / f"temp_{Path(data_file).stem}_framework.csv"
            df.to_csv(temp_path, index=False)
            
            try:
                if verbose:
                    click.echo("Running complete AutoML pipeline...")
                
                results = framework.run_complete_pipeline(
                    str(temp_path),
                    target,
                    **train_params
                )
                
                # Save the trained model
                framework.save_model(model_out)
                
                if verbose:
                    click.echo("Training completed successfully!")
                    training_results = results.get('results', {}).get('model_training', {})
                    click.echo(f"Best Model: {training_results.get('best_model', 'Unknown')}")
                    click.echo(f"Best Score: {training_results.get('best_score', 'Unknown'):.4f}")
                    click.echo(f"Models Evaluated: {training_results.get('models_trained', 'Unknown')}")
                
                click.echo(f"✅ Trained and saved model to: {model_out}")
                
            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
            
        except ImportError as e:
            if verbose:
                click.echo(f"Framework not available: {e}")
                click.echo("Falling back to simple sklearn pipeline...")
            
            # Fallback to simple sklearn pipeline
            X = df.drop(columns=[target])
            y = df[target]

            from sklearn.pipeline import Pipeline
            from sklearn.compose import ColumnTransformer
            from sklearn.preprocessing import OneHotEncoder, StandardScaler
            from sklearn.impute import SimpleImputer
            from sklearn.linear_model import LogisticRegression, LinearRegression
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

            num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()

            num_tf = Pipeline([
                ("impute", SimpleImputer(strategy="median")), 
                ("scale", StandardScaler())
            ])
            cat_tf = Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent")), 
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
            ])

            preprocessor = ColumnTransformer([
                ("num", num_tf, num_cols), 
                ("cat", cat_tf, cat_cols)
            ])

            # Determine if classification or regression
            is_classification = y.dtype.kind in ("i", "u", "b", "O", "U", "S") or y.nunique() <= 20
            
            if is_classification:
                estimator = RandomForestClassifier(random_state=seed, n_estimators=100)
            else:
                estimator = RandomForestRegressor(random_state=seed, n_estimators=100)

            pipeline = Pipeline([("preprocessor", preprocessor), ("estimator", estimator)])
            
            if verbose:
                click.echo("Training sklearn pipeline...")
            
            pipeline.fit(X, y)

            # Save model
            import joblib
            _ensure_parent(model_out)
            joblib.dump(pipeline, model_out)
            
            click.echo(f"✅ Trained and saved sklearn model to: {model_out}")

    except KeyError as e:
        click.echo(f"❌ Column error: {e}", err=True)
        click.echo(f"Available columns: {', '.join(df.columns)}", err=True)
        sys.exit(1)
    except Exception as e:
        if verbose:
            click.echo(f"Full error trace:\n{traceback.format_exc()}", err=True)
        else:
            click.echo(f"❌ train failed: {e} (use --verbose for details)", err=True)
        sys.exit(1)


# -----------------------------
# train-advanced (config file based)
# -----------------------------
@cli.command("train-advanced")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--output-dir", "-o", help="Output directory for results")
@click.pass_context
def train_advanced(ctx: click.Context, config_file: str, output_dir: Optional[str]) -> None:
    """
    Train using a detailed configuration file (JSON format).
    
    The config file should contain comprehensive training parameters,
    model selection criteria, and evaluation settings.
    
    Example config.json:
    {
        "data_file": "data.csv",
        "target_column": "target",
        "models_to_try": ["random_forest", "xgboost", "logistic_regression"],
        "multi_objective": true,
        "optimization_metrics": ["f1_weighted", "precision_weighted"],
        "n_trials": 100,
        "cv_folds": 10
    }
    """
    verbose = ctx.obj.get("verbose", False)
    
    try:
        if verbose:
            click.echo(f"Loading configuration from: {config_file}")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ["data_file", "target_column"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Required field '{field}' missing from config")
        
        # Use framework with configuration
        from intelligent_automl import IntelligentAutoMLFramework
        from intelligent_automl.core.config import AutoMLConfig
        
        if verbose:
            click.echo("Initializing framework with advanced configuration...")
        
        # Create AutoML config if specified
        automl_config = None
        if "evaluation" in config or "optimization" in config:
            automl_config = AutoMLConfig.create_default(
                config.get("task_type", "classification")
            )
            
            # Update with user config
            if "evaluation" in config:
                for key, value in config["evaluation"].items():
                    setattr(automl_config.evaluation, key, value)
            
            if "optimization" in config:
                for key, value in config["optimization"].items():
                    setattr(automl_config.optimization, key, value)
        
        framework = IntelligentAutoMLFramework(
            config=automl_config,
            verbose=verbose
        )
        
        # Extract training parameters
        train_params = {k: v for k, v in config.items() 
                       if k not in ["data_file", "target_column"]}
        
        if output_dir:
            train_params["output_dir"] = output_dir
        
        if verbose:
            click.echo("Running advanced training pipeline...")
        
        results = framework.run_complete_pipeline(
            config["data_file"],
            config["target_column"],
            **train_params
        )
        
        # Save comprehensive results
        if output_dir:
            results_path = Path(output_dir) / "training_results.json"
            save_json(results, results_path)
            click.echo(f"✅ Comprehensive results saved to: {results_path}")
        
        click.echo("✅ Advanced training completed successfully!")
        
    except Exception as e:
        if verbose:
            click.echo(f"Full error trace:\n{traceback.format_exc()}", err=True)
        else:
            click.echo(f"❌ train-advanced failed: {e} (use --verbose for details)", err=True)
        sys.exit(1)


# -----------------------------
# predict (enhanced)
# -----------------------------
@cli.command()
@click.argument("model_file", type=click.Path(exists=True))
@click.argument("data_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Where to save predictions (CSV)")
@click.option("--probabilities", is_flag=True, help="Include prediction probabilities (classification only)")
@click.option("--confidence", is_flag=True, help="Include confidence scores")
@click.pass_context
def predict(ctx: click.Context, model_file: str, data_file: str, output: Optional[str], 
           probabilities: bool, confidence: bool) -> None:
    """
    Generate predictions with a saved model/pipeline.

    Works with:
      - Intelligent AutoML Framework models
      - Custom DataPipeline objects
      - Standard joblib-saved sklearn pipelines
    """
    verbose = ctx.obj.get("verbose", False)
    
    try:
        if verbose:
            click.echo(f"Loading model: {model_file}")
            click.echo(f"Loading data: {data_file}")
        
        df = load_data(data_file)
        original_shape = df.shape
        
        # Clean potential target columns
        df = _clean_prediction_data(df, verbose)
        
        if df.shape[1] != original_shape[1] and verbose:
            click.echo(f"Data shape changed from {original_shape} to {df.shape} after cleaning")

        model = _load_model_or_pipeline(model_file, verbose)

        if verbose:
            click.echo("Generating predictions...")

        # Try different prediction methods based on model type
        predictions = None
        pred_probabilities = None
        
        # Method 1: Framework model
        try:
            if hasattr(model, 'make_predictions'):
                predictions = model.make_predictions(df)
                if probabilities and hasattr(model, 'get_prediction_probabilities'):
                    pred_probabilities = model.get_prediction_probabilities(df)
        except Exception:
            pass
        
        # Method 2: Direct predict method
        if predictions is None:
            try:
                predictions = model.predict(df)
                if probabilities and hasattr(model, 'predict_proba'):
                    pred_probabilities = model.predict_proba(df)
            except Exception:
                pass
        
        # Method 3: Pipeline with transform + predict
        if predictions is None:
            try:
                X_transformed = model.transform(df)
                estimator = getattr(model, "estimator", None) or getattr(model, "named_steps", {}).get("estimator")
                if estimator is None:
                    raise AttributeError("No underlying estimator found.")
                predictions = estimator.predict(X_transformed)
                if probabilities and hasattr(estimator, 'predict_proba'):
                    pred_probabilities = estimator.predict_proba(X_transformed)
            except Exception as e:
                raise RuntimeError(f"Model doesn't expose a usable predict API: {e}") from e

        predictions = np.asarray(predictions)
        
        # Prepare output data
        output_data = {"prediction": predictions}
        
        if pred_probabilities is not None:
            pred_probabilities = np.asarray(pred_probabilities)
            if pred_probabilities.ndim == 2:
                for i in range(pred_probabilities.shape[1]):
                    output_data[f"probability_class_{i}"] = pred_probabilities[:, i]
            else:
                output_data["probability"] = pred_probabilities
        
        if confidence:
            # Simple confidence based on prediction probability
            if pred_probabilities is not None:
                if pred_probabilities.ndim == 2:
                    output_data["confidence"] = np.max(pred_probabilities, axis=1)
                else:
                    output_data["confidence"] = pred_probabilities
            else:
                # For regression, use a simple heuristic
                output_data["confidence"] = np.ones(len(predictions)) * 0.5

        if output:
            out_path = Path(output)
            _ensure_parent(out_path)
            pd.DataFrame(output_data).to_csv(out_path, index=False)
            click.echo(f"💾 Saved predictions to: {output}")
        else:
            # Show summary
            try:
                unique_values, counts = np.unique(predictions, return_counts=True)
                is_classification = predictions.dtype.kind in ("i", "u", "b", "O", "U", "S") or len(unique_values) <= 20
            except Exception:
                unique_values, counts = np.array([]), np.array([])
                is_classification = False

            click.echo(f"\n📊 Prediction Summary:")
            click.echo(f"Total predictions: {len(predictions)}")
            
            if is_classification and len(unique_values) > 0:
                click.echo("Label distribution:")
                for u, c in zip(unique_values, counts):
                    percentage = (c / len(predictions)) * 100
                    click.echo(f"  {u}: {int(c)} ({percentage:.1f}%)")
            else:
                click.echo("Statistical summary:")
                click.echo(f"  mean: {float(np.mean(predictions)):.6f}")
                click.echo(f"  std:  {float(np.std(predictions)):.6f}")
                click.echo(f"  min:  {float(np.min(predictions)):.6f}")
                click.echo(f"  max:  {float(np.max(predictions)):.6f}")

    except Exception as e:
        if verbose:
            click.echo(f"Full error trace:\n{traceback.format_exc()}", err=True)
        else:
            click.echo(f"❌ predict failed: {e} (use --verbose for details)", err=True)
        sys.exit(1)


# -----------------------------
# evaluate (new command for model evaluation)
# -----------------------------
@cli.command()
@click.argument("model_file", type=click.Path(exists=True))
@click.argument("test_data", type=click.Path(exists=True))
@click.option("--target", "-t", required=True, help="Target column name in test data")
@click.option("--output", "-o", help="Where to save evaluation report")
@click.option("--metrics", help="Comma-separated list of specific metrics to compute")
@click.pass_context
def evaluate(ctx: click.Context, model_file: str, test_data: str, target: str, 
            output: Optional[str], metrics: Optional[str]) -> None:
    """
    Evaluate a trained model on test data.
    
    Provides comprehensive evaluation metrics and generates detailed
    performance reports including confusion matrices and error analysis.
    """
    verbose = ctx.obj.get("verbose", False)
    
    try:
        if verbose:
            click.echo(f"Loading model: {model_file}")
            click.echo(f"Loading test data: {test_data}")
        
        # Load test data
        df = load_data(test_data)
        
        if target not in df.columns:
            click.echo(f"❌ Target column '{target}' not found in test data.", err=True)
            click.echo(f"Available columns: {', '.join(df.columns)}", err=True)
            sys.exit(1)
        
        y_true = df[target]
        X_test = df.drop(columns=[target])
        
        # Clean prediction data
        X_test = _clean_prediction_data(X_test, verbose)
        
        # Load model
        model = _load_model_or_pipeline(model_file, verbose)
        
        if verbose:
            click.echo("Generating predictions for evaluation...")
        
        # Get predictions and probabilities
        try:
            if hasattr(model, 'make_predictions'):
                y_pred = model.make_predictions(X_test)
                y_proba = model.get_prediction_probabilities(X_test) if hasattr(model, 'get_prediction_probabilities') else None
            else:
                y_pred = model.predict(X_test)
                y_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
        except Exception as e:
            click.echo(f"❌ Prediction failed: {e}", err=True)
            sys.exit(1)
        
        # Perform evaluation
        try:
            from intelligent_automl.evaluation.multi_metric_evaluator import MultiMetricEvaluator
            
            evaluator = MultiMetricEvaluator()
            
            # Determine task type
            is_classification = y_true.dtype.kind in ("i", "u", "b", "O", "U", "S") or y_true.nunique() <= 20
            
            if is_classification:
                evaluation_results = evaluator.evaluate_classification(
                    y_true.values, y_pred, y_proba,
                    selected_metrics=metrics.split(',') if metrics else None
                )
            else:
                evaluation_results = evaluator.evaluate_regression(
                    y_true.values, y_pred,
                    selected_metrics=metrics.split(',') if metrics else None
                )
            
            # Generate report
            report = {
                "model_file": model_file,
                "test_data": test_data,
                "task_type": "classification" if is_classification else "regression",
                "test_samples": len(y_true),
                "primary_metric": evaluation_results.primary_metric,
                "primary_score": evaluation_results.primary_score,
                "all_metrics": {metric.name: metric.value for metric in evaluation_results.all_metrics.values()}
            }
            
            # Add top metrics
            top_metrics = evaluation_results.get_best_metrics(10)
            report["top_metrics"] = [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "higher_is_better": metric.higher_is_better,
                    "description": metric.description
                }
                for metric in top_metrics
            ]
            
            if output:
                save_json(report, output)
                click.echo(f"✅ Evaluation report saved to: {output}")
            else:
                # Display summary
                click.echo(f"\n📊 Model Evaluation Results:")
                click.echo(f"Task Type: {report['task_type'].title()}")
                click.echo(f"Test Samples: {report['test_samples']:,}")
                click.echo(f"Primary Metric: {report['primary_metric']} = {report['primary_score']:.4f}")
                click.echo(f"\nTop Performing Metrics:")
                for metric in top_metrics[:5]:
                    direction = "↗" if metric.higher_is_better else "↘"
                    click.echo(f"  {metric.name}: {metric.value:.4f} {direction}")
            
        except ImportError:
            # Fallback to basic sklearn metrics
            if verbose:
                click.echo("Using basic sklearn metrics (framework evaluation not available)")
            
            from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
            
            if is_classification:
                accuracy = accuracy_score(y_true, y_pred)
                click.echo(f"\n📊 Basic Evaluation Results:")
                click.echo(f"Accuracy: {accuracy:.4f}")
            else:
                mse = mean_squared_error(y_true, y_pred)
                r2 = r2_score(y_true, y_pred)
                click.echo(f"\n📊 Basic Evaluation Results:")
                click.echo(f"MSE: {mse:.4f}")
                click.echo(f"R²: {r2:.4f}")

    except Exception as e:
        if verbose:
            click.echo(f"Full error trace:\n{traceback.format_exc()}", err=True)
        else:
            click.echo(f"❌ evaluate failed: {e} (use --verbose for details)", err=True)
        sys.exit(1)


# -----------------------------
# info (framework information)
# -----------------------------
@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """
    Display information about the Intelligent AutoML Framework.
    
    Shows version, available components, supported algorithms,
    and configuration options.
    """
    verbose = ctx.obj.get("verbose", False)
    
    click.echo("🧠 Intelligent AutoML Framework")
    click.echo(f"Version: {__version__}")
    click.echo()
    
    # Check component availability
    components = {}
    
    try:
        from intelligent_automl import IntelligentAutoMLFramework
        components["Core Framework"] = "✅ Available"
    except ImportError:
        components["Core Framework"] = "❌ Not Available"
    
    try:
        from intelligent_automl.evaluation.multi_metric_evaluator import MultiMetricEvaluator
        components["Multi-Metric Evaluator"] = "✅ Available"
    except ImportError:
        components["Multi-Metric Evaluator"] = "❌ Not Available"
    
    try:
        from intelligent_automl.intelligence.pipeline_selector import IntelligentPipelineSelector
        components["Intelligent Pipeline Selector"] = "✅ Available"
    except ImportError:
        components["Intelligent Pipeline Selector"] = "❌ Not Available"
    
    # Check optional dependencies
    optional_deps = {}
    
    try:
        import xgboost
        optional_deps["XGBoost"] = f"✅ v{xgboost.__version__}"
    except ImportError:
        optional_deps["XGBoost"] = "❌ Not Available"
    
    try:
        import lightgbm
        optional_deps["LightGBM"] = f"✅ v{lightgbm.__version__}"
    except ImportError:
        optional_deps["LightGBM"] = "❌ Not Available"
    
    try:
        import optuna
        optional_deps["Optuna"] = f"✅ v{optuna.__version__}"
    except ImportError:
        optional_deps["Optuna"] = "❌ Not Available"
    
    click.echo("📦 Core Components:")
    for component, status in components.items():
        click.echo(f"  {component}: {status}")
    
    click.echo()
    click.echo("🔧 Optional Dependencies:")
    for dep, status in optional_deps.items():
        click.echo(f"  {dep}: {status}")
    
    if verbose:
        click.echo()
        click.echo("📚 Available Commands:")
        click.echo("  analyze        - Analyze dataset characteristics")
        click.echo("  train          - Train models with framework")
        click.echo("  train-advanced - Train with configuration file")
        click.echo("  predict        - Generate predictions")
        click.echo("  evaluate       - Evaluate model performance")
        click.echo("  info           - Show framework information")
        
        click.echo()
        click.echo("💡 Example Usage:")
        click.echo("  intelligent-automl analyze data.csv --detailed")
        click.echo("  intelligent-automl train data.csv -t target -m model.pkl --multi-objective")
        click.echo("  intelligent-automl predict model.pkl new_data.csv -o predictions.csv")


# -----------------------------
# Entry point for console script
# -----------------------------
def main() -> None:
    """Entry point used by [project.scripts] in pyproject.toml."""
    cli()


if __name__ == "__main__":
    cli()