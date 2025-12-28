"""
Context Managers
================

Resource management using context managers.
Ensures proper cleanup and resource handling.
"""

from typing import Optional, Any, Callable
from contextlib import contextmanager
import logging
import time

logger = logging.getLogger(__name__)


class SessionContext:
    """
    Context manager for session lifecycle management.
    
    Automatically handles session cleanup and error handling.
    
    Example:
        >>> with SessionContext(handler, data) as session:
        ...     session.stream("Hello!")
        ...     # Session is automatically closed
    """
    
    def __init__(self, handler: Any, data: Any):
        """
        Initialize context manager.
        
        Args:
            handler: OrcaHandler instance
            data: Request data
        """
        self.handler = handler
        self.data = data
        self.session: Optional[Any] = None
        self._start_time: Optional[float] = None
    
    def __enter__(self) -> Any:
        """
        Enter context - create session.
        
        Returns:
            Session instance
        """
        self._start_time = time.time()
        self.session = self.handler.begin(self.data)
        logger.debug("Session context entered")
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit context - cleanup session.
        
        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value
            exc_tb: Exception traceback
            
        Returns:
            False to propagate exceptions
        """
        duration = time.time() - self._start_time if self._start_time else 0
        
        if self.session:
            if exc_type is None:
                # Normal exit - close session
                try:
                    self.session.close()
                    logger.info(f"Session completed successfully in {duration:.3f}s")
                except Exception as e:
                    logger.error(f"Error closing session: {e}")
            else:
                # Error occurred - send error to client
                try:
                    error_msg = str(exc_val) if exc_val else "An error occurred"
                    self.session.error(error_msg)
                    logger.error(f"Session failed after {duration:.3f}s: {error_msg}")
                except Exception as e:
                    logger.error(f"Error handling session error: {e}")
        
        return False  # Propagate exceptions


class ResourceContext:
    """
    Generic resource context manager with callbacks.
    
    Allows custom setup and teardown logic.
    
    Example:
        >>> def setup():
        ...     print("Setting up")
        ...     return "resource"
        >>> 
        >>> def teardown(resource):
        ...     print(f"Cleaning up {resource}")
        >>> 
        >>> with ResourceContext(setup, teardown) as resource:
        ...     print(f"Using {resource}")
    """
    
    def __init__(
        self,
        setup: Callable[[], Any],
        teardown: Optional[Callable[[Any], None]] = None,
        error_handler: Optional[Callable[[Exception], None]] = None
    ):
        """
        Initialize resource context.
        
        Args:
            setup: Function to call on enter (should return resource)
            teardown: Function to call on exit (receives resource)
            error_handler: Function to call on error (receives exception)
        """
        self.setup = setup
        self.teardown = teardown
        self.error_handler = error_handler
        self.resource: Optional[Any] = None
    
    def __enter__(self) -> Any:
        """Enter context - call setup."""
        self.resource = self.setup()
        return self.resource
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context - call teardown and error handler."""
        if exc_type is not None and self.error_handler:
            try:
                self.error_handler(exc_val)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        
        if self.teardown:
            try:
                self.teardown(self.resource)
            except Exception as e:
                logger.error(f"Error in teardown: {e}")
        
        return False


@contextmanager
def timed_operation(operation_name: str, log_level: int = logging.INFO):
    """
    Context manager for timing operations.
    
    Args:
        operation_name: Name of the operation
        log_level: Logging level
        
    Yields:
        None
        
    Example:
        >>> with timed_operation("database_query"):
        ...     # Perform operation
        ...     pass
        ... # Logs: "database_query took 1.234s"
    """
    start_time = time.time()
    logger.log(log_level, f"Starting {operation_name}")
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.log(log_level, f"{operation_name} took {duration:.3f}s")


@contextmanager
def suppress_exceptions(*exception_types):
    """
    Context manager to suppress specific exceptions.
    
    Args:
        exception_types: Exception types to suppress
        
    Yields:
        None
        
    Example:
        >>> with suppress_exceptions(ValueError, TypeError):
        ...     # These exceptions will be suppressed
        ...     int("not a number")
    """
    try:
        yield
    except exception_types as e:
        logger.debug(f"Suppressed exception: {type(e).__name__}: {e}")


__all__ = [
    'SessionContext',
    'ResourceContext',
    'timed_operation',
    'suppress_exceptions',
]

