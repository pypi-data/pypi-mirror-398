# ===================================
# FILE: automl_framework/data/loaders.py
# LOCATION: /automl_framework/automl_framework/data/loaders.py
# ===================================

"""
Data loading strategies for the AutoML framework.

This module provides various data loaders for different file formats
and data sources, with automatic format detection and validation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import urllib.parse
import warnings

from ..core.base import DataLoader
from ..core.exceptions import DataLoadError, DataValidationError, handle_data_error
from ..core.types import DataFrame, FilePath, DataFormat


class CSVLoader(DataLoader):
    """
    Loader for CSV files with advanced parsing options.
    
    Supports various CSV formats, encodings, and parsing parameters
    with automatic delimiter detection and error handling.
    """
    
    def __init__(self, 
                 delimiter: Optional[str] = None,
                 encoding: str = 'utf-8',
                 header: Union[int, str] = 'infer',
                 index_col: Optional[Union[int, str]] = None,
                 skip_rows: Optional[int] = None,
                 max_rows: Optional[int] = None,
                 dtype_inference: bool = True,
                 parse_dates: bool = True,
                 **pandas_kwargs):
        """
        Initialize CSV loader.
        
        Args:
            delimiter: Column delimiter (auto-detect if None)
            encoding: File encoding
            header: Row number(s) to use as column names
            index_col: Column to use as row index
            skip_rows: Number of rows to skip at start
            max_rows: Maximum number of rows to read
            dtype_inference: Whether to infer data types
            parse_dates: Whether to parse date columns automatically
            **pandas_kwargs: Additional arguments for pandas.read_csv
        """
        self.delimiter = delimiter
        self.encoding = encoding
        self.header = header
        self.index_col = index_col
        self.skip_rows = skip_rows
        self.max_rows = max_rows
        self.dtype_inference = dtype_inference
        self.parse_dates = parse_dates
        self.pandas_kwargs = pandas_kwargs
    
    def _detect_delimiter(self, filepath: str, sample_size: int = 1024) -> str:
        """
        Detect the most likely delimiter for a CSV file.
        
        Args:
            filepath: Path to the CSV file
            sample_size: Number of bytes to sample for detection
            
        Returns:
            Detected delimiter
        """
        common_delimiters = [',', ';', '\t', '|', ':']
        
        try:
            with open(filepath, 'r', encoding=self.encoding) as f:
                sample = f.read(sample_size)
            
            # Count occurrences of each delimiter
            delimiter_counts = {}
            for delimiter in common_delimiters:
                count = sample.count(delimiter)
                if count > 0:
                    delimiter_counts[delimiter] = count
            
            if delimiter_counts:
                # Return delimiter with highest count
                return max(delimiter_counts.items(), key=lambda x: x[1])[0]
            else:
                # Default to comma
                return ','
                
        except Exception:
            return ','
    
    def _detect_encoding(self, filepath: str) -> str:
        """
        Detect file encoding.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Detected encoding
        """
        try:
            import chardet
            
            with open(filepath, 'rb') as f:
                sample = f.read(10000)  # Read first 10KB
            
            result = chardet.detect(sample)
            confidence = result.get('confidence', 0)
            
            if confidence > 0.8:
                return result['encoding']
            else:
                return self.encoding  # Fallback to default
                
        except ImportError:
            # chardet not available, use default
            return self.encoding
        except Exception:
            return self.encoding
    
    @handle_data_error
    def load(self, source: str, **kwargs) -> DataFrame:
        """
        Load data from CSV file.
        
        Args:
            source: Path to CSV file
            **kwargs: Additional parameters (override instance parameters)
            
        Returns:
            Loaded DataFrame
        """
        # Merge kwargs with instance parameters
        load_params = {
            'delimiter': self.delimiter,
            'encoding': self.encoding,
            'header': self.header,
            'index_col': self.index_col,
            'skiprows': self.skip_rows,
            'nrows': self.max_rows,
            **self.pandas_kwargs,
            **kwargs
        }
        
        # Auto-detect delimiter if not specified
        if load_params['delimiter'] is None:
            load_params['delimiter'] = self._detect_delimiter(source)
        
        # Auto-detect encoding if default fails
        try:
            # Try with specified encoding first
            delimiter = load_params.pop('delimiter', ',')
            df = pd.read_csv(source, sep=delimiter, **load_params)
        except UnicodeDecodeError:
            # Try with detected encoding
            detected_encoding = self._detect_encoding(source)
            load_params['encoding'] = detected_encoding
            delimiter = load_params.pop('delimiter', ',')
            df = pd.read_csv(source, sep=delimiter, **load_params)
        # Parse dates if requested
        if self.parse_dates:
            df = self._parse_dates(df)
        
        # Infer dtypes if requested
        if self.dtype_inference:
            df = self._infer_dtypes(df)
        
        return df
    
    def _parse_dates(self, df: DataFrame) -> DataFrame:
        """
        Automatically parse date columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with parsed dates
        """
        for col in df.select_dtypes(include=['object']).columns:
            # Try to parse as datetime for a sample
            sample = df[col].dropna().head(100)
            if len(sample) > 0:
                try:
                    pd.to_datetime(sample, errors='raise')
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    continue  # Not a date column
        
        return df
    
    def _infer_dtypes(self, df: DataFrame) -> DataFrame:
        """
        Infer optimal data types.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with optimized dtypes
        """
        # Convert appropriate columns to categorical
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        # Optimize numeric types
        for col in df.select_dtypes(include=['int64']).columns:
            col_min = df[col].min()
            col_max = df[col].max()
            
            if col_min >= np.iinfo(np.int8).min and col_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif col_min >= np.iinfo(np.int16).min and col_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif col_min >= np.iinfo(np.int32).min and col_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        
        for col in df.select_dtypes(include=['float64']).columns:
            if df[col].dtype == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')
        
        return df
    
    def validate_source(self, source: str) -> bool:
        """Validate CSV file accessibility and format."""
        try:
            path = Path(source)
            if not path.exists():
                return False
            
            if not path.is_file():
                return False
            
            # Try to read first few lines
            with open(source, 'r', encoding=self.encoding) as f:
                f.readline()  # Try to read one line
            
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported file formats."""
        return ['csv', 'tsv', 'txt']


