"""
Session Core
============

Core session class using composition.
Ultra-clean: Delegates to specialized operations classes.
"""

import logging
from typing import Optional

from .loading_ops import LoadingOperations
from .image_ops import ImageOperations
from .video_ops import VideoOperations
from .location_ops import LocationOperations
from .card_ops import CardListOperations
from .audio_ops import AudioOperations
from .tracing_ops import TracingOperations
from .usage_ops import UsageOperations
from .button_ops import ButtonOperations
from ...helpers.button_helper import ButtonHelper

logger = logging.getLogger(__name__)


class Session:
    """
    Clean session using composition pattern.
    
    Responsibilities:
    - Coordinate operations via composition
    - Provide unified API
    - Delegate to specialized operations
    
    Design:
    - Composition over Inheritance
    - Single Responsibility (coordination only)
    - Each operation is a separate, focused class
    """
    
    def __init__(self, handler, data):
        """
        Initialize session with composition.
        
        Args:
            handler: Parent OrcaHandler
            data: Request data
        """
        self._handler = handler
        self._data = data
        
        # Core operations (public property access)
        self.loading = LoadingOperations(handler, data, self._stream_wrapper)
        self.image = ImageOperations(self._stream_wrapper)
        self.video = VideoOperations(self._stream_wrapper)
        self.location = LocationOperations(self._stream_wrapper)
        self.card = CardListOperations(self._stream_wrapper)
        self.audio = AudioOperations(self._stream_wrapper)
        self.tracing = TracingOperations(handler, self._stream_wrapper)
        self.usage = UsageOperations(handler, data)
        
        # Button helper (public namespace)
        self.button = ButtonHelper(self)
        
        # Deprecated button operations (for backwards compatibility)
        self._button_ops = ButtonOperations(self.button)
        self._button_ops.set_context(handler, self._stream_wrapper)
        
        # Preconfigure Centrifugo if provided
        if (not handler.dev_mode and 
            hasattr(data, 'stream_url') and 
            hasattr(data, 'stream_token')):
            handler.update_centrifugo_config(data.stream_url, data.stream_token)
    
    # ==================== Core Operations ====================
    
    def stream(self, content: str) -> None:
        """Stream content chunk."""
        self._handler.stream(self._data, content)
    
    def close(self, usage_info=None, file_url=None) -> str:
        """Complete response."""
        return self._handler.close(self._data, usage_info=usage_info, file_url=file_url)
    
    def error(self, error_message: str, exception: Exception = None, trace: str = None) -> None:
        """Send error."""
        self._handler.send_error(self._data, error_message, trace=trace, exception=exception)
    
    # ==================== Wrapper for Delegation ====================
    
    def _stream_wrapper(self, content: str) -> None:
        """Internal wrapper for delegation."""
        self.stream(content)
    
    # ==================== Deprecated Methods (Backwards Compatibility) ====================
    
    def start_loading(self, kind: str = "thinking") -> None:
        """[DEPRECATED] Use session.loading.start_loading() instead."""
        self.loading.start(kind)
    
    def end_loading(self, kind: str = "thinking") -> None:
        """[DEPRECATED] Use session.loading.end_loading() instead."""
        self.loading.end(kind)
    
    def pass_image(self, url: str) -> None:
        """[DEPRECATED] Use session.image.image() instead."""
        self.image.send(url)
    
    def tracing(self, content: str, visibility: str = "all") -> None:
        """[DEPRECATED] Use session.tracing.begin() instead."""
        self.tracing.send(content, visibility)
    
    def tracing_begin(self, message: str, visibility: str = "all") -> None:
        """[DEPRECATED] Use session.tracing.begin() instead."""
        self.tracing.begin(message, visibility)
    
    def tracing_append(self, message: str) -> None:
        """[DEPRECATED] Use session.tracing.append() instead."""
        self.tracing.append(message)
    
    def tracing_end(self, message: str = None) -> None:
        """End progressive trace."""
        self._tracing.end(message)
    
    # ==================== Usage Operations ====================
    
    def usage(
        self,
        tokens: int,
        token_type: str,
        cost: Optional[str] = None,
        label: Optional[str] = None
    ) -> None:
        """Track usage."""
        self._usage.track(tokens, token_type, cost, label)
    
    # ==================== Deprecated Button Methods ====================
    
    def button_link(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.link()"""
        self._button_ops.button_link(*args, **kwargs)
    
    def button_action(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.action()"""
        self._button_ops.button_action(*args, **kwargs)
    
    def buttons_begin(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.begin()"""
        self._button_ops.buttons_begin(*args, **kwargs)
    
    def buttons_add_link(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.add_link()"""
        self._button_ops.buttons_add_link(*args, **kwargs)
    
    def buttons_add_action(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.add_action()"""
        self._button_ops.buttons_add_action(*args, **kwargs)
    
    def buttons_add_link_button(self, *args, **kwargs) -> None:
        """Deprecated"""
        self._button_ops.buttons_add_link_button(*args, **kwargs)
    
    def buttons_add_action_button(self, *args, **kwargs) -> None:
        """Deprecated"""
        self._button_ops.buttons_add_action_button(*args, **kwargs)
    
    def buttons_end(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.end()"""
        self._button_ops.buttons_end(*args, **kwargs)
    
    def buttons(self, *args, **kwargs) -> None:
        """Deprecated dictionary-based API"""
        self._button_ops.buttons(*args, **kwargs)

