"""Custom exceptions for the smart data loader."""

from typing import List, Dict, Any, Optional


class DataLoaderError(Exception):
    """Base exception for all data loader errors.
    
    This is the base class for all exceptions raised by the smart data loader.
    It provides common functionality for error context and suggestions.
    """
    
    def __init__(
        self, 
        message: str, 
        suggestions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.suggestions = suggestions or []
        self.context = context or {}
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion for resolving this error."""
        if suggestion not in self.suggestions:
            self.suggestions.append(suggestion)
    
    def add_context(self, key: str, value: Any) -> None:
        """Add context information to this error."""
        self.context[key] = value
    
    def get_detailed_message(self) -> str:
        """Get a detailed error message with context and suggestions."""
        parts = [str(self)]
        
        if self.context:
            parts.append("\nContext:")
            for key, value in self.context.items():
                parts.append(f"  {key}: {value}")
        
        if self.suggestions:
            parts.append("\nSuggestions:")
            for suggestion in self.suggestions:
                parts.append(f"  - {suggestion}")
        
        return "\n".join(parts)


class FormatDetectionError(DataLoaderError):
    """Raised when file format cannot be determined.
    
    This error occurs when the smart data loader cannot identify the format
    of a file through extension analysis or content inspection.
    """
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None, 
        supported_formats: Optional[List[str]] = None,
        detection_evidence: Optional[Dict[str, Any]] = None
    ):
        # Build comprehensive error message
        full_message = self._build_error_message(message, file_path, supported_formats)
        
        # Build suggestions
        suggestions = self._build_suggestions(file_path, supported_formats)
        
        # Build context
        context = {"file_path": file_path} if file_path else {}
        if supported_formats:
            context["supported_formats"] = supported_formats
        if detection_evidence:
            context["detection_evidence"] = detection_evidence
        
        super().__init__(full_message, suggestions, context)
        self.file_path = file_path
        self.supported_formats = supported_formats or []
        self.detection_evidence = detection_evidence or {}
    
    def _build_error_message(
        self, 
        message: str, 
        file_path: Optional[str], 
        supported_formats: Optional[List[str]]
    ) -> str:
        """Build a comprehensive error message."""
        parts = [message]
        
        if file_path:
            parts.append(f"File: {file_path}")
        
        if supported_formats:
            formats_str = ", ".join(supported_formats)
            parts.append(f"Supported formats: {formats_str}")
        
        return " | ".join(parts)
    
    def _build_suggestions(
        self, 
        file_path: Optional[str], 
        supported_formats: Optional[List[str]]
    ) -> List[str]:
        """Build helpful suggestions for resolving the error."""
        suggestions = []
        
        if file_path:
            suggestions.append(f"Verify that '{file_path}' is a valid data file")
            suggestions.append("Check if the file extension matches the actual content")
        
        if supported_formats:
            suggestions.append(f"Ensure the file is in one of these formats: {', '.join(supported_formats)}")
        
        suggestions.extend([
            "Try opening the file in a text editor to inspect its structure",
            "Consider converting the file to a supported format (CSV, Excel, or Parquet)",
            "Use the debug_mode=True parameter to see detailed detection information"
        ])
        
        return suggestions


class ParameterInferenceError(DataLoaderError):
    """Raised when loading parameters cannot be reliably inferred.
    
    This error occurs when the smart data loader cannot determine optimal
    parameters for loading a file, typically for CSV files with ambiguous
    structure or formatting.
    """
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None, 
        attempted_params: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[float] = None
    ):
        # Build comprehensive error message
        full_message = self._build_error_message(message, file_path, confidence_score)
        
        # Build suggestions
        suggestions = self._build_suggestions(file_path, attempted_params)
        
        # Build context
        context = {}
        if file_path:
            context["file_path"] = file_path
        if attempted_params:
            context["attempted_params"] = attempted_params
        if confidence_score is not None:
            context["confidence_score"] = confidence_score
        
        super().__init__(full_message, suggestions, context)
        self.file_path = file_path
        self.attempted_params = attempted_params or {}
        self.confidence_score = confidence_score
    
    def _build_error_message(
        self, 
        message: str, 
        file_path: Optional[str], 
        confidence_score: Optional[float]
    ) -> str:
        """Build a comprehensive error message."""
        parts = [message]
        
        if file_path:
            parts.append(f"File: {file_path}")
        
        if confidence_score is not None:
            parts.append(f"Confidence: {confidence_score:.2f}")
        
        return " | ".join(parts)
    
    def _build_suggestions(
        self, 
        file_path: Optional[str], 
        attempted_params: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Build helpful suggestions for resolving the error."""
        suggestions = []
        
        if file_path:
            suggestions.append(f"Manually inspect '{file_path}' to identify the correct parameters")
        
        suggestions.extend([
            "Specify parameters explicitly using LoadingParameters",
            "Check if the file has metadata rows that should be skipped",
            "Verify the file uses a consistent separator throughout",
            "Consider cleaning the data file to remove inconsistencies",
            "Use debug_mode=True to see detailed parameter inference information"
        ])
        
        if attempted_params:
            param_str = ", ".join([f"{k}={v}" for k, v in attempted_params.items()])
            suggestions.append(f"Try these detected parameters manually: {param_str}")
        
        return suggestions


class BackendNotAvailableError(DataLoaderError):
    """Raised when required DataFrame backend is not installed.
    
    This error occurs when trying to use a DataFrame backend (pandas or polars)
    that is not installed or not available in the current environment.
    """
    
    def __init__(self, backend: str, install_command: Optional[str] = None):
        # Build comprehensive error message
        message = f"Backend '{backend}' is not available or not installed"
        if install_command:
            message += f". Install with: {install_command}"
        
        # Build suggestions
        suggestions = self._build_suggestions(backend, install_command)
        
        # Build context
        context = {"backend": backend}
        if install_command:
            context["install_command"] = install_command
        
        super().__init__(message, suggestions, context)
        self.backend = backend
        self.install_command = install_command
    
    def _build_suggestions(self, backend: str, install_command: Optional[str]) -> List[str]:
        """Build helpful suggestions for resolving the error."""
        suggestions = []
        
        if install_command:
            suggestions.append(f"Install {backend} with: {install_command}")
        else:
            # Provide default installation commands
            if backend.lower() == "pandas":
                suggestions.extend([
                    "Install pandas with: uv add pandas",
                    "Or with pip: pip install pandas"
                ])
            elif backend.lower() == "polars":
                suggestions.extend([
                    "Install polars with: uv add polars",
                    "Or with pip: pip install polars"
                ])
            else:
                suggestions.append(f"Install {backend} using your package manager")
        
        suggestions.extend([
            f"Verify {backend} is properly installed: python -c 'import {backend}'",
            "Check if you're using the correct virtual environment",
            "Try using a different backend if available"
        ])
        
        return suggestions


class BackendLoadingError(DataLoaderError):
    """Raised when DataFrame creation fails with backend-specific issues.
    
    This error occurs when a DataFrame backend encounters an error while
    trying to load data, such as file corruption, memory issues, or
    incompatible data formats.
    """
    
    def __init__(
        self, 
        message: str, 
        backend: Optional[str] = None, 
        original_error: Optional[Exception] = None,
        file_path: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        # Store attributes first so they're available when building the message
        self.backend = backend
        self.original_error = original_error
        self.file_path = file_path
        self.parameters = parameters
        
        # Build comprehensive error message
        full_message = self._build_error_message(message, backend, original_error)
        
        # Build suggestions
        suggestions = self._build_suggestions(backend, original_error, file_path, parameters)
        
        # Build context
        context = {}
        if backend:
            context["backend"] = backend
        if original_error:
            context["original_error"] = f"{type(original_error).__name__}: {original_error}"
        if file_path:
            context["file_path"] = file_path
        if parameters:
            context["parameters"] = parameters
        
        super().__init__(full_message, suggestions, context)
    
    def _build_error_message(
        self, 
        message: str, 
        backend: Optional[str], 
        original_error: Optional[Exception]
    ) -> str:
        """Build a comprehensive error message."""
        parts = [message]
        
        if backend:
            parts.append(f"Backend: {backend}")
        
        if original_error:
            parts.append(f"Underlying error: {type(original_error).__name__}")
        
        # Include file path if available
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        
        return " | ".join(parts)
    
    def _build_suggestions(
        self, 
        backend: Optional[str], 
        original_error: Optional[Exception],
        file_path: Optional[str],
        parameters: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Build helpful suggestions for resolving the error."""
        suggestions = []
        
        if file_path:
            suggestions.extend([
                f"Verify that '{file_path}' is not corrupted",
                "Check if the file is currently being used by another process",
                "Ensure you have read permissions for the file"
            ])
        
        if parameters:
            suggestions.append("Try adjusting the loading parameters")
            if "separator" in parameters:
                suggestions.append("Verify the separator parameter matches the file format")
            if "skip_rows" in parameters:
                suggestions.append("Check if the skip_rows parameter is correct")
        
        if backend:
            suggestions.extend([
                f"Try using a different backend if {backend} is having issues",
                f"Update {backend} to the latest version",
                f"Check {backend} documentation for file format compatibility"
            ])
        
        # Add suggestions based on common error types
        if original_error:
            error_type = type(original_error).__name__
            if "Memory" in error_type or "memory" in str(original_error).lower():
                suggestions.extend([
                    "The file might be too large for available memory",
                    "Try processing the file in chunks",
                    "Consider using a more memory-efficient format like Parquet"
                ])
            elif "Permission" in error_type or "permission" in str(original_error).lower():
                suggestions.extend([
                    "Check file permissions",
                    "Ensure the file is not locked by another application"
                ])
            elif "Encoding" in error_type or "encoding" in str(original_error).lower():
                suggestions.extend([
                    "Try specifying a different encoding (e.g., 'latin-1', 'cp1252')",
                    "Check if the file contains non-UTF-8 characters"
                ])
        
        suggestions.append("Use debug_mode=True to get more detailed error information")
        
        return suggestions


# Error message templates for consistent messaging
ERROR_TEMPLATES = {
    "file_not_found": "File not found: {file_path}. Please verify the file path is correct.",
    "unsupported_format": "Unsupported file format detected for {file_path}. Supported formats: {formats}.",
    "parameter_inference_failed": "Could not reliably infer loading parameters for {file_path}. Confidence: {confidence:.2f}.",
    "backend_unavailable": "Backend '{backend}' is not available. Install with: {install_command}.",
    "backend_loading_failed": "Backend loading failed for {file_path} using {backend} backend: {error}.",
    "format_detection_failed": "Format detection failed for {file_path}. Try specifying the format manually.",
    "csv_parsing_error": "CSV parsing failed for {file_path}. Check separator and quoting parameters.",
    "excel_reading_error": "Excel file reading failed for {file_path}. Verify the file is not corrupted.",
    "parquet_loading_error": "Parquet file loading failed for {file_path}. Check file integrity."
}


def format_error_message(template_key: str, **kwargs) -> str:
    """Format an error message using a predefined template.
    
    Args:
        template_key: Key for the error template
        **kwargs: Values to substitute in the template
        
    Returns:
        Formatted error message
    """
    template = ERROR_TEMPLATES.get(template_key, "An error occurred: {error}")
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Error formatting message template '{template_key}': missing key {e}"