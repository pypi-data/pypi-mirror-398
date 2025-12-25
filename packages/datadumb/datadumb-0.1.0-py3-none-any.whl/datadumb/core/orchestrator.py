"""Core loading orchestrator that coordinates detection, inference, and loading."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import (
    DataLoaderError,
    FormatDetectionError,
    ParameterInferenceError,
    BackendNotAvailableError,
    BackendLoadingError,
    format_error_message
)
from .models import LoadingContext, LoadingParameters, FileFormat
from ..detection.format_detector import get_format_detector
from ..detection.parameter_inferrer import get_parameter_inferrer
from ..backends import PandasAdapter, PolarsAdapter
from ..utils.logging import (
    get_logger,
    log_error_with_context,
    log_parameter_inference_warning,
    log_format_detection_debug,
    log_backend_availability
)


logger = get_logger(__name__)


class BackendRegistry:
    """Registry for managing backend adapters."""
    
    def __init__(self):
        self._backends: Dict[str, Any] = {}
        
        # Register default backends
        self.register(PandasAdapter())
        self.register(PolarsAdapter())
    
    def register(self, adapter: Any) -> None:
        """Register a backend adapter.
        
        Args:
            adapter: BackendAdapter instance to register
        """
        self._backends[adapter.name] = adapter
        logger.debug(f"Registered backend adapter: {adapter.name}")
    
    def unregister(self, backend_name: str) -> None:
        """Unregister a backend adapter.
        
        Args:
            backend_name: Name of the backend to unregister
        """
        if backend_name in self._backends:
            self._backends.pop(backend_name, None)
            logger.debug(f"Unregistered backend adapter: {backend_name}")
    
    def get_backend(self, backend_name: str) -> Any:
        """Get a backend adapter by name.
        
        Args:
            backend_name: Name of the backend
            
        Returns:
            BackendAdapter instance
            
        Raises:
            BackendNotAvailableError: If backend is not registered or available
        """
        if backend_name not in self._backends:
            error = BackendNotAvailableError(
                backend=backend_name,
                install_command=f"uv add {backend_name}"
            )
            log_error_with_context(
                logger,
                f"Backend '{backend_name}' is not registered",
                operation="backend_lookup",
                suggestions=error.suggestions
            )
            raise error
        
        adapter = self._backends[backend_name]
        if not adapter.is_available():
            error = BackendNotAvailableError(
                backend=backend_name,
                install_command=f"uv add {backend_name}"
            )
            log_error_with_context(
                logger,
                f"Backend '{backend_name}' is not available",
                operation="backend_availability_check",
                suggestions=error.suggestions
            )
            raise error
        
        return adapter
    
    def get_available_backends(self) -> Dict[str, Any]:
        """Get all available backend adapters.
        
        Returns:
            Dictionary mapping backend names to adapter instances
        """
        available = {
            name: adapter 
            for name, adapter in self._backends.items() 
            if adapter.is_available()
        }
        
        logger.debug(f"Available backends: {list(available.keys())}")
        return available


class LoadingOrchestrator:
    """Orchestrates the complete data loading workflow."""
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the loading orchestrator.
        
        Args:
            debug_mode: Enable debug logging
        """
        self.debug_mode = debug_mode
        self._backend_registry = BackendRegistry()
        
        # Configure logging level based on debug mode
        if debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled for LoadingOrchestrator")
    
    def load_dataframe(
        self, 
        file_path: Path, 
        backend: str,
        parameters: Optional[LoadingParameters] = None
    ) -> Any:
        """Load a data file into a DataFrame using the complete workflow.
        
        Args:
            file_path: Path to the data file
            backend: Backend library to use ('pandas' or 'polars')
            parameters: Optional pre-determined loading parameters
            
        Returns:
            DataFrame object from the specified backend
            
        Raises:
            FileNotFoundError: If the file does not exist
            FormatDetectionError: If file format cannot be determined
            ParameterInferenceError: If parameters cannot be inferred
            BackendNotAvailableError: If backend is not available
            BackendLoadingError: If DataFrame creation fails
        """
        # Validate file exists
        if not file_path.exists():
            error_msg = format_error_message("file_not_found", file_path=file_path)
            log_error_with_context(
                logger,
                error_msg,
                file_path=str(file_path),
                operation="file_validation",
                suggestions=[
                    "Verify the file path is correct",
                    "Check if the file exists in the expected location",
                    "Ensure you have read permissions for the file"
                ]
            )
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Starting data loading workflow for {file_path} with {backend} backend")
        
        # Log backend availability information
        available_backends = self._backend_registry.get_available_backends()
        log_backend_availability(logger, available_backends, backend)
        
        try:
            # Step 1: Detect file format if not provided in parameters
            if parameters is None:
                logger.debug("Detecting file format...")
                detection_result = self._detect_format(file_path)
                detected_format = detection_result.format
                logger.info(f"Detected format: {detected_format.value} (confidence: {detection_result.confidence:.2f})")
                
                if self.debug_mode:
                    log_format_detection_debug(
                        logger, 
                        str(file_path), 
                        {"format": detected_format.value, "confidence": detection_result.confidence},
                        [{"format": detected_format.value, "confidence": detection_result.confidence, "evidence": detection_result.evidence}]
                    )
            else:
                detected_format = parameters.format
                logger.debug(f"Using provided format: {detected_format.value}")
            
            # Step 2: Infer loading parameters if not provided
            if parameters is None:
                logger.debug("Inferring loading parameters...")
                parameters = self._infer_parameters(file_path, detected_format)
                logger.info(f"Inferred parameters: separator='{parameters.separator}', skip_rows={parameters.skip_rows}, confidence={parameters.confidence_score:.2f}")
                
                if self.debug_mode:
                    logger.debug(f"Parameter inference details: {parameters.additional_params}")
                
                # Log warnings for low confidence parameter inference (but only for formats that need inference)
                if parameters.confidence_score < 0.8 and detected_format == FileFormat.CSV:
                    # Get alternative parameters for warning
                    alternatives = parameters.additional_params.get("alternatives", [])
                    chosen_params = {
                        "separator": parameters.separator,
                        "skip_rows": parameters.skip_rows
                    }
                    log_parameter_inference_warning(
                        logger,
                        str(file_path),
                        chosen_params,
                        alternatives,
                        parameters.confidence_score
                    )
            else:
                logger.debug("Using provided loading parameters")
            
            # Step 3: Load DataFrame with backend
            logger.debug(f"Loading DataFrame with {backend} backend...")
            dataframe = self._load_with_backend_direct(file_path, parameters, backend)
            
            logger.info(f"Successfully loaded data from {file_path}")
            return dataframe
            
        except (FormatDetectionError, ParameterInferenceError, BackendNotAvailableError) as e:
            # These are expected errors with good context - re-raise as-is
            logger.error(f"Data loading failed: {str(e)}")
            raise
            
        except BackendLoadingError as e:
            # Backend loading errors already have context - re-raise as-is
            logger.error(f"Backend loading failed: {str(e)}")
            raise
            
        except Exception as e:
            # Wrap unexpected errors with context
            error_msg = f"Unexpected error during data loading for {file_path}: {str(e)}"
            log_error_with_context(
                logger,
                error_msg,
                file_path=str(file_path),
                operation="data_loading",
                original_error=e,
                suggestions=[
                    "Enable debug_mode=True for more detailed error information",
                    "Check if the file is corrupted or in an unexpected format",
                    "Try loading the file with explicit parameters",
                    "Verify all required dependencies are installed"
                ]
            )
            wrapped_error = DataLoaderError(error_msg)
            wrapped_error.__cause__ = e
            raise wrapped_error
    
    def _detect_format(self, file_path: Path) -> Any:
        """Detect file format with error context preservation.
        
        Args:
            file_path: Path to the file
            
        Returns:
            DetectionResult with format information
            
        Raises:
            FormatDetectionError: If format cannot be determined
        """
        try:
            format_detector = get_format_detector()
            result = format_detector.detect_format(file_path)
            
            logger.debug(f"Format detection completed for {file_path}: {result.format.value}")
            return result
            
        except FormatDetectionError as e:
            # Enhance the error with additional context if needed
            if not e.suggestions:
                e.add_suggestion("Use debug_mode=True to see detailed detection information")
                e.add_suggestion("Try opening the file in a text editor to inspect its structure")
            
            log_error_with_context(
                logger,
                str(e),
                file_path=str(file_path),
                operation="format_detection",
                suggestions=e.suggestions
            )
            raise
            
        except Exception as e:
            # Wrap other exceptions with format detection context
            error_msg = format_error_message("format_detection_failed", file_path=file_path)
            
            # Get supported formats for error context
            try:
                supported_formats = [fmt.value for fmt in get_format_detector().get_supported_formats()]
            except:
                supported_formats = ["csv", "excel", "parquet"]
            
            wrapped_error = FormatDetectionError(
                error_msg,
                file_path=str(file_path),
                supported_formats=supported_formats,
                detection_evidence={"original_error": str(e)}
            )
            wrapped_error.__cause__ = e
            
            log_error_with_context(
                logger,
                error_msg,
                file_path=str(file_path),
                operation="format_detection",
                original_error=e,
                suggestions=wrapped_error.suggestions
            )
            raise wrapped_error
    
    def _infer_parameters(self, file_path: Path, format: FileFormat) -> LoadingParameters:
        """Infer loading parameters with error context preservation.
        
        Args:
            file_path: Path to the file
            format: Detected file format
            
        Returns:
            LoadingParameters with inferred settings
            
        Raises:
            ParameterInferenceError: If parameters cannot be inferred
        """
        try:
            parameter_inferrer = get_parameter_inferrer()
            result = parameter_inferrer.infer_parameters(file_path, format)
            
            logger.debug(f"Parameter inference completed for {file_path}")
            return result
            
        except ParameterInferenceError as e:
            # Enhance the error with additional context if needed
            if not e.suggestions:
                e.add_suggestion("Try specifying parameters explicitly using LoadingParameters")
                e.add_suggestion("Use debug_mode=True to see detailed inference information")
            
            log_error_with_context(
                logger,
                str(e),
                file_path=str(file_path),
                operation="parameter_inference",
                suggestions=e.suggestions
            )
            raise
            
        except Exception as e:
            # Wrap other exceptions with parameter inference context
            error_msg = format_error_message(
                "parameter_inference_failed", 
                file_path=file_path, 
                confidence=0.0
            )
            
            wrapped_error = ParameterInferenceError(
                error_msg,
                file_path=str(file_path),
                confidence_score=0.0
            )
            wrapped_error.__cause__ = e
            
            log_error_with_context(
                logger,
                error_msg,
                file_path=str(file_path),
                operation="parameter_inference",
                original_error=e,
                suggestions=wrapped_error.suggestions
            )
            raise wrapped_error
    
    def _load_with_backend_direct(self, file_path: Path, parameters: LoadingParameters, backend: str) -> Any:
        """Load DataFrame using the specified backend with error context preservation.
        
        Args:
            file_path: Path to the data file
            parameters: Loading parameters
            backend: Backend name
            
        Returns:
            DataFrame object from the backend
            
        Raises:
            BackendNotAvailableError: If backend is not available
            BackendLoadingError: If loading fails
        """
        try:
            # Get the backend adapter (this will validate the backend name)
            backend_adapter = self._backend_registry.get_backend(backend)
            
            logger.debug(f"Using {backend} backend to load {parameters.format.value} file")
            
            # Load based on file format
            if parameters.format == FileFormat.CSV:
                return backend_adapter.load_csv(file_path, parameters)
            elif parameters.format == FileFormat.EXCEL:
                return backend_adapter.load_excel(file_path, parameters)
            elif parameters.format == FileFormat.PARQUET:
                return backend_adapter.load_parquet(file_path, parameters)
            else:
                error_msg = f"Unsupported format for loading: {parameters.format.value}"
                error = BackendLoadingError(
                    error_msg,
                    backend=backend,
                    file_path=str(file_path),
                    parameters=parameters.__dict__
                )
                
                log_error_with_context(
                    logger,
                    error_msg,
                    file_path=str(file_path),
                    operation="backend_loading",
                    suggestions=error.suggestions
                )
                raise error
                
        except (BackendNotAvailableError, BackendLoadingError):
            # Re-raise backend errors as-is (they already have good context)
            raise
            
        except Exception as e:
            # Wrap other exceptions with backend loading context
            error_msg = format_error_message(
                "backend_loading_failed",
                file_path=file_path,
                backend=backend,
                error=str(e)
            )
            
            wrapped_error = BackendLoadingError(
                error_msg,
                backend=backend,
                original_error=e,
                file_path=str(file_path),
                parameters=parameters.__dict__
            )
            wrapped_error.__cause__ = e
            
            log_error_with_context(
                logger,
                error_msg,
                file_path=str(file_path),
                operation="backend_loading",
                original_error=e,
                suggestions=wrapped_error.suggestions
            )
            raise wrapped_error
    
    def _load_with_backend(self, context: LoadingContext) -> Any:
        """Load DataFrame using the specified backend with error context preservation.
        
        Args:
            context: Loading context with all necessary information
            
        Returns:
            DataFrame object from the backend
            
        Raises:
            BackendNotAvailableError: If backend is not available
            BackendLoadingError: If loading fails
        """
        try:
            # Get the backend adapter
            backend_adapter = self._backend_registry.get_backend(context.backend)
            
            # Load based on file format
            if context.parameters.format == FileFormat.CSV:
                return backend_adapter.load_csv(context.file_path, context.parameters)
            elif context.parameters.format == FileFormat.EXCEL:
                return backend_adapter.load_excel(context.file_path, context.parameters)
            elif context.parameters.format == FileFormat.PARQUET:
                return backend_adapter.load_parquet(context.file_path, context.parameters)
            else:
                error_msg = f"Unsupported format for loading: {context.parameters.format.value}"
                error = BackendLoadingError(
                    error_msg,
                    backend=context.backend,
                    file_path=str(context.file_path),
                    parameters=context.parameters.__dict__
                )
                
                log_error_with_context(
                    logger,
                    error_msg,
                    file_path=str(context.file_path),
                    operation="backend_loading",
                    suggestions=error.suggestions
                )
                raise error
                
        except (BackendNotAvailableError, BackendLoadingError):
            # Re-raise backend errors as-is (they already have good context)
            raise
            
        except Exception as e:
            # Wrap other exceptions with backend loading context
            error_msg = format_error_message(
                "backend_loading_failed",
                file_path=context.file_path,
                backend=context.backend,
                error=str(e)
            )
            
            wrapped_error = BackendLoadingError(
                error_msg,
                backend=context.backend,
                original_error=e,
                file_path=str(context.file_path),
                parameters=context.parameters.__dict__
            )
            wrapped_error.__cause__ = e
            
            log_error_with_context(
                logger,
                error_msg,
                file_path=str(context.file_path),
                operation="backend_loading",
                original_error=e,
                suggestions=wrapped_error.suggestions
            )
            raise wrapped_error
    
    def get_backend_registry(self) -> BackendRegistry:
        """Get the backend registry for advanced usage.
        
        Returns:
            BackendRegistry instance
        """
        return self._backend_registry


# Global orchestrator instance
_orchestrator = LoadingOrchestrator()


def get_loading_orchestrator(debug_mode: bool = False) -> LoadingOrchestrator:
    """Get a loading orchestrator instance.
    
    Args:
        debug_mode: Enable debug logging
        
    Returns:
        LoadingOrchestrator instance
    """
    if debug_mode and not _orchestrator.debug_mode:
        # Create a new instance with debug mode if needed
        return LoadingOrchestrator(debug_mode=True)
    return _orchestrator


def load_dataframe(
    file_path: Path, 
    backend: str,
    parameters: Optional[LoadingParameters] = None,
    debug_mode: bool = False
) -> Any:
    """Convenience function to load a data file into a DataFrame.
    
    Args:
        file_path: Path to the data file
        backend: Backend library to use ('pandas' or 'polars')
        parameters: Optional pre-determined loading parameters
        debug_mode: Enable debug logging
        
    Returns:
        DataFrame object from the specified backend
    """
    orchestrator = get_loading_orchestrator(debug_mode=debug_mode)
    return orchestrator.load_dataframe(file_path, backend, parameters)