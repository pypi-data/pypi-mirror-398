"""
Audio Operations
================

Handles audio operations for a session.
Ultra-focused: ONLY audio handling.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class AudioOperations:
    """
    Manages audio streaming.
    
    Ultra-focused on audio operations only.
    Single Responsibility: Audio handling.
    """
    
    def __init__(self, stream_func):
        """
        Initialize audio operations.
        
        Args:
            stream_func: Function to stream content
        """
        self._stream = stream_func
    
    def send(self, tracks: List[Dict[str, str]]) -> None:
        """
        Stream audio tracks with Orca markers.
        
        Args:
            tracks: List of track dictionaries with keys:
                    - label: Track label (required)
                    - url: Audio URL (required)
                    - type: MIME type (e.g., "audio/mp3") (optional)
        """
        if not tracks:
            logger.warning("Audio tracks list is empty, skipping")
            return
        
        # Build YAML-like format
        payload = "[orca.audio.start]\n"
        
        for track in tracks:
            payload += "- "
            track_items = []
            
            if track.get("label"):
                track_items.append(f"label: {track['label']}")
            if track.get("url"):
                track_items.append(f"url: {track['url']}")
            if track.get("type"):
                track_items.append(f"type: {track['type']}")
            
            payload += "\n  ".join(track_items) + "\n"
        
        payload += "[orca.audio.end]"
        self._stream(payload)
    
    def send_single(self, url: str, label: str = None, mime_type: str = None) -> None:
        """
        Send single audio track.
        
        Args:
            url: Audio URL
            label: Optional track label
            mime_type: Optional MIME type (e.g., "audio/mp3")
        """
        track = {"url": url}
        if label:
            track["label"] = label
        if mime_type:
            track["type"] = mime_type
        
        self.send([track])

