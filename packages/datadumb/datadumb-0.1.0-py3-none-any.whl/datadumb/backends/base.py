"""Abstract base class for backend adapters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..core.models import LoadingParameters


class BackendAdapter(ABC):
    """Abstract base class for DataFrame backend adapters."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the backend (e.g., 'pandas', 'polars')."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend library is available.
        
        Returns:
            True if the backend can be used, False otherwise
        """
        pass
    
    @abstractmethod
    def load_csv(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a CSV file using this backend.
        
        Args:
            file_path: Path to the CSV file
            parameters: Loading parameters
            
        Returns:
            DataFrame object from this backend
            
        Raises:
            BackendNotAvailableError: If backend library is not available
            ValueError: If parameters are invalid for this backend
        """
        pass
    
    @abstractmethod
    def load_excel(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load an Excel file using this backend.
        
        Args:
            file_path: Path to the Excel file
            parameters: Loading parameters
            
        Returns:
            DataFrame object from this backend
            
        Raises:
            BackendNotAvailableError: If backend library is not available
            ValueError: If parameters are invalid for this backend
        """
        pass
    
    @abstractmethod
    def load_parquet(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a Parquet file using this backend.
        
        Args:
            file_path: Path to the Parquet file
            parameters: Loading parameters
            
        Returns:
            DataFrame object from this backend
            
        Raises:
            BackendNotAvailableError: If backend library is not available
            ValueError: If parameters are invalid for this backend
        """
        pass