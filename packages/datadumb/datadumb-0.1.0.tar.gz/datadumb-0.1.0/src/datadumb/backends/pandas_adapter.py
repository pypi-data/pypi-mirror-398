"""Pandas backend adapter implementation."""

from pathlib import Path
from typing import Any

from .base import BackendAdapter
from ..core.models import LoadingParameters, FileFormat
from ..core.exceptions import BackendNotAvailableError, BackendLoadingError


class PandasAdapter(BackendAdapter):
    """Adapter for pandas DataFrame backend."""
    
    @property
    def name(self) -> str:
        """Name of the backend."""
        return "pandas"
    
    def is_available(self) -> bool:
        """Check if pandas is available.
        
        Returns:
            True if pandas can be imported, False otherwise
        """
        try:
            import pandas
            return True
        except ImportError:
            return False
    
    def _ensure_available(self) -> None:
        """Ensure pandas is available, raise error if not."""
        if not self.is_available():
            raise BackendNotAvailableError(
                backend="pandas",
                install_command="uv add pandas"
            )
    
    def load_csv(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a CSV file using pandas.
        
        Args:
            file_path: Path to the CSV file
            parameters: Loading parameters
            
        Returns:
            pandas DataFrame
            
        Raises:
            BackendNotAvailableError: If pandas is not available
            BackendLoadingError: If loading fails
        """
        self._ensure_available()
        
        try:
            import pandas as pd
            
            # Build pandas-specific parameters
            read_kwargs = {
                "filepath_or_buffer": str(file_path),
                "encoding": parameters.encoding,
            }
            
            # Add separator if specified
            if parameters.separator:
                read_kwargs["sep"] = parameters.separator
            
            # Add skip rows if specified
            if parameters.skip_rows > 0:
                read_kwargs["skiprows"] = parameters.skip_rows
            
            # Handle header
            if not parameters.has_header:
                read_kwargs["header"] = None
            
            # Add any additional parameters (filter out internal evidence parameters)
            filtered_params = {
                k: v for k, v in parameters.additional_params.items()
                if k not in ['separator_evidence', 'validation_evidence', 'alternatives', 'reason']
            }
            read_kwargs.update(filtered_params)
            
            return pd.read_csv(**read_kwargs)
            
        except Exception as e:
            raise BackendLoadingError(
                message=f"Failed to load CSV file with pandas: {str(e)}",
                backend="pandas",
                original_error=e
            )
    
    def load_excel(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load an Excel file using pandas.
        
        Args:
            file_path: Path to the Excel file
            parameters: Loading parameters
            
        Returns:
            pandas DataFrame
            
        Raises:
            BackendNotAvailableError: If pandas is not available
            BackendLoadingError: If loading fails
        """
        self._ensure_available()
        
        try:
            import pandas as pd
            
            # Determine the appropriate engine based on file extension
            file_extension = file_path.suffix.lower()
            if file_extension == '.xls':
                engine = 'xlrd'  # For older Excel files (.xls)
            elif file_extension in ['.xlsx', '.xlsm', '.xlsb']:
                engine = 'openpyxl'  # For newer Excel files (.xlsx, .xlsm, .xlsb)
            else:
                engine = None  # Let pandas auto-detect
            
            # Build pandas-specific parameters
            read_kwargs = {
                "io": str(file_path),
            }
            
            # Add engine if determined
            if engine:
                read_kwargs["engine"] = engine
            
            # Add skip rows if specified
            if parameters.skip_rows > 0:
                read_kwargs["skiprows"] = parameters.skip_rows
            
            # Handle header
            if not parameters.has_header:
                read_kwargs["header"] = None
            
            # Add any additional parameters (filter out internal evidence parameters)
            filtered_params = {
                k: v for k, v in parameters.additional_params.items()
                if k not in ['separator_evidence', 'validation_evidence', 'alternatives', 'reason']
            }
            read_kwargs.update(filtered_params)
            
            return pd.read_excel(**read_kwargs)
            
        except Exception as e:
            raise BackendLoadingError(
                message=f"Failed to load Excel file with pandas: {str(e)}",
                backend="pandas",
                original_error=e
            )
    
    def load_parquet(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a Parquet file using pandas.
        
        Args:
            file_path: Path to the Parquet file
            parameters: Loading parameters
            
        Returns:
            pandas DataFrame
            
        Raises:
            BackendNotAvailableError: If pandas is not available
            BackendLoadingError: If loading fails
        """
        self._ensure_available()
        
        try:
            import pandas as pd
            
            # Build pandas-specific parameters
            read_kwargs = {
                "path": str(file_path),
            }
            
            # Add any additional parameters (filter out internal evidence parameters)
            filtered_params = {
                k: v for k, v in parameters.additional_params.items()
                if k not in ['separator_evidence', 'validation_evidence', 'alternatives', 'reason']
            }
            read_kwargs.update(filtered_params)
            
            return pd.read_parquet(**read_kwargs)
            
        except Exception as e:
            raise BackendLoadingError(
                message=f"Failed to load Parquet file with pandas: {str(e)}",
                backend="pandas",
                original_error=e
            )
