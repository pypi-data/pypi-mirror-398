"""Data models for the smart data loader."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class FileFormat(Enum):
    """Supported file formats."""
    CSV = "csv"
    EXCEL = "excel"
    PARQUET = "parquet"
    UNKNOWN = "unknown"


@dataclass
class LoadingParameters:
    """Parameters for loading data files."""
    format: FileFormat
    separator: Optional[str] = None
    skip_rows: int = 0
    encoding: str = "utf-8"
    has_header: bool = True
    confidence_score: float = 1.0
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        if self.skip_rows < 0:
            raise ValueError("Skip rows must be non-negative")


@dataclass
class LoadingContext:
    """Context information for loading operations."""
    file_path: Path
    parameters: LoadingParameters
    backend: str
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate context after initialization."""
        if self.backend not in ("pandas", "polars"):
            raise ValueError("Backend must be 'pandas' or 'polars'")


@dataclass
class DetectionResult:
    """Result of file format detection."""
    format: FileFormat
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate detection result after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")