"""Core components for the smart data loader."""

from .interfaces import FileLoader, BackendAdapter
from .models import FileFormat, LoadingParameters, LoadingContext, DetectionResult
from .orchestrator import LoadingOrchestrator
from .exceptions import (
    DataLoaderError,
    FormatDetectionError,
    ParameterInferenceError,
    BackendNotAvailableError,
    BackendLoadingError,
)

__all__ = [
    "FileLoader",
    "BackendAdapter", 
    "FileFormat",
    "LoadingParameters",
    "LoadingContext",
    "DetectionResult",
    "LoadingOrchestrator",
    "DataLoaderError",
    "FormatDetectionError",
    "ParameterInferenceError",
    "BackendNotAvailableError",
    "BackendLoadingError",
]