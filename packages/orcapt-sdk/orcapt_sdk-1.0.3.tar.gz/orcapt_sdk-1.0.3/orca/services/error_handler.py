"""
Error Handler Service
=====================

Centralized error handling and formatting.
Follows Single Responsibility Principle (SRP).
"""

import logging
import traceback
from typing import Any, Dict, Optional
from ..domain.interfaces import IErrorHandler

logger = logging.getLogger(__name__)


class ErrorHandler(IErrorHandler):
    """
    Handles error formatting and response building.
    
    Responsibilities:
    - Format error messages for display
    - Build error response payloads
    - Create log payloads for error tracking
    - Extract stack traces from exceptions
    """
    
    MAX_MESSAGE_LENGTH = 1000
    MAX_TRACE_LENGTH = 5000
    
    def __init__(self):
        logger.debug("ErrorHandler initialized")
    
    def handle_error(
        self,
        data: Any,
        error_message: str,
        trace: Optional[str] = None,
        exception: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """
        Handle error and return formatted error response.
        
        Args:
            data: Request data object
            error_message: Error message text
            trace: Optional stack trace string
            exception: Optional exception object
            
        Returns:
            Dict containing error response data
        """
        # Build error response
        error_response = {
            'uuid': getattr(data, 'response_uuid', None),
            'conversation_id': getattr(data, 'conversation_id', None),
            'content': error_message,
            'role': 'developer',
            'status': 'FAILED',
            'usage': {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'input_token_details': {'tokens': []},
                'output_token_details': {'tokens': []}
            }
        }
        
        return error_response
    
    def format_error_display(self, error_message: str) -> str:
        """
        Format error message for user display.
        
        Args:
            error_message: Raw error message
            
        Returns:
            Formatted error message with emoji and markdown
        """
        return f"❌ **Error:** {error_message}"
    
    def create_log_payload(
        self,
        error_message: str,
        trace: str,
        response_uuid: str,
        conversation_id: int,
        thread_id: str,
        channel: str
    ) -> Dict[str, Any]:
        """
        Create log payload for error logging API.
        
        Args:
            error_message: Error message
            trace: Stack trace
            response_uuid: Response identifier
            conversation_id: Conversation identifier
            thread_id: Thread identifier
            channel: Channel identifier
            
        Returns:
            Log payload dict
        """
        # Truncate message and trace to API limits
        truncated_message = error_message[:self.MAX_MESSAGE_LENGTH]
        truncated_trace = trace[:self.MAX_TRACE_LENGTH] if trace else ''
        
        payload = {
            'message': truncated_message,
            'trace': truncated_trace,
            'level': 'error',
            'where': 'orcapt-sdk',
            'additional': {
                'uuid': response_uuid,
                'conversation_id': conversation_id,
                'thread_id': thread_id,
                'channel': channel
            }
        }
        
        return payload
    
    def extract_trace(
        self,
        trace: Optional[str] = None,
        exception: Optional[Exception] = None
    ) -> str:
        """
        Extract stack trace from various sources.
        
        Args:
            trace: Provided trace string
            exception: Exception object
            
        Returns:
            Stack trace string
        """
        # Use provided trace if available
        if trace:
            return trace
        
        # Extract from exception if available
        if exception:
            return ''.join(
                traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__
                )
            )
        
        # Try to get current exception context
        exc_info = traceback.format_exc()
        if exc_info and exc_info != 'NoneType: None\n':
            return exc_info
        
        return ''
    
    def log_error(
        self,
        error_message: str,
        trace: Optional[str] = None,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error with context information.
        
        Args:
            error_message: Error message
            trace: Optional trace string
            exception: Optional exception object
            context: Optional context information
        """
        logger.error(f"=== ERROR ===")
        logger.error(f"Message: {error_message}")
        
        if context:
            logger.error(f"Context: {context}")
        
        trace_info = self.extract_trace(trace, exception)
        if trace_info:
            logger.error(f"Trace:\n{trace_info}")
        
        logger.error(f"=== END ERROR ===")

