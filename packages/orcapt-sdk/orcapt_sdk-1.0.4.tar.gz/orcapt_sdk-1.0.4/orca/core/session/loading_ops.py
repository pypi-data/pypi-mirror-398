"""
Loading Operations
==================

Handles loading indicator operations for a session.
Ultra-focused: ONLY loading indicators.
"""

import logging

logger = logging.getLogger(__name__)


class LoadingOperations:
    """
    Manages loading indicators.
    
    Ultra-focused on loading operations only.
    Single Responsibility: Loading indicators.
    """
    
    def __init__(self, handler, data, stream_func):
        """
        Initialize loading operations.
        
        Args:
            handler: Parent handler (for accessing services)
            data: Request data
            stream_func: Function to stream content
        """
        self._handler = handler
        self._data = data
        self._stream = stream_func
    
    def start(self, kind: str = "thinking") -> None:
        """
        Start loading indicator.
        
        Args:
            kind: Type of loading (thinking, image, code, search)
        """
        marker = self._handler._loading_marker_provider.get_marker(kind, "start")
        self._stream(marker)
    
    def end(self, kind: str = "thinking") -> None:
        """
        End loading indicator.
        
        Args:
            kind: Type of loading (thinking, image, code, search)
        """
        marker = self._handler._loading_marker_provider.get_marker(kind, "end")
        self._stream(marker)

