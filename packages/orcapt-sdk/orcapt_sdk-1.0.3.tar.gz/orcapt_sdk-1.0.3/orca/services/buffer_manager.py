"""
Buffer Manager Service
======================

Thread-safe buffer management for streaming responses.
Follows Single Responsibility Principle (SRP).
"""

import threading
import logging
from typing import Dict, List
from ..domain.interfaces import IBufferManager

logger = logging.getLogger(__name__)


class BufferManager(IBufferManager):
    """
    Thread-safe buffer manager for accumulating streaming content.
    
    Responsibilities:
    - Store streaming chunks per response UUID
    - Provide thread-safe append operations
    - Drain buffers when complete
    """
    
    def __init__(self):
        self._buffers: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
        logger.debug("BufferManager initialized")
    
    def append(self, response_uuid: str, content: str) -> None:
        """
        Thread-safely append content to buffer.
        
        Args:
            response_uuid: Unique identifier for response
            content: Content chunk to append
        """
        if not response_uuid:
            logger.warning("Cannot append to buffer: response_uuid is empty")
            return
        
        with self._lock:
            if response_uuid not in self._buffers:
                self._buffers[response_uuid] = []
                logger.debug(f"Created new buffer for response {response_uuid}")
            
            self._buffers[response_uuid].append(content)
            logger.debug(f"Appended {len(content)} chars to buffer {response_uuid}")
    
    def drain(self, response_uuid: str) -> str:
        """
        Retrieve and clear buffer for response UUID.
        
        Args:
            response_uuid: Unique identifier for response
            
        Returns:
            Joined content from buffer, or empty string if no buffer exists
        """
        if not response_uuid:
            logger.warning("Cannot drain buffer: response_uuid is empty")
            return ""
        
        with self._lock:
            parts = self._buffers.pop(response_uuid, None)
        
        if not parts:
            logger.debug(f"No buffer found for response {response_uuid}")
            return ""
        
        result = "".join(parts)
        logger.debug(f"Drained buffer {response_uuid}: {len(result)} chars total")
        return result
    
    def has_buffer(self, response_uuid: str) -> bool:
        """
        Check if buffer exists for response UUID.
        
        Args:
            response_uuid: Unique identifier for response
            
        Returns:
            True if buffer exists, False otherwise
        """
        with self._lock:
            return response_uuid in self._buffers
    
    def clear(self, response_uuid: str) -> None:
        """
        Clear buffer without returning content.
        
        Args:
            response_uuid: Unique identifier for response
        """
        with self._lock:
            if response_uuid in self._buffers:
                del self._buffers[response_uuid]
                logger.debug(f"Cleared buffer for response {response_uuid}")
    
    def get_buffer_count(self) -> int:
        """
        Get count of active buffers.
        
        Returns:
            Number of active buffers
        """
        with self._lock:
            return len(self._buffers)

