#!/usr/bin/env python
"""
Setup script for Intelligent AutoML Framework
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read version from version.py
version = {}
with open("intelligent_automl/version.py") as fp:
    exec(fp.read(), version)

# Core dependencies
install_requires = [
    "pandas>=1.3.0",
    "numpy>=1.21.0", 
    "scikit-learn>=1.1.0",
    "matplotlib>=3.5.0",
    "seaborn>=0.11.0",
    "scipy>=1.7.0",
    "joblib>=1.1.0",
    "click>=8.0.0",          
    "tqdm>=4.62.0",
    "pydantic>=1.9.0",
    "python-json-logger>=2.0.0",
    "colorlog>=6.6.0",
    "python-dotenv>=0.19.0",
]

# Optional dependencies for advanced features
extras_require = {
    "full": [
        "xgboost>=1.6.0",
        "lightgbm>=3.3.0", 
        "catboost>=1.0.0",
        "optuna>=2.10.0",
        "scikit-optimize>=0.9.0",
    ],
    "dev": [
        "pytest>=6.0",
        "pytest-cov>=2.0", 
        "black>=21.0",
        "flake8>=3.8",
        "mypy>=0.910",
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "twine>=3.0.0",
        "wheel>=0.37.0",
    ],
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=1.0.0", 
        "myst-parser>=0.16.0",
        "sphinx-autoapi>=1.8.0",
    ],
}

# Add 'all' extra that includes everything
extras_require["all"] = list(set(sum(extras_require.values(), [])))

setup(
    name="intelligent-automl",
    version=version["__version__"],
    author="Ahmed Mansour",
    author_email="your.email@example.com",  # Update with your email
    description="Intelligent AutoML Framework with comprehensive multi-metric evaluation and AI-driven optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AhmedMansour1070/intelligent-automl",
    project_urls={
        "Bug Tracker": "https://github.com/AhmedMansour1070/intelligent-automl/issues",
        "Documentation": "https://github.com/AhmedMansour1070/intelligent-automl/docs",
        "Source Code": "https://github.com/AhmedMansour1070/intelligent-automl",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research", 
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Typing :: Typed",
    ],
    keywords=[
        "automl", "machine-learning", "artificial-intelligence", "data-science",
        "automated-ml", "hyperparameter-optimization", "feature-engineering",
        "model-selection", "multi-objective-optimization", "pareto-optimization"
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    
    # Console scripts for CLI
    entry_points={
        "console_scripts": [
            "intelligent-automl=intelligent_automl.cli:main",
        ],
    },
    
    # Include additional files
    include_package_data=True,
    package_data={
        "intelligent_automl": [
            "data/*.csv",
            "configs/*.json",
            "templates/*.txt",
        ],
    },
    
    # Ensure wheel compatibility
    zip_safe=False,
    
    # Additional metadata for PyPI
    license="MIT",
    platforms=["any"],
)