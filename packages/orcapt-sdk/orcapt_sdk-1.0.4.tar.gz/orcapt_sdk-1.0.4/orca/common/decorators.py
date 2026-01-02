"""
Decorators
==========

Reusable decorators for common patterns in Orca SDK.
Follows DRY principle and reduces boilerplate code.

Available Decorators:
- @retry: Retry failed operations
- @timeout: Add timeout to operations
- @log_execution: Log function execution
- @validate_types: Runtime type validation
- @measure_time: Measure execution time
- @cache_result: Cache function results
- @handle_errors: Comprehensive error handling
"""

import time
import logging
import functools
from typing import Callable, Any, Optional, Type, TypeVar, cast
from .exceptions import wrap_exception

logger = logging.getLogger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
        
    Example:
        >>> @retry(max_attempts=3, delay=1.0)
        ... def unreliable_operation():
        ...     # This will retry up to 3 times
        ...     pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay}s: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            return None
        
        return cast(F, wrapper)
    return decorator


def log_execution(
    level: int = logging.INFO,
    include_args: bool = False,
    include_result: bool = False
) -> Callable[[F], F]:
    """
    Log function execution with optional args and results.
    
    Args:
        level: Logging level (default: INFO)
        include_args: Whether to log function arguments
        include_result: Whether to log function result
        
    Returns:
        Decorated function
        
    Example:
        >>> @log_execution(level=logging.DEBUG, include_args=True)
        ... def important_function(x, y):
        ...     return x + y
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            
            # Log start
            if include_args:
                logger.log(level, f"Calling {func_name} with args={args}, kwargs={kwargs}")
            else:
                logger.log(level, f"Calling {func_name}")
            
            # Execute
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log success
                if include_result:
                    logger.log(level, f"{func_name} completed in {duration:.3f}s, result={result}")
                else:
                    logger.log(level, f"{func_name} completed in {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.exception(f"{func_name} failed after {duration:.3f}s: {e}")
                raise
        
        return cast(F, wrapper)
    return decorator


def measure_time(label_or_func: Any = None) -> Any:
    """
    Measure and log execution time.
    
    Supports both @measure_time and @measure_time("label") syntax.
    
    Args:
        label_or_func: Optional label string, or function if called without parentheses
        
    Returns:
        Decorated function
        
    Example:
        >>> @measure_time
        ... def slow_operation():
        ...     time.sleep(1)
        # Output: slow_operation took 1.000s
        
        >>> @measure_time("data_processing")
        ... def process_data():
        ...     pass
        # Output: data_processing took 0.234s
    """
    def create_decorator(label: Optional[str] = None) -> Callable[[F], F]:
        """Create decorator with optional label."""
        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_label = label if label is not None else func.__name__
                logger.info(f"{log_label} took {duration:.3f}s")
                return result
            
            return cast(F, wrapper)
        return decorator
    
    # Support both @measure_time and @measure_time("label")
    if label_or_func is None:
        # Called as @measure_time (without parentheses)
        # Return decorator that will receive function
        return create_decorator(label=None)
    elif isinstance(label_or_func, str):
        # Called as @measure_time("label")
        # Return decorator with label
        return create_decorator(label=label_or_func)
    elif callable(label_or_func):
        # Called as @measure_time (function passed directly, rare case)
        # Apply decorator immediately
        return create_decorator(label=None)(label_or_func)
    else:
        # Invalid argument type
        raise TypeError(f"measure_time expects str or callable, got {type(label_or_func)}")


def handle_errors(
    default_return: Any = None,
    exception_class: Type[Exception] = Exception,
    log_level: int = logging.ERROR
) -> Callable[[F], F]:
    """
    Handle errors gracefully with default return value.
    
    Args:
        default_return: Value to return on error
        exception_class: Exception class to catch
        log_level: Logging level for errors
        
    Returns:
        Decorated function
        
    Example:
        >>> @handle_errors(default_return=[], exception_class=ValueError)
        ... def get_items():
        ...     # Returns [] if ValueError occurs
        ...     pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exception_class as e:
                logger.log(
                    log_level,
                    f"Error in {func.__name__}: {e}, returning default value"
                )
                return default_return
        
        return cast(F, wrapper)
    return decorator


def deprecated(reason: str, alternative: Optional[str] = None) -> Callable[[F], F]:
    """
    Mark a function as deprecated.
    
    Args:
        reason: Reason for deprecation
        alternative: Alternative function to use
        
    Returns:
        Decorated function
        
    Example:
        >>> @deprecated("Use new_function instead", alternative="new_function")
        ... def old_function():
        ...     pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            message = f"{func.__name__} is deprecated: {reason}"
            if alternative:
                message += f". Use {alternative} instead"
            logger.warning(message)
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


def singleton(cls: Type[T]) -> Type[T]:
    """
    Singleton decorator for classes.
    
    Ensures only one instance of a class exists.
    
    Args:
        cls: Class to make singleton
        
    Returns:
        Singleton class
        
    Example:
        >>> @singleton
        ... class Configuration:
        ...     pass
    """
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return cast(Type[T], get_instance)


def validate_not_none(*param_names: str) -> Callable[[F], F]:
    """
    Validate that specified parameters are not None.
    
    Args:
        param_names: Names of parameters to validate
        
    Returns:
        Decorated function
        
    Example:
        >>> @validate_not_none('user_id', 'token')
        ... def authenticate(user_id, token):
        ...     pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate specified parameters
            for param_name in param_names:
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is None:
                        raise ValueError(f"Parameter '{param_name}' cannot be None")
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


__all__ = [
    'retry',
    'log_execution',
    'measure_time',
    'handle_errors',
    'deprecated',
    'singleton',
    'validate_not_none',
]

