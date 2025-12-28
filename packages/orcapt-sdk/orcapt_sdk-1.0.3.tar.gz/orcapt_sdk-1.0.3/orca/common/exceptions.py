"""
Custom Exceptions
=================

Comprehensive exception hierarchy for Orca SDK.
Follows best practices for exception design.

Exception Hierarchy:
    OrcaException (base)
    ├── ConfigurationError
    │   ├── InvalidConfigError
    │   └── MissingConfigError
    ├── ValidationError
    │   ├── InvalidTypeError
    │   ├── InvalidValueError
    │   └── MissingRequiredFieldError
    ├── CommunicationError
    │   ├── StreamError
    │   ├── APIError
    │   └── TimeoutError
    ├── BufferError
    │   ├── BufferOverflowError
    │   └── BufferEmptyError
    └── UsageTrackingError
"""

from typing import Optional, Any, Dict


class OrcaException(Exception):
    """
    Base exception for all Orca SDK exceptions.
    
    All custom exceptions should inherit from this base class.
    Allows users to catch all Orca-related errors with a single except clause.
    
    Attributes:
        message: Error message
        details: Additional error details
        original_exception: Original exception if this wraps another exception
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize exception with message and optional details.
        
        Args:
            message: Human-readable error message
            details: Additional context about the error
            original_exception: Original exception if this wraps another exception
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_exception = original_exception
    
    def __str__(self) -> str:
        """String representation with details."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary.
        
        Returns:
            Dictionary representation of exception
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


# ==================== Configuration Errors ====================

class ConfigurationError(OrcaException):
    """Base class for configuration-related errors."""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""
    pass


# ==================== Validation Errors ====================

class ValidationError(OrcaException):
    """Base class for validation-related errors."""
    pass


class InvalidTypeError(ValidationError):
    """Raised when a value has an invalid type."""
    
    def __init__(self, field: str, expected_type: str, actual_type: str):
        """
        Initialize with field and type information.
        
        Args:
            field: Name of the field
            expected_type: Expected type name
            actual_type: Actual type name
        """
        message = f"Invalid type for '{field}': expected {expected_type}, got {actual_type}"
        details = {
            "field": field,
            "expected_type": expected_type,
            "actual_type": actual_type,
        }
        super().__init__(message, details)


class InvalidValueError(ValidationError):
    """Raised when a value is invalid."""
    
    def __init__(self, field: str, value: Any, reason: str):
        """
        Initialize with field, value, and reason.
        
        Args:
            field: Name of the field
            value: The invalid value
            reason: Why the value is invalid
        """
        message = f"Invalid value for '{field}': {reason}"
        details = {
            "field": field,
            "value": str(value),
            "reason": reason,
        }
        super().__init__(message, details)


class MissingRequiredFieldError(ValidationError):
    """Raised when a required field is missing."""
    
    def __init__(self, field: str):
        """
        Initialize with field name.
        
        Args:
            field: Name of the missing field
        """
        message = f"Required field '{field}' is missing"
        details = {"field": field}
        super().__init__(message, details)


# ==================== Communication Errors ====================

class CommunicationError(OrcaException):
    """Base class for communication-related errors."""
    pass


class StreamError(CommunicationError):
    """Raised when streaming fails."""
    
    def __init__(self, message: str, channel: Optional[str] = None):
        """
        Initialize with message and optional channel.
        
        Args:
            message: Error message
            channel: Stream channel if applicable
        """
        details = {"channel": channel} if channel else {}
        super().__init__(message, details)


class APIError(CommunicationError):
    """Raised when API communication fails."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        response_body: Optional[str] = None
    ):
        """
        Initialize with API error details.
        
        Args:
            message: Error message
            status_code: HTTP status code
            endpoint: API endpoint
            response_body: Response body if available
        """
        details = {}
        if status_code is not None:
            details["status_code"] = status_code
        if endpoint:
            details["endpoint"] = endpoint
        if response_body:
            details["response_body"] = response_body
        super().__init__(message, details)


class TimeoutError(CommunicationError):
    """Raised when an operation times out."""
    
    def __init__(self, operation: str, timeout: float):
        """
        Initialize with operation and timeout.
        
        Args:
            operation: Name of the operation that timed out
            timeout: Timeout duration in seconds
        """
        message = f"Operation '{operation}' timed out after {timeout}s"
        details = {"operation": operation, "timeout": timeout}
        super().__init__(message, details)


# ==================== Buffer Errors ====================

class BufferError(OrcaException):
    """Base class for buffer-related errors."""
    pass


class BufferOverflowError(BufferError):
    """Raised when buffer capacity is exceeded."""
    
    def __init__(self, size: int, capacity: int):
        """
        Initialize with size information.
        
        Args:
            size: Attempted size
            capacity: Maximum capacity
        """
        message = f"Buffer overflow: attempted to store {size} items, capacity is {capacity}"
        details = {"size": size, "capacity": capacity}
        super().__init__(message, details)


class BufferEmptyError(BufferError):
    """Raised when attempting to read from empty buffer."""
    
    def __init__(self):
        """Initialize with standard message."""
        super().__init__("Buffer is empty")


# ==================== Usage Tracking Errors ====================

class UsageTrackingError(OrcaException):
    """Raised when usage tracking fails."""
    
    def __init__(self, message: str, token_type: Optional[str] = None):
        """
        Initialize with message and optional token type.
        
        Args:
            message: Error message
            token_type: Type of tokens being tracked
        """
        details = {"token_type": token_type} if token_type else {}
        super().__init__(message, details)


# ==================== Helper Functions ====================

def wrap_exception(
    exception: Exception,
    message: str,
    exception_class: type = OrcaException
) -> OrcaException:
    """
    Wrap an exception in a Orca exception.
    
    Args:
        exception: Original exception to wrap
        message: New error message
        exception_class: Exception class to use for wrapping
        
    Returns:
        Wrapped exception
        
    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     raise wrap_exception(e, "Operation failed")
    """
    return exception_class(
        message=message,
        details={"original_error": str(exception)},
        original_exception=exception
    )


__all__ = [
    # Base
    'OrcaException',
    # Configuration
    'ConfigurationError',
    'InvalidConfigError',
    'MissingConfigError',
    # Validation
    'ValidationError',
    'InvalidTypeError',
    'InvalidValueError',
    'MissingRequiredFieldError',
    # Communication
    'CommunicationError',
    'StreamError',
    'APIError',
    'TimeoutError',
    # Buffer
    'BufferError',
    'BufferOverflowError',
    'BufferEmptyError',
    # Usage
    'UsageTrackingError',
    # Helpers
    'wrap_exception',
]

