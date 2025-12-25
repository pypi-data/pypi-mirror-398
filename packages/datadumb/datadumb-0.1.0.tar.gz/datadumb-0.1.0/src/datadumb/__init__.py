"""Smart data loader with automatic format detection and parameter inference."""

import os
from pathlib import Path
from typing import Any, Optional, Union

from .core.models import LoadingParameters
from .core.orchestrator import get_loading_orchestrator
from .utils.logging import configure_logging, get_logger

__version__ = "0.1.0"

# Configure default logging
configure_logging()

# Get logger for this module
logger = get_logger(__name__)


def pandas_load(
    file_path: Union[str, Path],
    parameters: Optional[LoadingParameters] = None,
    debug_mode: bool = False
) -> Any:
    """Load data into a pandas DataFrame with automatic format detection.
    
    This function automatically detects the file format (CSV, Excel, Parquet) and
    infers optimal loading parameters like CSV separators and header locations.
    It provides a unified interface for loading various data formats into pandas
    DataFrames without manual configuration.
    
    Args:
        file_path: Path to the data file to load. Can be a string or Path object.
        parameters: Optional pre-determined loading parameters. If not provided,
                   parameters will be automatically detected and inferred.
        debug_mode: Enable debug logging to see detailed information about
                   format detection and parameter inference process.
    
    Returns:
        pandas.DataFrame: The loaded data as a pandas DataFrame.
    
    Raises:
        FileNotFoundError: If the specified file does not exist.
        FormatDetectionError: If the file format cannot be determined or is unsupported.
        ParameterInferenceError: If loading parameters cannot be reliably inferred.
        BackendNotAvailableError: If pandas is not installed or available.
        BackendLoadingError: If DataFrame creation fails due to backend-specific issues.
        DataLoaderError: For other unexpected errors during the loading process.
    
    Examples:
        Basic usage with automatic detection:
        
        >>> import datadumb
        >>> df = datadumb.pandas_load('data.csv')
        >>> print(df.head())
        
        Loading with debug information:
        
        >>> df = datadumb.pandas_load('data.xlsx', debug_mode=True)
        
        Loading with custom parameters:
        
        >>> from datadumb.core.models import LoadingParameters, FileFormat
        >>> params = LoadingParameters(
        ...     format=FileFormat.CSV,
        ...     separator=';',
        ...     skip_rows=2
        ... )
        >>> df = datadumb.pandas_load('data.csv', parameters=params)
        
        Handling different file formats:
        
        >>> # CSV files - automatic separator detection
        >>> csv_df = datadumb.pandas_load('sales.csv')
        >>> 
        >>> # Excel files - automatic sheet detection
        >>> excel_df = datadumb.pandas_load('report.xlsx')
        >>> 
        >>> # Parquet files - optimized loading
        >>> parquet_df = datadumb.pandas_load('large_dataset.parquet')
    
    Note:
        This function requires pandas to be installed. Install it with:
        `uv add pandas` or `pip install pandas`
        
        The function uses the same detection and inference logic as polars_load(),
        ensuring consistent behavior across different DataFrame backends.
    """
    # Convert string path to Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Configure logging if debug mode is enabled
    if debug_mode:
        configure_logging(enable_debug=True)
        logger.debug(f"pandas_load called with file_path={file_path}, debug_mode={debug_mode}")
    
    # Get orchestrator and load with pandas backend
    orchestrator = get_loading_orchestrator(debug_mode=debug_mode)
    return orchestrator.load_dataframe(file_path, "pandas", parameters)


def polars_load(
    file_path: Union[str, Path],
    parameters: Optional[LoadingParameters] = None,
    debug_mode: bool = False
) -> Any:
    """Load data into a polars DataFrame with automatic format detection.
    
    This function automatically detects the file format (CSV, Excel, Parquet) and
    infers optimal loading parameters like CSV separators and header locations.
    It provides a unified interface for loading various data formats into polars
    DataFrames without manual configuration.
    
    Args:
        file_path: Path to the data file to load. Can be a string or Path object.
        parameters: Optional pre-determined loading parameters. If not provided,
                   parameters will be automatically detected and inferred.
        debug_mode: Enable debug logging to see detailed information about
                   format detection and parameter inference process.
    
    Returns:
        polars.DataFrame: The loaded data as a polars DataFrame.
    
    Raises:
        FileNotFoundError: If the specified file does not exist.
        FormatDetectionError: If the file format cannot be determined or is unsupported.
        ParameterInferenceError: If loading parameters cannot be reliably inferred.
        BackendNotAvailableError: If polars is not installed or available.
        BackendLoadingError: If DataFrame creation fails due to backend-specific issues.
        DataLoaderError: For other unexpected errors during the loading process.
    
    Examples:
        Basic usage with automatic detection:
        
        >>> import datadumb
        >>> df = datadumb.polars_load('data.csv')
        >>> print(df.head())
        
        Loading with debug information:
        
        >>> df = datadumb.polars_load('data.xlsx', debug_mode=True)
        
        Loading with custom parameters:
        
        >>> from datadumb.core.models import LoadingParameters, FileFormat
        >>> params = LoadingParameters(
        ...     format=FileFormat.CSV,
        ...     separator=';',
        ...     skip_rows=2
        ... )
        >>> df = datadumb.polars_load('data.csv', parameters=params)
        
        Handling different file formats:
        
        >>> # CSV files - automatic separator detection
        >>> csv_df = datadumb.polars_load('sales.csv')
        >>> 
        >>> # Excel files - automatic sheet detection
        >>> excel_df = datadumb.polars_load('report.xlsx')
        >>> 
        >>> # Parquet files - optimized loading
        >>> parquet_df = datadumb.polars_load('large_dataset.parquet')
    
    Note:
        This function requires polars to be installed. Install it with:
        `uv add polars` or `pip install polars`
        
        The function uses the same detection and inference logic as pandas_load(),
        ensuring consistent behavior across different DataFrame backends.
    """
    # Convert string path to Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Configure logging if debug mode is enabled
    if debug_mode:
        configure_logging(enable_debug=True)
        logger.debug(f"polars_load called with file_path={file_path}, debug_mode={debug_mode}")
    
    # Get orchestrator and load with polars backend
    orchestrator = get_loading_orchestrator(debug_mode=debug_mode)
    return orchestrator.load_dataframe(file_path, "polars", parameters)


__all__ = ["pandas_load", "polars_load"]
