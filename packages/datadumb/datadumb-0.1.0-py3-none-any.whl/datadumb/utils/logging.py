"""Logging configuration and utilities for the smart data loader."""

import logging
import sys
from typing import Optional


class DataLoaderFormatter(logging.Formatter):
    """Custom formatter for data loader log messages."""
    
    def __init__(self):
        super().__init__()
        
        # Define format strings for different log levels
        self.formats = {
            logging.DEBUG: "[DEBUG] %(name)s: %(message)s",
            logging.INFO: "[INFO] %(message)s",
            logging.WARNING: "[WARNING] %(message)s",
            logging.ERROR: "[ERROR] %(message)s",
            logging.CRITICAL: "[CRITICAL] %(message)s"
        }
        
        # Default format
        self.default_format = "[%(levelname)s] %(name)s: %(message)s"
    
    def format(self, record):
        """Format log record with appropriate format string."""
        log_format = self.formats.get(record.levelno, self.default_format)
        formatter = logging.Formatter(log_format)
        return formatter.format(record)


def configure_logging(
    level: str = "INFO",
    enable_debug: bool = False,
    log_file: Optional[str] = None
) -> None:
    """Configure logging for the smart data loader.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_debug: Enable debug logging for all data loader modules
        log_file: Optional file path to write logs to
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger for datadumb package
    logger = logging.getLogger("datadumb")
    logger.setLevel(logging.DEBUG if enable_debug else numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(DataLoaderFormatter())
    logger.addHandler(console_handler)
    
    # Create file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance configured for the data loader
    """
    # Ensure the logger is under the datadumb hierarchy
    if not name.startswith("datadumb"):
        name = f"datadumb.{name}"
    
    return logging.getLogger(name)


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    file_path: Optional[str] = None,
    operation: Optional[str] = None,
    suggestions: Optional[list] = None,
    original_error: Optional[Exception] = None
) -> None:
    """Log an error with comprehensive context information.
    
    Args:
        logger: Logger instance to use
        message: Primary error message
        file_path: File path related to the error
        operation: Operation that was being performed
        suggestions: List of suggestions to resolve the error
        original_error: Original exception that caused the error
    """
    # Build context information
    context_parts = []
    
    if operation:
        context_parts.append(f"Operation: {operation}")
    
    if file_path:
        context_parts.append(f"File: {file_path}")
    
    if original_error:
        context_parts.append(f"Underlying error: {type(original_error).__name__}: {original_error}")
    
    # Log the main error message
    logger.error(message)
    
    # Log context information
    if context_parts:
        for context in context_parts:
            logger.error(f"  {context}")
    
    # Log suggestions
    if suggestions:
        logger.error("Suggestions:")
        for suggestion in suggestions:
            logger.error(f"  - {suggestion}")


def log_parameter_inference_warning(
    logger: logging.Logger,
    file_path: str,
    chosen_params: dict,
    alternatives: list,
    confidence: float
) -> None:
    """Log a warning about ambiguous parameter inference.
    
    Args:
        logger: Logger instance to use
        file_path: Path to the file being processed
        chosen_params: Parameters that were chosen
        alternatives: Alternative parameter combinations
        confidence: Confidence score of chosen parameters
    """
    logger.warning(
        f"CSV parameter inference has low confidence ({confidence:.2f}) for file: {file_path}"
    )
    
    # Log chosen parameters
    param_str = ", ".join([f"{k}='{v}'" for k, v in chosen_params.items()])
    logger.warning(f"  Chosen parameters: {param_str}")
    
    # Log alternatives
    if alternatives:
        logger.warning("  Alternative options:")
        for i, alt in enumerate(alternatives[:3], 1):  # Show top 3 alternatives
            alt_str = ", ".join([f"{k}='{v}'" for k, v in alt.items() if k != 'score'])
            logger.warning(f"    {i}. {alt_str} (score: {alt.get('score', 0):.2f})")


def log_format_detection_debug(
    logger: logging.Logger,
    file_path: str,
    detection_result: dict,
    all_results: list
) -> None:
    """Log debug information about format detection process.
    
    Args:
        logger: Logger instance to use
        file_path: Path to the file being analyzed
        detection_result: Final detection result
        all_results: All detection results from different detectors
    """
    logger.debug(f"Format detection for {file_path}:")
    logger.debug(f"  Final result: {detection_result.get('format', 'unknown')} "
                f"(confidence: {detection_result.get('confidence', 0):.2f})")
    
    if all_results:
        logger.debug("  All detector results:")
        for result in all_results:
            logger.debug(f"    {result.get('format', 'unknown')}: "
                        f"confidence={result.get('confidence', 0):.2f}, "
                        f"method={result.get('evidence', {}).get('method', 'unknown')}")


def log_backend_availability(
    logger: logging.Logger,
    available_backends: dict,
    requested_backend: str
) -> None:
    """Log information about backend availability.
    
    Args:
        logger: Logger instance to use
        available_backends: Dictionary of available backends
        requested_backend: Backend that was requested
    """
    if requested_backend in available_backends:
        logger.debug(f"Backend '{requested_backend}' is available and ready")
    else:
        logger.debug(f"Backend '{requested_backend}' is not available")
        if available_backends:
            available_names = list(available_backends.keys())
            logger.debug(f"Available backends: {', '.join(available_names)}")
        else:
            logger.debug("No backends are currently available")


# Initialize default logging configuration
configure_logging()