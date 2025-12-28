"""
Tracing Operations
==================

Handles tracing/debugging operations for a session.
Ultra-focused: ONLY tracing functionality.
"""

import logging
from ...services.tracing_service import ProgressiveTraceBuffer

logger = logging.getLogger(__name__)


class TracingOperations:
    """
    Manages tracing and debugging operations.
    
    Ultra-focused on tracing only.
    Single Responsibility: Tracing/debugging.
    """
    
    def __init__(self, handler, stream_func):
        """
        Initialize tracing operations.
        
        Args:
            handler: Parent handler (for accessing tracing service)
            stream_func: Function to stream content
        """
        self._handler = handler
        self._stream = stream_func
        self._progressive_trace = ProgressiveTraceBuffer(handler._tracing_service)
    
    def send(self, content: str, visibility: str = "all") -> None:
        """
        Send single trace entry.
        
        Args:
            content: Trace content
            visibility: Visibility level ("all" or "admin")
        """
        if not content:
            return
        
        payload = self._handler._tracing_service.send_trace(content, visibility)
        self._stream(payload)
    
    def begin(self, message: str, visibility: str = "all") -> None:
        """
        Start progressive trace.
        
        Args:
            message: Initial message
            visibility: Visibility level
        """
        self._progressive_trace.begin(message, visibility)
    
    def append(self, message: str) -> None:
        """
        Append to progressive trace.
        
        Args:
            message: Message to append
        """
        self._progressive_trace.append(message)
    
    def end(self, message: str = None) -> None:
        """
        Complete and send progressive trace.
        
        Args:
            message: Optional final message
        """
        payload = self._progressive_trace.end(message)
        if payload:
            self._stream(payload)

