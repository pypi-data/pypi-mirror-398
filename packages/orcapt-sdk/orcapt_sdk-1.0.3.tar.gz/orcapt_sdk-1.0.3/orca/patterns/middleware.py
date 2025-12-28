"""
Middleware Pattern
==================

Middleware chain for request/response processing.
Allows extensible processing pipeline.
"""

from typing import List, Callable, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """
    Base class for middleware components.
    
    Middleware can process requests before they reach the handler
    and responses before they're returned to the client.
    """
    
    @abstractmethod
    def process_request(self, data: Any) -> Any:
        """
        Process incoming request.
        
        Args:
            data: Request data
            
        Returns:
            Processed data (can be modified)
        """
        pass
    
    @abstractmethod
    def process_response(self, response: Any, data: Any) -> Any:
        """
        Process outgoing response.
        
        Args:
            response: Response data
            data: Original request data
            
        Returns:
            Processed response (can be modified)
        """
        pass
    
    def process_error(self, error: Exception, data: Any) -> None:
        """
        Process error (optional).
        
        Args:
            error: Exception that occurred
            data: Request data
        """
        pass


class LoggingMiddleware(Middleware):
    """
    Middleware for logging requests and responses.
    
    Example:
        >>> middleware = LoggingMiddleware()
        >>> middleware.process_request(data)
    """
    
    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize logging middleware.
        
        Args:
            log_level: Logging level
        """
        self.log_level = log_level
    
    def process_request(self, data: Any) -> Any:
        """Log incoming request."""
        logger.log(self.log_level, f"Processing request: {type(data).__name__}")
        return data
    
    def process_response(self, response: Any, data: Any) -> Any:
        """Log outgoing response."""
        logger.log(self.log_level, f"Sending response: {type(response).__name__}")
        return response
    
    def process_error(self, error: Exception, data: Any) -> None:
        """Log error."""
        logger.error(f"Error processing request: {error}")


class ValidationMiddleware(Middleware):
    """
    Middleware for validating requests.
    
    Example:
        >>> def validator(data):
        ...     if not hasattr(data, 'message'):
        ...         raise ValueError("Missing message")
        >>> 
        >>> middleware = ValidationMiddleware(validator)
    """
    
    def __init__(self, validator: Callable[[Any], None]):
        """
        Initialize validation middleware.
        
        Args:
            validator: Function that validates data (raises on error)
        """
        self.validator = validator
    
    def process_request(self, data: Any) -> Any:
        """Validate request."""
        self.validator(data)
        return data
    
    def process_response(self, response: Any, data: Any) -> Any:
        """Pass through response."""
        return response


class TransformMiddleware(Middleware):
    """
    Middleware for transforming data.
    
    Example:
        >>> def transform(data):
        ...     data.processed = True
        ...     return data
        >>> 
        >>> middleware = TransformMiddleware(request_transform=transform)
    """
    
    def __init__(
        self,
        request_transform: Optional[Callable[[Any], Any]] = None,
        response_transform: Optional[Callable[[Any], Any]] = None
    ):
        """
        Initialize transform middleware.
        
        Args:
            request_transform: Function to transform requests
            response_transform: Function to transform responses
        """
        self.request_transform = request_transform
        self.response_transform = response_transform
    
    def process_request(self, data: Any) -> Any:
        """Transform request."""
        if self.request_transform:
            return self.request_transform(data)
        return data
    
    def process_response(self, response: Any, data: Any) -> Any:
        """Transform response."""
        if self.response_transform:
            return self.response_transform(response)
        return response


class MiddlewareChain:
    """
    Chain of middleware components.
    
    Processes data through multiple middleware in sequence.
    
    Example:
        >>> chain = MiddlewareChain()
        >>> chain.add(LoggingMiddleware())
        >>> chain.add(ValidationMiddleware(validator))
        >>> processed_data = chain.process_request(data)
    """
    
    def __init__(self):
        """Initialize empty middleware chain."""
        self.middlewares: List[Middleware] = []
    
    def add(self, middleware: Middleware) -> 'MiddlewareChain':
        """
        Add middleware to chain.
        
        Args:
            middleware: Middleware to add
            
        Returns:
            Self for chaining
        """
        self.middlewares.append(middleware)
        logger.debug(f"Added middleware: {type(middleware).__name__}")
        return self
    
    def process_request(self, data: Any) -> Any:
        """
        Process request through all middleware.
        
        Args:
            data: Request data
            
        Returns:
            Processed data
        """
        for middleware in self.middlewares:
            try:
                data = middleware.process_request(data)
            except Exception as e:
                logger.error(f"Error in middleware {type(middleware).__name__}: {e}")
                middleware.process_error(e, data)
                raise
        return data
    
    def process_response(self, response: Any, data: Any) -> Any:
        """
        Process response through all middleware (in reverse).
        
        Args:
            response: Response data
            data: Original request data
            
        Returns:
            Processed response
        """
        # Process in reverse order
        for middleware in reversed(self.middlewares):
            try:
                response = middleware.process_response(response, data)
            except Exception as e:
                logger.error(f"Error in middleware {type(middleware).__name__}: {e}")
                middleware.process_error(e, data)
                raise
        return response


class MiddlewareManager:
    """
    Manager for middleware chains.
    
    Provides high-level API for middleware management.
    
    Example:
        >>> manager = MiddlewareManager()
        >>> manager.use(LoggingMiddleware())
        >>> manager.use(ValidationMiddleware(validator))
        >>> result = manager.execute(handler_func, data)
    """
    
    def __init__(self):
        """Initialize middleware manager."""
        self.chain = MiddlewareChain()
    
    def use(self, middleware: Middleware) -> 'MiddlewareManager':
        """
        Add middleware (fluent interface).
        
        Args:
            middleware: Middleware to add
            
        Returns:
            Self for chaining
        """
        self.chain.add(middleware)
        return self
    
    def execute(
        self,
        handler: Callable[[Any], Any],
        data: Any
    ) -> Any:
        """
        Execute handler with middleware.
        
        Args:
            handler: Function to execute
            data: Request data
            
        Returns:
            Response from handler (after middleware processing)
        """
        # Process request
        processed_data = self.chain.process_request(data)
        
        # Execute handler
        response = handler(processed_data)
        
        # Process response
        processed_response = self.chain.process_response(response, processed_data)
        
        return processed_response


__all__ = [
    'Middleware',
    'LoggingMiddleware',
    'ValidationMiddleware',
    'TransformMiddleware',
    'MiddlewareChain',
    'MiddlewareManager',
]

