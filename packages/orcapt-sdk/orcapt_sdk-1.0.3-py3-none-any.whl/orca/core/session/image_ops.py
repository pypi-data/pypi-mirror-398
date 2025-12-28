"""
Image Operations
================

Handles image operations for a session.
Ultra-focused: ONLY image handling.
"""

import logging

logger = logging.getLogger(__name__)


class ImageOperations:
    """
    Manages image streaming.
    
    Ultra-focused on image operations only.
    Single Responsibility: Image handling.
    """
    
    def __init__(self, stream_func):
        """
        Initialize image operations.
        
        Args:
            stream_func: Function to stream content
        """
        self._stream = stream_func
    
    def send(self, url: str) -> None:
        """
        Stream image with Orca markers.
        
        Args:
            url: Image URL
        """
        if not url:
            logger.warning("Image URL is empty, skipping")
            return
        
        payload = f"[orca.image.start]{url}[orca.image.end]"
        self._stream(payload)
    
    # Alias for convenience
    pass_image = send

