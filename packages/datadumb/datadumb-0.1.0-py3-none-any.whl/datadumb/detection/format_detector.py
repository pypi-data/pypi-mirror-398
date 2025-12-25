"""File format detection with extensible registry system."""

import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..core.exceptions import FormatDetectionError, format_error_message
from ..core.interfaces import FormatDetector
from ..core.models import DetectionResult, FileFormat
from ..utils.logging import get_logger


logger = get_logger(__name__)


class ExtensionDetector(FormatDetector):
    """Detects file format based on file extension."""
    
    EXTENSION_MAP = {
        '.csv': FileFormat.CSV,
        '.tsv': FileFormat.CSV,
        '.txt': FileFormat.CSV,
        '.xlsx': FileFormat.EXCEL,
        '.xls': FileFormat.EXCEL,
        '.parquet': FileFormat.PARQUET,
        '.pq': FileFormat.PARQUET,
    }
    
    def detect(self, file_path: Path) -> DetectionResult:
        """Detect format based on file extension."""
        extension = file_path.suffix.lower()
        
        if extension in self.EXTENSION_MAP:
            format_type = self.EXTENSION_MAP[extension]
            confidence = 0.7  # Medium confidence for extension-based detection
            evidence = {"method": "extension", "extension": extension}
            return DetectionResult(format_type, confidence, evidence)
        
        return DetectionResult(FileFormat.UNKNOWN, 0.0, {"method": "extension", "extension": extension})
    
    def supports_format(self, format: FileFormat) -> bool:
        """Check if this detector supports a format."""
        return format in self.EXTENSION_MAP.values()


class ContentDetector(FormatDetector):
    """Detects file format based on content analysis."""
    
    def detect(self, file_path: Path) -> DetectionResult:
        """Detect format based on file content."""
        if not file_path.exists():
            error = FormatDetectionError(
                format_error_message("file_not_found", file_path=file_path),
                file_path=str(file_path)
            )
            logger.error(f"File not found during content detection: {file_path}")
            raise error
        
        try:
            logger.debug(f"Starting content-based format detection for {file_path}")
            
            # Read first few bytes to analyze content
            with open(file_path, 'rb') as f:
                header = f.read(1024)
            
            # Check for Parquet magic bytes
            if header.startswith(b'PAR1'):
                logger.debug("Detected Parquet format via magic bytes")
                return DetectionResult(
                    FileFormat.PARQUET, 
                    0.95, 
                    {"method": "content", "magic_bytes": "PAR1"}
                )
            
            # Check for Excel file signatures
            if (header.startswith(b'PK\x03\x04') or  # XLSX (ZIP-based)
                header.startswith(b'\xd0\xcf\x11\xe0')):  # XLS (OLE2-based)
                logger.debug("Detected Excel format via binary signature")
                return DetectionResult(
                    FileFormat.EXCEL, 
                    0.9, 
                    {"method": "content", "signature": "excel_binary"}
                )
            
            # Try to decode as text for CSV detection
            try:
                text_content = header.decode('utf-8', errors='ignore')
                if self._looks_like_csv(text_content):
                    logger.debug("Detected CSV format via content analysis")
                    return DetectionResult(
                        FileFormat.CSV, 
                        0.8, 
                        {"method": "content", "analysis": "csv_structure"}
                    )
            except UnicodeDecodeError:
                logger.debug("Failed to decode content as UTF-8")
                pass
            
            logger.debug("Could not determine format from content analysis")
            return DetectionResult(FileFormat.UNKNOWN, 0.0, {"method": "content"})
            
        except (IOError, OSError) as e:
            error = FormatDetectionError(
                f"Cannot read file {file_path}: {e}",
                file_path=str(file_path)
            )
            logger.error(f"IO error during content detection: {e}")
            raise error
    
    def _looks_like_csv(self, text: str) -> bool:
        """Analyze text content to determine if it looks like CSV."""
        lines = text.strip().split('\n')[:5]  # Check first 5 lines
        
        if not lines:
            return False
        
        # Look for common CSV patterns
        common_separators = [',', ';', '\t', '|']
        
        for separator in common_separators:
            if self._has_consistent_columns(lines, separator):
                return True
        
        return False
    
    def _has_consistent_columns(self, lines: List[str], separator: str) -> bool:
        """Check if lines have consistent number of columns with given separator."""
        if len(lines) < 2:
            return False
        
        column_counts = [len(line.split(separator)) for line in lines if line.strip()]
        
        # Need at least 2 columns and consistent count across lines
        return len(set(column_counts)) == 1 and column_counts[0] >= 2
    
    def supports_format(self, format: FileFormat) -> bool:
        """Check if this detector supports a format."""
        return format in {FileFormat.CSV, FileFormat.EXCEL, FileFormat.PARQUET}


