"""Polars backend adapter implementation."""

from pathlib import Path
from typing import Any

from .base import BackendAdapter
from ..core.models import LoadingParameters, FileFormat
from ..core.exceptions import BackendNotAvailableError, BackendLoadingError


class PolarsAdapter(BackendAdapter):
    """Adapter for polars DataFrame backend."""
    
    @property
    def name(self) -> str:
        """Name of the backend."""
        return "polars"
    
    def is_available(self) -> bool:
        """Check if polars is available.
        
        Returns:
            True if polars can be imported, False otherwise
        """
        try:
            import polars
            return True
        except ImportError:
            return False
    
    def _ensure_available(self) -> None:
        """Ensure polars is available, raise error if not."""
        if not self.is_available():
            raise BackendNotAvailableError(
                backend="polars",
                install_command="uv add polars"
            )
    
    def load_csv(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a CSV file using polars.
        
        Args:
            file_path: Path to the CSV file
            parameters: Loading parameters
            
        Returns:
            polars DataFrame
            
        Raises:
            BackendNotAvailableError: If polars is not available
            BackendLoadingError: If loading fails
        """
        self._ensure_available()
        
        try:
            import polars as pl
            
            # Build polars-specific parameters
            read_kwargs = {
                "source": str(file_path),
                "encoding": parameters.encoding,
            }
            
            # Add separator if specified
            if parameters.separator:
                read_kwargs["separator"] = parameters.separator
            
            # Add skip rows if specified
            if parameters.skip_rows > 0:
                read_kwargs["skip_rows"] = parameters.skip_rows
            
            # Handle header
            read_kwargs["has_header"] = parameters.has_header
            
            # Add any additional parameters (filter out internal evidence parameters)
            filtered_params = {
                k: v for k, v in parameters.additional_params.items()
                if k not in ['separator_evidence', 'validation_evidence', 'alternatives', 'reason']
            }
            read_kwargs.update(filtered_params)
            
            return pl.read_csv(**read_kwargs)
            
        except Exception as e:
            raise BackendLoadingError(
                message=f"Failed to load CSV file with polars: {str(e)}",
                backend="polars",
                original_error=e
            )
    
    def load_excel(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load an Excel file using polars.
        
        Args:
            file_path: Path to the Excel file
            parameters: Loading parameters
            
        Returns:
            polars DataFrame
            
        Raises:
            BackendNotAvailableError: If polars is not available
            BackendLoadingError: If loading fails
        """
        self._ensure_available()
        
        try:
            import polars as pl
            
            # Build polars-specific parameters
            read_kwargs = {
                "source": str(file_path),
                "has_header": parameters.has_header,
            }
            
            # Note: polars read_excel doesn't have skip_rows parameter like CSV
            # Skip rows functionality would need to be handled differently if needed
            
            # Add any additional parameters (filter out internal evidence parameters)
            filtered_params = {
                k: v for k, v in parameters.additional_params.items()
                if k not in ['separator_evidence', 'validation_evidence', 'alternatives', 'reason']
            }
            read_kwargs.update(filtered_params)
            
            return pl.read_excel(**read_kwargs)
            
        except Exception as e:
            raise BackendLoadingError(
                message=f"Failed to load Excel file with polars: {str(e)}",
                backend="polars",
                original_error=e
            )
    
    def load_parquet(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a Parquet file using polars.
        
        Args:
            file_path: Path to the Parquet file
            parameters: Loading parameters
            
        Returns:
            polars DataFrame
            
        Raises:
            BackendNotAvailableError: If polars is not available
            BackendLoadingError: If loading fails
        """
        self._ensure_available()
        
        try:
            import polars as pl
            
            # Build polars-specific parameters
            read_kwargs = {
                "source": str(file_path),
            }
            
            # Add any additional parameters (filter out internal evidence parameters)
            filtered_params = {
                k: v for k, v in parameters.additional_params.items()
                if k not in ['separator_evidence', 'validation_evidence', 'alternatives', 'reason']
            }
            read_kwargs.update(filtered_params)
            
            return pl.read_parquet(**read_kwargs)
            
        except Exception as e:
            raise BackendLoadingError(
                message=f"Failed to load Parquet file with polars: {str(e)}",
                backend="polars",
                original_error=e
            )