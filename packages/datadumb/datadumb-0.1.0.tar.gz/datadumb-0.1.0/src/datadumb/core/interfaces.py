"""Core protocol definitions for the smart data loader."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .models import FileFormat, LoadingParameters, DetectionResult


@runtime_checkable
class FileLoader(Protocol):
    """Protocol for file loading components."""
    
    def detect_format(self, file_path: Path) -> DetectionResult:
        """Detect the format of a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            DetectionResult containing format and confidence information
        """
        ...
    
    def infer_parameters(self, file_path: Path, format: FileFormat) -> LoadingParameters:
        """Infer loading parameters for a file.
        
        Args:
            file_path: Path to the file to analyze
            format: Detected file format
            
        Returns:
            LoadingParameters with inferred settings
        """
        ...
    
    def load_dataframe(self, file_path: Path, parameters: LoadingParameters, backend: str) -> Any:
        """Load a file into a DataFrame.
        
        Args:
            file_path: Path to the file to load
            parameters: Loading parameters to use
            backend: Backend library to use ('pandas' or 'polars')
            
        Returns:
            DataFrame object from the specified backend
        """
        ...


@runtime_checkable
class BackendAdapter(Protocol):
    """Protocol for DataFrame backend adapters."""
    
    @property
    def name(self) -> str:
        """Name of the backend (e.g., 'pandas', 'polars')."""
        ...
    
    def is_available(self) -> bool:
        """Check if the backend library is available.
        
        Returns:
            True if the backend can be used, False otherwise
        """
        ...
    
    def load_csv(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a CSV file using this backend.
        
        Args:
            file_path: Path to the CSV file
            parameters: Loading parameters
            
        Returns:
            DataFrame object from this backend
        """
        ...
    
    def load_excel(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load an Excel file using this backend.
        
        Args:
            file_path: Path to the Excel file
            parameters: Loading parameters
            
        Returns:
            DataFrame object from this backend
        """
        ...
    
    def load_parquet(self, file_path: Path, parameters: LoadingParameters) -> Any:
        """Load a Parquet file using this backend.
        
        Args:
            file_path: Path to the Parquet file
            parameters: Loading parameters
            
        Returns:
            DataFrame object from this backend
        """
        ...


class FormatDetector(ABC):
    """Abstract base class for format detection."""
    
    @abstractmethod
    def detect(self, file_path: Path) -> DetectionResult:
        """Detect the format of a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            DetectionResult with format and confidence
        """
        pass
    
    @abstractmethod
    def supports_format(self, format: FileFormat) -> bool:
        """Check if this detector supports a format.
        
        Args:
            format: File format to check
            
        Returns:
            True if format is supported, False otherwise
        """
        pass


class ParameterInferrer(ABC):
    """Abstract base class for parameter inference."""
    
    @abstractmethod
    def infer(self, file_path: Path, format: FileFormat) -> LoadingParameters:
        """Infer loading parameters for a file.
        
        Args:
            file_path: Path to the file to analyze
            format: Detected file format
            
        Returns:
            LoadingParameters with inferred settings
        """
        pass
    
    @abstractmethod
    def supports_format(self, format: FileFormat) -> bool:
        """Check if this inferrer supports a format.
        
        Args:
            format: File format to check
            
        Returns:
            True if format is supported, False otherwise
        """
        pass