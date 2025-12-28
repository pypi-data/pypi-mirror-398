"""
Type Guards
===========

Runtime type checking and validation using type guards.
Provides type-safe runtime validation with TypeGuard support.

Type guards help ensure type safety at runtime, complementing
static type checking with mypy/pyright.
"""

from typing import Any, TypeVar, TypeGuard, Optional, List, Dict, Union, Protocol
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ==================== Basic Type Guards ====================

def is_string(value: Any) -> TypeGuard[str]:
    """
    Type guard for string values.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a string
        
    Example:
        >>> data = "hello"
        >>> if is_string(data):
        ...     # data is guaranteed to be str here
        ...     print(data.upper())
    """
    return isinstance(value, str)


def is_int(value: Any) -> TypeGuard[int]:
    """Type guard for integer values."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_float(value: Any) -> TypeGuard[float]:
    """Type guard for float values."""
    return isinstance(value, float)


def is_bool(value: Any) -> TypeGuard[bool]:
    """Type guard for boolean values."""
    return isinstance(value, bool)


def is_dict(value: Any) -> TypeGuard[Dict[Any, Any]]:
    """Type guard for dictionary values."""
    return isinstance(value, dict)


def is_list(value: Any) -> TypeGuard[List[Any]]:
    """Type guard for list values."""
    return isinstance(value, list)


# ==================== Optional Type Guards ====================

def is_non_empty_string(value: Any) -> TypeGuard[str]:
    """
    Type guard for non-empty strings.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a non-empty string
    """
    return isinstance(value, str) and len(value) > 0


def is_positive_int(value: Any) -> TypeGuard[int]:
    """Type guard for positive integers."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def is_non_negative_int(value: Any) -> TypeGuard[int]:
    """Type guard for non-negative integers."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


# ==================== Protocol-Based Type Guards ====================

class HasName(Protocol):
    """Protocol for objects with a name attribute."""
    name: str


class HasValue(Protocol):
    """Protocol for objects with a value attribute."""
    value: Any


def has_name(obj: Any) -> TypeGuard[HasName]:
    """
    Type guard for objects with name attribute.
    
    Args:
        obj: Object to check
        
    Returns:
        True if object has name attribute
    """
    return hasattr(obj, 'name') and isinstance(getattr(obj, 'name'), str)


def has_value(obj: Any) -> TypeGuard[HasValue]:
    """Type guard for objects with value attribute."""
    return hasattr(obj, 'value')


# ==================== Composite Type Guards ====================

def is_string_list(value: Any) -> TypeGuard[List[str]]:
    """
    Type guard for list of strings.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a list of strings
    """
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def is_int_list(value: Any) -> TypeGuard[List[int]]:
    """Type guard for list of integers."""
    return isinstance(value, list) and all(isinstance(item, int) and not isinstance(item, bool) for item in value)


def is_string_dict(value: Any) -> TypeGuard[Dict[str, Any]]:
    """Type guard for dictionary with string keys."""
    return isinstance(value, dict) and all(isinstance(key, str) for key in value.keys())


# ==================== Validation Functions ====================

def validate_type(
    value: Any,
    expected_type: type,
    field_name: str = "value",
    raise_exception: bool = True
) -> bool:
    """
    Validate that a value has the expected type.
    
    Args:
        value: Value to validate
        expected_type: Expected type
        field_name: Name of the field (for error messages)
        raise_exception: Whether to raise exception on failure
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        TypeError: If value has wrong type and raise_exception is True
        
    Example:
        >>> validate_type("hello", str, "message")
        True
        >>> validate_type(123, str, "message")  # Raises TypeError
    """
    if not isinstance(value, expected_type):
        error_msg = f"Expected {field_name} to be {expected_type.__name__}, got {type(value).__name__}"
        if raise_exception:
            raise TypeError(error_msg)
        logger.warning(error_msg)
        return False
    return True


def validate_not_none(
    value: Optional[T],
    field_name: str = "value",
    raise_exception: bool = True
) -> TypeGuard[T]:
    """
    Validate that a value is not None.
    
    Args:
        value: Value to validate
        field_name: Name of the field
        raise_exception: Whether to raise exception on failure
        
    Returns:
        True if not None
        
    Raises:
        ValueError: If value is None and raise_exception is True
    """
    if value is None:
        error_msg = f"{field_name} cannot be None"
        if raise_exception:
            raise ValueError(error_msg)
        logger.warning(error_msg)
        return False
    return True


def validate_in_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    field_name: str = "value",
    raise_exception: bool = True
) -> bool:
    """
    Validate that a value is within a range.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field
        raise_exception: Whether to raise exception on failure
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If value is out of range and raise_exception is True
    """
    if min_value is not None and value < min_value:
        error_msg = f"{field_name} must be >= {min_value}, got {value}"
        if raise_exception:
            raise ValueError(error_msg)
        logger.warning(error_msg)
        return False
    
    if max_value is not None and value > max_value:
        error_msg = f"{field_name} must be <= {max_value}, got {value}"
        if raise_exception:
            raise ValueError(error_msg)
        logger.warning(error_msg)
        return False
    
    return True


def validate_string_length(
    value: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "value",
    raise_exception: bool = True
) -> bool:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of the field
        raise_exception: Whether to raise exception on failure
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If length is invalid and raise_exception is True
    """
    length = len(value)
    
    if min_length is not None and length < min_length:
        error_msg = f"{field_name} must be at least {min_length} characters, got {length}"
        if raise_exception:
            raise ValueError(error_msg)
        logger.warning(error_msg)
        return False
    
    if max_length is not None and length > max_length:
        error_msg = f"{field_name} must be at most {max_length} characters, got {length}"
        if raise_exception:
            raise ValueError(error_msg)
        logger.warning(error_msg)
        return False
    
    return True


__all__ = [
    # Basic type guards
    'is_string',
    'is_int',
    'is_float',
    'is_bool',
    'is_dict',
    'is_list',
    # Optional type guards
    'is_non_empty_string',
    'is_positive_int',
    'is_non_negative_int',
    # Protocol-based
    'has_name',
    'has_value',
    # Composite
    'is_string_list',
    'is_int_list',
    'is_string_dict',
    # Validation
    'validate_type',
    'validate_not_none',
    'validate_in_range',
    'validate_string_length',
]

