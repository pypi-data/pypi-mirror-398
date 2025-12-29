import logging
import traceback
from typing import Optional, Dict, Any, Type, Callable

logger = logging.getLogger(__name__)

class DocumentConverterError(Exception):
    """Base exception for all document converter errors."""
    def __init__(self, message: str, original_error: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error
        self.context = context or {}

class ConversionError(DocumentConverterError):
    """Raised when a specific conversion task fails."""
    pass

class FormatError(DocumentConverterError):
    """Raised when file format detection or validation fails."""
    pass

class ConfigurationError(DocumentConverterError):
    """Raised when there is a configuration issue."""
    pass

class ResourceError(DocumentConverterError):
    """Raised when external resources (files, services) fail."""
    pass

class ErrorHandler:
    """
    Centralized error handling and recovery strategy manager.
    """
    
    def __init__(self):
        self._handlers: Dict[Type[Exception], Callable] = {}
        # Register default handlers
        self.register_handler(FileNotFoundError, self._handle_file_not_found)
        self.register_handler(PermissionError, self._handle_permission_error)

    def register_handler(self, exception_type: Type[Exception], handler_func: Callable):
        """Register a specific handler for an exception type."""
        self._handlers[exception_type] = handler_func

    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an exception and return a standardized error report.
        Allows for recovery strategies or graceful degradation.
        """
        context = context or {}
        
        # Log the full traceback for debugging
        logger.debug("Exception caught by ErrorHandler:", exc_info=error)
        
        # Check for specific handlers
        for exc_type, handler in self._handlers.items():
            if isinstance(error, exc_type):
                return handler(error, context)
        
        # Default handling logic
        if isinstance(error, DocumentConverterError):
            return self._handle_custom_error(error, context)
        
        return self._handle_unknown_error(error, context)

    def _handle_file_not_found(self, error: FileNotFoundError, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "ResourceError",
            "message": f"File not found: {error.filename}",
            "suggestion": "Please verify the file path and ensure the file exists.",
            "severity": "high",
            "recoverable": False
        }

    def _handle_permission_error(self, error: PermissionError, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "ResourceError",
            "message": f"Permission denied: {error.filename}",
            "suggestion": "Check file permissions or ensure the file is not open in another program.",
            "severity": "high",
            "recoverable": False
        }

    def _handle_custom_error(self, error: DocumentConverterError, context: Dict[str, Any]) -> Dict[str, Any]:
        # Try to derive suggestion from context or error message patterns
        suggestion = error.context.get("suggestion")
        if not suggestion:
            if "dependency" in error.message.lower():
                suggestion = "Try installing missing requirements via 'pip install -r requirements.txt'."
            elif "format" in error.message.lower():
                suggestion = "Ensure the file format is supported and the extension matches the content."
            else:
                suggestion = "Check application logs for more details."

        return {
            "type": error.__class__.__name__,
            "message": error.message,
            "suggestion": suggestion,
            "context": error.context,
            "original_error": str(error.original_error) if error.original_error else None,
            "severity": "error",
            "recoverable": False
        }

    def _handle_unknown_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "UnhandledException",
            "message": str(error),
            "suggestion": "This is an unexpected error. Please report it to the developers.",
            "traceback": traceback.format_exc(),
            "severity": "critical",
            "recoverable": False
        }