class FormatDetectorRegistry:
    """Registry for managing format detectors with extensible plugin system."""
    
    def __init__(self):
        self._detectors: List[FormatDetector] = []
        self._format_support: Dict[FileFormat, Set[FormatDetector]] = {}
        
        # Register default detectors
        self.register(ContentDetector())
        self.register(ExtensionDetector())
    
    def register(self, detector: FormatDetector) -> None:
        """Register a new format detector.
        
        Args:
            detector: FormatDetector instance to register
        """
        if detector not in self._detectors:
            self._detectors.append(detector)
            
            # Update format support mapping
            for format_type in FileFormat:
                if detector.supports_format(format_type):
                    if format_type not in self._format_support:
                        self._format_support[format_type] = set()
                    self._format_support[format_type].add(detector)
    
    def unregister(self, detector: FormatDetector) -> None:
        """Unregister a format detector.
        
        Args:
            detector: FormatDetector instance to unregister
        """
        if detector in self._detectors:
            self._detectors.remove(detector)
            
            # Update format support mapping
            for format_set in self._format_support.values():
                format_set.discard(detector)
    
    def detect_format(self, file_path: Path) -> DetectionResult:
        """Detect file format using all registered detectors.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            DetectionResult with highest confidence format
            
        Raises:
            FormatDetectionError: If no format can be determined
        """
        if not file_path.exists():
            error = FormatDetectionError(
                format_error_message("file_not_found", file_path=file_path),
                file_path=str(file_path)
            )
            logger.error(f"File not found during format detection: {file_path}")
            raise error
        
        logger.debug(f"Starting format detection for {file_path} using {len(self._detectors)} detectors")
        
        results = []
        detector_errors = []
        
        # Run all detectors and collect results
        for detector in self._detectors:
            try:
                result = detector.detect(file_path)
                if result.format != FileFormat.UNKNOWN:
                    results.append(result)
                    logger.debug(f"Detector {type(detector).__name__} found {result.format.value} "
                               f"(confidence: {result.confidence:.2f})")
            except Exception as e:
                # Log detector failures but continue with other detectors
                detector_errors.append(f"{type(detector).__name__}: {e}")
                logger.debug(f"Detector {type(detector).__name__} failed: {e}")
                continue
        
        if detector_errors:
            logger.debug(f"Some detectors failed: {'; '.join(detector_errors)}")
        
        if not results:
            supported_formats = [fmt.value for fmt in FileFormat if fmt != FileFormat.UNKNOWN]
            error = FormatDetectionError(
                format_error_message("format_detection_failed", file_path=file_path),
                file_path=str(file_path),
                supported_formats=supported_formats,
                detection_evidence={"detector_errors": detector_errors}
            )
            logger.error(f"No detectors could determine format for {file_path}")
            raise error
        
        # Return result with highest confidence
        # Content-based detection takes priority over extension-based
        results.sort(key=lambda r: (r.confidence, r.evidence.get("method") == "content"), reverse=True)
        best_result = results[0]
        
        logger.info(f"Format detection completed for {file_path}: {best_result.format.value} "
                   f"(confidence: {best_result.confidence:.2f})")
        
        return best_result
    
    def get_supported_formats(self) -> List[FileFormat]:
        """Get list of all supported formats.
        
        Returns:
            List of supported FileFormat values
        """
        return [fmt for fmt in self._format_support.keys() if fmt != FileFormat.UNKNOWN]
    
    def get_detectors_for_format(self, format: FileFormat) -> List[FormatDetector]:
        """Get detectors that support a specific format.
        
        Args:
            format: FileFormat to query
            
        Returns:
            List of FormatDetector instances supporting the format
        """
        return list(self._format_support.get(format, set()))


# Global registry instance
_registry = FormatDetectorRegistry()


def get_format_detector() -> FormatDetectorRegistry:
    """Get the global format detector registry.
    
    Returns:
        FormatDetectorRegistry instance
    """
    return _registry


def detect_file_format(file_path: Path) -> DetectionResult:
    """Convenience function to detect file format.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        DetectionResult with format and confidence information
    """
    return _registry.detect_format(file_path)