class ExcelLoader(DataLoader):
    """
    Loader for Excel files (.xlsx, .xls) with sheet selection and range support.
    
    Handles multiple sheets, cell ranges, and Excel-specific formatting
    with robust error handling and validation.
    """
    
    def __init__(self,
                 sheet_name: Union[str, int, List] = 0,
                 header: Union[int, List[int]] = 0,
                 index_col: Optional[Union[int, str]] = None,
                 usecols: Optional[Union[str, List]] = None,
                 skip_rows: Optional[int] = None,
                 max_rows: Optional[int] = None,
                 **pandas_kwargs):
        """
        Initialize Excel loader.
        
        Args:
            sheet_name: Sheet name, index, or list of sheets to read
            header: Row number(s) to use as column names
            index_col: Column to use as row index
            usecols: Columns to read (by name or index)
            skip_rows: Number of rows to skip at start
            max_rows: Maximum number of rows to read
            **pandas_kwargs: Additional arguments for pandas.read_excel
        """
        self.sheet_name = sheet_name
        self.header = header
        self.index_col = index_col
        self.usecols = usecols
        self.skip_rows = skip_rows
        self.max_rows = max_rows
        self.pandas_kwargs = pandas_kwargs
    
    @handle_data_error
    def load(self, source: str, **kwargs) -> DataFrame:
        """
        Load data from Excel file.
        
        Args:
            source: Path to Excel file
            **kwargs: Additional parameters
            
        Returns:
            Loaded DataFrame or dict of DataFrames if multiple sheets
        """
        load_params = {
            'sheet_name': self.sheet_name,
            'header': self.header,
            'index_col': self.index_col,
            'usecols': self.usecols,
            'skiprows': self.skip_rows,
            'nrows': self.max_rows,
            **self.pandas_kwargs,
            **kwargs
        }
        
        try:
            df = pd.read_excel(source, **load_params)
            
            # If multiple sheets, combine them or return dict
            if isinstance(df, dict):
                if len(df) == 1:
                    # Single sheet, return DataFrame
                    return list(df.values())[0]
                else:
                    # Multiple sheets - for now, return first sheet
                    # In future, could implement sheet combination strategies
                    return list(df.values())[0]
            
            return df
            
        except Exception as e:
            raise DataLoadError(f"Failed to load Excel file: {str(e)}") from e
    
    def get_sheet_names(self, source: str) -> List[str]:
        """
        Get names of all sheets in Excel file.
        
        Args:
            source: Path to Excel file
            
        Returns:
            List of sheet names
        """
        try:
            with pd.ExcelFile(source) as xls:
                return xls.sheet_names
        except Exception as e:
            raise DataLoadError(f"Failed to get sheet names: {str(e)}") from e
    
    def validate_source(self, source: str) -> bool:
        """Validate Excel file accessibility."""
        try:
            path = Path(source)
            if not path.exists() or not path.is_file():
                return False
            
            # Try to open with pandas
            with pd.ExcelFile(source) as xls:
                pass  # Just check if we can open it
            
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported file formats."""
        return ['xlsx', 'xls', 'xlsm']


class JSONLoader(DataLoader):
    """
    Loader for JSON files with various structure support.
    
    Handles flat JSON, nested JSON, and JSON Lines formats
    with normalization and flattening options.
    """
    
    def __init__(self,
                 lines: bool = False,
                 normalize: bool = True,
                 max_level: Optional[int] = None,
                 **pandas_kwargs):
        """
        Initialize JSON loader.
        
        Args:
            lines: Whether file is in JSON Lines format
            normalize: Whether to normalize nested JSON
            max_level: Maximum nesting level to normalize
            **pandas_kwargs: Additional arguments for pandas functions
        """
        self.lines = lines
        self.normalize = normalize
        self.max_level = max_level
        self.pandas_kwargs = pandas_kwargs
    
    @handle_data_error
    def load(self, source: str, **kwargs) -> DataFrame:
        """
        Load data from JSON file.
        
        Args:
            source: Path to JSON file
            **kwargs: Additional parameters
            
        Returns:
            Loaded DataFrame
        """
        load_params = {
            'lines': self.lines,
            **self.pandas_kwargs,
            **kwargs
        }
        
        try:
            if self.lines:
                df = pd.read_json(source, lines=True, **load_params)
            else:
                df = pd.read_json(source, **load_params)
            
            # Normalize nested JSON if requested
            if self.normalize and any(df.dtypes == 'object'):
                df = self._normalize_nested_columns(df)
            
            return df
            
        except Exception as e:
            raise DataLoadError(f"Failed to load JSON file: {str(e)}") from e
    
    def _normalize_nested_columns(self, df: DataFrame) -> DataFrame:
        """
        Normalize nested JSON columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with normalized nested columns
        """
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains dict-like objects
                sample = df[col].dropna().head(10)
                if len(sample) > 0 and isinstance(sample.iloc[0], dict):
                    try:
                        # Normalize this column
                        normalized = pd.json_normalize(
                            df[col].dropna().tolist(),
                            max_level=self.max_level
                        )
                        
                        # Add normalized columns to main DataFrame
                        for norm_col in normalized.columns:
                            new_col_name = f"{col}_{norm_col}"
                            df[new_col_name] = normalized[norm_col]
                        
                        # Drop original nested column
                        df = df.drop(columns=[col])
                        
                    except Exception:
                        # If normalization fails, keep original column
                        continue
        
        return df
    
    def validate_source(self, source: str) -> bool:
        """Validate JSON file accessibility and format."""
        try:
            path = Path(source)
            if not path.exists() or not path.is_file():
                return False
            
            # Try to parse a small sample
            with open(source, 'r') as f:
                if self.lines:
                    # For JSON Lines, try to parse first line
                    first_line = f.readline().strip()
                    if first_line:
                        import json
                        json.loads(first_line)
                else:
                    # For regular JSON, try to parse first 1000 chars
                    sample = f.read(1000)
                    import json
                    json.loads(sample)
            
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported file formats."""
        return ['json', 'jsonl', 'ndjson']


