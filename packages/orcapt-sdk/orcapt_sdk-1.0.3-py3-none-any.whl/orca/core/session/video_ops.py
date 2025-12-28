"""
Video Operations
================

Handles video operations for a session.
Ultra-focused: ONLY video handling.
"""

import logging

logger = logging.getLogger(__name__)


class VideoOperations:
    """
    Manages video streaming.
    
    Ultra-focused on video operations only.
    Single Responsibility: Video handling.
    """
    
    def __init__(self, stream_func):
        """
        Initialize video operations.
        
        Args:
            stream_func: Function to stream content
        """
        self._stream = stream_func
    
    def send(self, url: str) -> None:
        """
        Stream video with Orca markers.
        
        Args:
            url: Video URL
        """
        if not url:
            logger.warning("Video URL is empty, skipping")
            return
        
        payload = f"[orca.video.start]{url}[orca.video.end]"
        self._stream(payload)
    
    def youtube(self, url: str) -> None:
        """
        Stream YouTube video with Orca markers.
        
        Args:
            url: YouTube video URL
        """
        if not url:
            logger.warning("YouTube URL is empty, skipping")
            return
        
        payload = f"[orca.youtube.start]{url}[orca.youtube.end]"
        self._stream(payload)

