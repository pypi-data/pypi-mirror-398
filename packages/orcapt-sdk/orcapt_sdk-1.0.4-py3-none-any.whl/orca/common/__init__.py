"""
Common Module
=============

Common utilities and patterns used across Orca SDK.
This module contains reusable components that don't fit into specific layers.

Submodules:
- exceptions: Custom exception hierarchy
- decorators: Reusable decorators for common patterns
- logging_config: Centralized logging configuration

These are cross-cutting concerns that span multiple layers.
"""

from .exceptions import (
    # Base
    OrcaException,
    # Configuration
    ConfigurationError,
    InvalidConfigError,
    MissingConfigError,
    # Validation
    ValidationError,
    InvalidTypeError,
    InvalidValueError,
    MissingRequiredFieldError,
    # Communication
    CommunicationError,
    StreamError,
    APIError,
    TimeoutError,
    # Buffer
    BufferError,
    BufferOverflowError,
    BufferEmptyError,
    # Usage
    UsageTrackingError,
    # Helpers
    wrap_exception,
)

from .decorators import (
    retry,
    log_execution,
    measure_time,
    handle_errors,
    deprecated,
    singleton,
    validate_not_none,
)

from .logging_config import (
    setup_logging,
    get_logger,
    set_level,
    disable_logging,
    enable_debug_logging,
    LoggingContext,
    LogColors,
    ColoredFormatter,
)

from .type_guards import (
    # Basic type guards
    is_string,
    is_int,
    is_non_empty_string,
    is_positive_int,
    # Validation functions
    validate_type,
    validate_not_none,
    validate_in_range,
    validate_string_length,
)

__all__ = [
    # Exceptions
    'OrcaException',
    'ConfigurationError',
    'InvalidConfigError',
    'MissingConfigError',
    'ValidationError',
    'InvalidTypeError',
    'InvalidValueError',
    'MissingRequiredFieldError',
    'CommunicationError',
    'StreamError',
    'APIError',
    'TimeoutError',
    'BufferError',
    'BufferOverflowError',
    'BufferEmptyError',
    'UsageTrackingError',
    'wrap_exception',
    # Decorators
    'retry',
    'log_execution',
    'measure_time',
    'handle_errors',
    'deprecated',
    'singleton',
    'validate_not_none',
    # Logging
    'setup_logging',
    'get_logger',
    'set_level',
    'disable_logging',
    'enable_debug_logging',
    'LoggingContext',
    'LogColors',
    'ColoredFormatter',
    # Type Guards
    'is_string',
    'is_int',
    'is_non_empty_string',
    'is_positive_int',
    'validate_type',
    'validate_not_none',
    'validate_in_range',
    'validate_string_length',
]