class ParquetLoader(DataLoader):
    """
    Loader for Parquet files with column selection and filtering.
    
    Efficient loading of columnar data with optional column subset
    and basic filtering capabilities.
    """
    
    def __init__(self,
                 columns: Optional[List[str]] = None,
                 use_pandas_metadata: bool = True,
                 **pandas_kwargs):
        """
        Initialize Parquet loader.
        
        Args:
            columns: Specific columns to load
            use_pandas_metadata: Whether to use pandas metadata
            **pandas_kwargs: Additional arguments for pandas.read_parquet
        """
        self.columns = columns
        self.use_pandas_metadata = use_pandas_metadata
        self.pandas_kwargs = pandas_kwargs
    
    @handle_data_error
    def load(self, source: str, **kwargs) -> DataFrame:
        """
        Load data from Parquet file.
        
        Args:
            source: Path to Parquet file
            **kwargs: Additional parameters
            
        Returns:
            Loaded DataFrame
        """
        load_params = {
            'columns': self.columns,
            'use_pandas_metadata': self.use_pandas_metadata,
            **self.pandas_kwargs,
            **kwargs
        }
        
        try:
            df = pd.read_parquet(source, **load_params)
            return df
            
        except Exception as e:
            raise DataLoadError(f"Failed to load Parquet file: {str(e)}") from e
    
    def validate_source(self, source: str) -> bool:
        """Validate Parquet file accessibility."""
        try:
            path = Path(source)
            if not path.exists() or not path.is_file():
                return False
            
            # Try to read metadata
            import pyarrow.parquet as pq
            pq.read_metadata(source)
            
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported file formats."""
        return ['parquet', 'pq']


class AutoLoader(DataLoader):
    """
    Automatic data loader that detects file format and uses appropriate loader.
    
    Provides a unified interface for loading various file formats
    with automatic format detection and optimal loader selection.
    """
    
    def __init__(self):
        """Initialize auto loader with all available loaders."""
        self.loaders = {
            'csv': CSVLoader(),
            'tsv': CSVLoader(delimiter='\t'),
            'txt': CSVLoader(),
            'xlsx': ExcelLoader(),
            'xls': ExcelLoader(),
            'xlsm': ExcelLoader(),
            'json': JSONLoader(),
            'jsonl': JSONLoader(lines=True),
            'ndjson': JSONLoader(lines=True),
            'parquet': ParquetLoader(),
            'pq': ParquetLoader(),
        }
    
    def _detect_format(self, source: str) -> str:
        """
        Detect file format from extension.
        
        Args:
            source: File path
            
        Returns:
            Detected format
        """
        path = Path(source)
        extension = path.suffix.lower().lstrip('.')
        
        # Handle special cases
        if extension in ['txt', 'dat']:
            # Try to detect if it's CSV-like
            try:
                with open(source, 'r') as f:
                    first_line = f.readline()
                    if ',' in first_line or ';' in first_line or '\t' in first_line:
                        return 'csv'
            except:
                pass
            return 'txt'
        
        if extension in self.loaders:
            return extension
        
        # Default to CSV for unknown text files
        return 'csv'
    
    @handle_data_error
    def load(self, source: str, format: Optional[str] = None, **kwargs) -> DataFrame:
        """
        Load data with automatic format detection.
        
        Args:
            source: Path to data file
            format: Optional format override
            **kwargs: Additional parameters for the specific loader
            
        Returns:
            Loaded DataFrame
        """
        # Determine format
        if format is None:
            format = self._detect_format(source)
        
        if format not in self.loaders:
            raise DataLoadError(f"Unsupported format: {format}")
        
        # Use appropriate loader
        loader = self.loaders[format]
        return loader.load(source, **kwargs)
    
    def validate_source(self, source: str) -> bool:
        """Validate data source accessibility."""
        try:
            format = self._detect_format(source)
            loader = self.loaders.get(format)
            
            if loader is None:
                return False
            
            return loader.validate_source(source)
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get all supported file formats."""
        formats = set()
        for loader in self.loaders.values():
            formats.update(loader.get_supported_formats())
        return sorted(list(formats))
    
    def get_file_info(self, source: str) -> Dict[str, Any]:
        """
        Get information about the data file.
        
        Args:
            source: Path to data file
            
        Returns:
            Dictionary with file information
        """
        path = Path(source)
        
        info = {
            'path': str(path.absolute()),
            'name': path.name,
            'extension': path.suffix.lower(),
            'size_bytes': path.stat().st_size if path.exists() else 0,
            'size_mb': (path.stat().st_size / (1024 * 1024)) if path.exists() else 0,
            'exists': path.exists(),
            'is_file': path.is_file() if path.exists() else False,
            'detected_format': self._detect_format(source),
            'is_supported': self.validate_source(source)
        }
        
        # Try to get additional info by loading a sample
        if info['is_supported'] and info['size_mb'] < 100:  # Only for smaller files
            try:
                # Load just the first few rows for info
                sample_df = self.load(source, nrows=10)
                info.update({
                    'columns': list(sample_df.columns),
                    'column_count': len(sample_df.columns),
                    'dtypes': sample_df.dtypes.to_dict(),
                    'sample_shape': sample_df.shape
                })
            except Exception:
                pass  # Don't fail if we can't get sample info
        
        return info


