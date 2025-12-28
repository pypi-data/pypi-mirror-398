"""
Tracing Service
===============

Handles tracing/logging functionality for debugging and monitoring.
Follows Single Responsibility Principle (SRP).
"""

import logging
from typing import Optional
from ..domain.interfaces import ITracingService

logger = logging.getLogger(__name__)


class TracingService(ITracingService):
    """
    Service for creating trace payloads with visibility control.
    
    Responsibilities:
    - Validate trace visibility
    - Format trace payloads
    - Manage progressive trace buffers
    """
    
    VALID_VISIBILITIES = ("all", "admin")
    DEFAULT_VISIBILITY = "all"
    
    def __init__(self):
        logger.debug("TracingService initialized")
    
    def send_trace(self, content: str, visibility: str = "all") -> str:
        """
        Generate trace payload for given content and visibility.
        
        Args:
            content: Trace content to display
            visibility: Who can see trace ("all" or "admin")
            
        Returns:
            Formatted trace payload string
        """
        if not content:
            logger.warning("send_trace called with empty content")
            return ""
        
        # Validate and normalize visibility
        validated_visibility = self.validate_visibility(visibility)
        
        # Build payload
        payload = (
            f"[orca.tracing.start]\n"
            f"- visibility: {validated_visibility}\n"
            f"content: {content}\n"
            f"[orca.tracing.end]"
        )
        
        logger.debug(f"Generated trace payload with visibility '{validated_visibility}'")
        return payload
    
    def validate_visibility(self, visibility: str) -> str:
        """
        Validate and normalize visibility parameter.
        
        Args:
            visibility: Visibility setting to validate
            
        Returns:
            Validated visibility (defaults to "all" if invalid)
        """
        if not visibility or visibility not in self.VALID_VISIBILITIES:
            logger.warning(
                f"Invalid visibility '{visibility}', "
                f"defaulting to '{self.DEFAULT_VISIBILITY}'"
            )
            return self.DEFAULT_VISIBILITY
        
        return visibility
    
    def get_valid_visibilities(self) -> tuple:
        """
        Get list of valid visibility options.
        
        Returns:
            Tuple of valid visibility options
        """
        return self.VALID_VISIBILITIES


class ProgressiveTraceBuffer:
    """
    Helper class for building traces progressively.
    
    Allows building a single trace entry over time by appending
    content incrementally before sending.
    """
    
    def __init__(self, tracing_service: TracingService):
        """
        Initialize progressive trace buffer.
        
        Args:
            tracing_service: Tracing service for generating final payload
        """
        self._tracing_service = tracing_service
        self._buffer: Optional[str] = None
        self._visibility: str = "all"
        logger.debug("ProgressiveTraceBuffer initialized")
    
    def begin(self, message: str, visibility: str = "all") -> None:
        """
        Start a progressive trace block.
        
        Args:
            message: Initial message
            visibility: Trace visibility setting
        """
        if not message:
            logger.warning("begin called with empty message")
            return
        
        validated_visibility = self._tracing_service.validate_visibility(visibility)
        
        self._buffer = message
        self._visibility = validated_visibility
        
        logger.debug(f"Progressive trace started with visibility '{validated_visibility}'")
    
    def append(self, message: str) -> None:
        """
        Append content to current trace buffer.
        
        Args:
            message: Content to append
        """
        if self._buffer is None:
            logger.warning(
                "append called without begin(). Call begin() first."
            )
            return
        
        if not message:
            return
        
        self._buffer += message
        logger.debug(f"Appended {len(message)} chars to progressive trace")
    
    def end(self, message: Optional[str] = None) -> str:
        """
        Complete and return the progressive trace payload.
        
        Args:
            message: Optional final message to append
            
        Returns:
            Complete trace payload string
        """
        if self._buffer is None:
            logger.warning(
                "end called without begin(). Nothing to send."
            )
            return ""
        
        # Append optional final message
        if message:
            self._buffer += message
        
        # Generate final payload
        complete_content = self._buffer
        visibility = self._visibility
        
        # Clear buffer
        self._buffer = None
        self._visibility = "all"
        
        # Generate and return trace payload
        payload = self._tracing_service.send_trace(complete_content, visibility)
        logger.debug(f"Progressive trace completed: {len(complete_content)} chars")
        
        return payload
    
    def is_active(self) -> bool:
        """
        Check if progressive trace is currently active.
        
        Returns:
            True if trace is active, False otherwise
        """
        return self._buffer is not None
    
    def clear(self) -> None:
        """Clear buffer without generating payload."""
        if self._buffer is not None:
            logger.debug("Cleared progressive trace buffer")
            self._buffer = None
            self._visibility = "all"