class DatabaseLoader(DataLoader):
    """
    Loader for database connections using SQL queries.
    
    Supports various database engines through SQLAlchemy
    with connection pooling and query optimization.
    """
    
    def __init__(self,
                 connection_string: str,
                 query: Optional[str] = None,
                 table_name: Optional[str] = None,
                 chunksize: Optional[int] = None,
                 **pandas_kwargs):
        """
        Initialize database loader.
        
        Args:
            connection_string: Database connection string
            query: SQL query to execute
            table_name: Table name to read (alternative to query)
            chunksize: Number of rows to read at a time
            **pandas_kwargs: Additional arguments for pandas.read_sql
        """
        self.connection_string = connection_string
        self.query = query
        self.table_name = table_name
        self.chunksize = chunksize
        self.pandas_kwargs = pandas_kwargs
    
    @handle_data_error
    def load(self, source: str = None, **kwargs) -> DataFrame:
        """
        Load data from database.
        
        Args:
            source: Optional query override
            **kwargs: Additional parameters
            
        Returns:
            Loaded DataFrame
        """
        try:
            import sqlalchemy
        except ImportError:
            raise DataLoadError("SQLAlchemy is required for database loading")
        
        # Determine what to query
        sql_query = source or self.query
        if sql_query is None and self.table_name:
            sql_query = f"SELECT * FROM {self.table_name}"
        
        if sql_query is None:
            raise DataLoadError("No query or table name specified")
        
        load_params = {
            'chunksize': self.chunksize,
            **self.pandas_kwargs,
            **kwargs
        }
        
        try:
            engine = sqlalchemy.create_engine(self.connection_string)
            
            if self.chunksize:
                # Return iterator for large datasets
                return pd.read_sql(sql_query, engine, **load_params)
            else:
                # Return DataFrame directly
                df = pd.read_sql(sql_query, engine, **load_params)
                engine.dispose()
                return df
                
        except Exception as e:
            raise DataLoadError(f"Failed to load from database: {str(e)}") from e
    
    def validate_source(self, source: str = None) -> bool:
        """Validate database connection."""
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(self.connection_string)
            
            # Try a simple query
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            
            engine.dispose()
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported database types."""
        return ['sql', 'sqlite', 'postgresql', 'mysql', 'oracle', 'mssql']


class URLLoader(DataLoader):
    """
    Loader for data from URLs with automatic format detection.
    
    Downloads and loads data from web sources with caching
    and format detection capabilities.
    """
    
    def __init__(self,
                 cache_dir: Optional[str] = None,
                 timeout: int = 30,
                 verify_ssl: bool = True,
                 **loader_kwargs):
        """
        Initialize URL loader.
        
        Args:
            cache_dir: Directory for caching downloaded files
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            **loader_kwargs: Arguments for the underlying loader
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.loader_kwargs = loader_kwargs
        self.auto_loader = AutoLoader()
    
    def _download_file(self, url: str) -> str:
        """
        Download file from URL.
        
        Args:
            url: URL to download from
            
        Returns:
            Path to downloaded file
        """
        try:
            import requests
        except ImportError:
            raise DataLoadError("requests library is required for URL loading")
        
        # Generate cache filename
        parsed_url = urllib.parse.urlparse(url)
        filename = Path(parsed_url.path).name or "downloaded_data"
        
        if self.cache_dir:
            self.cache_dir.mkdir(exist_ok=True)
            cache_path = self.cache_dir / filename
            
            # Check if cached file exists and is recent
            if cache_path.exists():
                # For now, always use cached file
                # In future, could add cache expiration logic
                return str(cache_path)
        else:
            # Use temporary file
            import tempfile
            cache_path = Path(tempfile.mktemp(suffix=f"_{filename}"))
        
        # Download file
        try:
            response = requests.get(
                url, 
                timeout=self.timeout, 
                verify=self.verify_ssl,
                stream=True
            )
            response.raise_for_status()
            
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(cache_path)
            
        except Exception as e:
            raise DataLoadError(f"Failed to download from URL: {str(e)}") from e
    
    @handle_data_error
    def load(self, source: str, **kwargs) -> DataFrame:
        """
        Load data from URL.
        
        Args:
            source: URL to load from
            **kwargs: Additional parameters
            
        Returns:
            Loaded DataFrame
        """
        # Download file
        local_path = self._download_file(source)
        
        # Load using auto loader
        merged_kwargs = {**self.loader_kwargs, **kwargs}
        return self.auto_loader.load(local_path, **merged_kwargs)
    
    def validate_source(self, source: str) -> bool:
        """Validate URL accessibility."""
        try:
            import requests
            response = requests.head(
                source, 
                timeout=self.timeout, 
                verify=self.verify_ssl
            )
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported formats (same as AutoLoader)."""
        return self.auto_loader.get_supported_formats()


# Factory function for easy loader creation
def create_loader(source: str, **kwargs) -> DataLoader:
    """
    Create appropriate loader based on source type.
    
    Args:
        source: Data source (file path, URL, etc.)
        **kwargs: Additional parameters for the loader
        
    Returns:
        Configured data loader
    """
    # Check if it's a URL
    if source.startswith(('http://', 'https://')):
        return URLLoader(**kwargs)
    
    # Check if it's a database connection string
    if '://' in source and not source.startswith(('http://', 'https://')):
        return DatabaseLoader(connection_string=source, **kwargs)
    
    # Otherwise, use auto loader for files
    return AutoLoader()


# Convenience function for direct loading
def load_data(source: str, **kwargs) -> DataFrame:
    """
    Load data from any supported source.
    
    Args:
        source: Data source (file path, URL, connection string)
        **kwargs: Additional parameters
        
    Returns:
        Loaded DataFrame
    """
    loader = create_loader(source, **kwargs)
    return loader.load(source, **kwargs)