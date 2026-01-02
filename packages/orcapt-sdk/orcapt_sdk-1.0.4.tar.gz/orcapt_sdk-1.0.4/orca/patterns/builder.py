"""
Builder Pattern
===============

Fluent interface for building complex objects.
Provides a clean, readable API for object construction.
"""

from typing import Optional, Dict, Any, List
from ..config import LoadingKind, ButtonColor
import logging
import asyncio

logger = logging.getLogger(__name__)


class OrcaBuilder:
    """
    Builder for OrcaHandler with fluent interface.
    
    Provides a clean, readable way to construct OrcaHandler with custom configuration.
    
    Example:
        >>> handler = (OrcaBuilder()
        ...     .with_dev_mode(True)
        ...     .with_buffer_size(2000)
        ...     .with_timeout(60)
        ...     .build())
    """
    
    def __init__(self):
        """Initialize builder with default values."""
        self._dev_mode: Optional[bool] = None
        self._stream_client = None
        self._api_client = None
        self._buffer_manager = None
        self._button_renderer = None
        self._loading_marker_provider = None
        self._usage_tracker = None
        self._tracing_service = None
        self._error_handler = None
        self._response_builder = None
        self._custom_config: Dict[str, Any] = {}
    
    def with_dev_mode(self, enabled: bool = True) -> 'OrcaBuilder':
        """
        Enable or disable development mode.
        
        Args:
            enabled: Whether to enable dev mode
            
        Returns:
            Self for chaining
        """
        self._dev_mode = enabled
        return self
    
    def with_stream_client(self, client: Any) -> 'OrcaBuilder':
        """
        Set custom stream client.
        
        Args:
            client: Custom stream client
            
        Returns:
            Self for chaining
        """
        self._stream_client = client
        return self
    
    def with_api_client(self, client: Any) -> 'OrcaBuilder':
        """Set custom API client."""
        self._api_client = client
        return self
    
    def with_buffer_manager(self, manager: Any) -> 'OrcaBuilder':
        """Set custom buffer manager."""
        self._buffer_manager = manager
        return self
    
    def with_config(self, key: str, value: Any) -> 'OrcaBuilder':
        """
        Set custom configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            Self for chaining
        """
        self._custom_config[key] = value
        return self
    
    def build(self) -> Any:
        """
        Build and return OrcaHandler instance.
        
        Returns:
            Configured OrcaHandler instance
        """
        from ..core import OrcaHandler
        
        return OrcaHandler(
            dev_mode=self._dev_mode,
            stream_client=self._stream_client,
            api_client=self._api_client,
            buffer_manager=self._buffer_manager,
            button_renderer=self._button_renderer,
            loading_marker_provider=self._loading_marker_provider,
            usage_tracker=self._usage_tracker,
            tracing_service=self._tracing_service,
            error_handler=self._error_handler,
            response_builder=self._response_builder,
        )


class SessionBuilder:
    """
    Builder for constructing complex session interactions.
    
    Provides a fluent interface for building multi-step session flows.
    
    Example:
        >>> session_flow = (SessionBuilder(session)
        ...     .add_loading(LoadingKind.THINKING)
        ...     .add_stream("Processing...")
        ...     .add_button_link("Click", "https://example.com")
        ...     .build())
    """
    
    def __init__(self, handler_or_session: Optional[Any] = None):
        """
        Initialize builder with optional handler or session.
        
        Args:
            handler_or_session: Optional handler or session instance.
                                If handler, use start_session(data) to begin.
                                If session, can use directly.
        """
        # Try to detect if it's a handler (has 'begin' method) or session (has 'stream' method)
        if handler_or_session is None:
            self._handler = None
            self._session = None
        elif hasattr(handler_or_session, 'begin'):
            # It's a handler
            self._handler = handler_or_session
            self._session = None
        elif hasattr(handler_or_session, 'stream'):
            # It's a session
            self._handler = None
            self._session = handler_or_session
        else:
            # Default: assume it's a handler (for backward compatibility)
            self._handler = handler_or_session
            self._session = None
        
        self._operations: List[Dict[str, Any]] = []
    
    def start_session(self, data: Any) -> 'SessionBuilder':
        """
        Start session with request data (convenience method for documentation API).
        
        Requires handler to be provided in constructor.
        
        Args:
            data: Request data to start session with
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If handler was not provided in constructor
        """
        if self._handler is None:
            raise ValueError("Handler must be provided in constructor to use start_session()")
        
        self._session = self._handler.begin(data)
        return self
    
    def add_loading(
        self,
        kind: str = LoadingKind.THINKING.value,
        action: str = "start"
    ) -> 'SessionBuilder':
        """
        Add loading indicator operation.
        
        Args:
            kind: Type of loading
            action: 'start' or 'end'
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "loading",
            "kind": kind,
            "action": action,
        })
        return self
    
    def add_stream(self, content: str) -> 'SessionBuilder':
        """
        Add stream operation (queued, not real-time).
        
        All operations are queued and executed together when execute() or complete() is called.
        This ensures proper grouping and ordering of operations.
        
        Args:
            content: Content to stream
            
        Returns:
            Self for chaining
        """
        # Always queue - no real-time streaming
        self._operations.append({
            "type": "stream",
            "content": content,
        })
        return self
    
    def stream(self, content: str) -> 'SessionBuilder':
        """
        Stream content immediately (real-time).
        
        This method streams content directly to the session without queuing.
        Requires session to be available (either set directly or via start_session()).
        
        Args:
            content: Content to stream
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If session is not available
        """
        if self._session is None:
            raise ValueError("Session not available. Either provide session in constructor or call start_session(data) first.")
        
        self._session.stream(content)
        return self
    
    def add_button_link(
        self,
        label: str,
        url: str,
        row: int = 1,
        color: Optional[str] = None
    ) -> 'SessionBuilder':
        """
        Add link button operation.
        
        Args:
            label: Button label
            url: Button URL
            row: Button row
            color: Button color
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "button_link",
            "label": label,
            "url": url,
            "row": row,
            "color": color or ButtonColor.PRIMARY.value,
        })
        return self
    
    def add_button_action(
        self,
        label: str,
        action_id: str,
        row: int = 1,
        color: Optional[str] = None
    ) -> 'SessionBuilder':
        """Add action button operation."""
        self._operations.append({
            "type": "button_action",
            "label": label,
            "action_id": action_id,
            "row": row,
            "color": color or ButtonColor.PRIMARY.value,
        })
        return self
    
    def add_image(self, url: str) -> 'SessionBuilder':
        """Add image operation."""
        self._operations.append({
            "type": "image",
            "url": url,
        })
        return self
    
    def add_tracing(
        self,
        message: str,
        visibility: str = "all"
    ) -> 'SessionBuilder':
        """Add tracing operation."""
        self._operations.append({
            "type": "tracing",
            "message": message,
            "visibility": visibility,
        })
        return self
    
    def add_video(self, url: str) -> 'SessionBuilder':
        """
        Add video operation.
        
        Args:
            url: Video URL
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "video",
            "url": url,
        })
        return self
    
    def add_youtube(self, url: str) -> 'SessionBuilder':
        """
        Add YouTube video operation.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "youtube",
            "url": url,
        })
        return self
    
    def add_location(self, coordinates: str) -> 'SessionBuilder':
        """
        Add location operation.
        
        Args:
            coordinates: Location coordinates (e.g., "35.6892, 51.3890")
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "location",
            "coordinates": coordinates,
        })
        return self
    
    def add_location_coordinates(self, lat: float, lng: float) -> 'SessionBuilder':
        """
        Add location operation with coordinates.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Self for chaining
        """
        coordinates = f"{lat}, {lng}"
        return self.add_location(coordinates)
    
    def add_card_list(self, cards: List[Dict[str, Any]]) -> 'SessionBuilder':
        """
        Add card list operation.
        
        Args:
            cards: List of card dictionaries with keys:
                   - photo: Image URL (optional)
                   - header: Card title (optional)
                   - subheader: Card description (optional)
                   - text: Additional content (optional)
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "card_list",
            "cards": cards,
        })
        return self
    
    def add_audio(self, tracks: List[Dict[str, str]]) -> 'SessionBuilder':
        """
        Add audio operation.
        
        Args:
            tracks: List of track dictionaries with keys:
                    - label: Track label (required)
                    - url: Audio URL (required)
                    - type: MIME type (e.g., "audio/mp3") (optional)
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "audio",
            "tracks": tracks,
        })
        return self
    
    def add_audio_single(
        self,
        url: str,
        label: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> 'SessionBuilder':
        """
        Add single audio track operation.
        
        Args:
            url: Audio URL
            label: Optional track label
            mime_type: Optional MIME type (e.g., "audio/mp3")
            
        Returns:
            Self for chaining
        """
        track = {"url": url}
        if label:
            track["label"] = label
        if mime_type:
            track["type"] = mime_type
        
        return self.add_audio([track])
    
    def execute(self) -> None:
        """
        Execute all queued operations on the session.
        
        This method runs all operations that were added via the builder.
        Operations are executed and removed from the queue, so execute() can be called multiple times
        to execute new operations as they are added.
        
        Raises:
            ValueError: If session is not available (neither set directly nor started)
        """
        if self._session is None:
            raise ValueError("Session not available. Either provide session in constructor or call start_session(data) first.")
        
        if not self._operations:
            # No operations to execute
            return
        
        # Execute all queued operations
        operations_to_execute = self._operations.copy()
        self._operations = []  # Clear operations after copying
        
        for op in operations_to_execute:
            op_type = op["type"]
            
            if op_type == "loading":
                if op["action"] == "start":
                    self._session.loading.start(op["kind"])
                else:
                    self._session.loading.end(op["kind"])
            
            elif op_type == "stream":
                self._session.stream(op["content"])
            
            elif op_type == "button_link":
                self._session.button.link(
                    op["label"],
                    op["url"],
                    row=op["row"],
                    color=op["color"]
                )
            
            elif op_type == "button_action":
                self._session.button.action(
                    op["label"],
                    op["action_id"],
                    row=op["row"],
                    color=op["color"]
                )
            
            elif op_type == "image":
                self._session.image.send(op["url"])
            
            elif op_type == "tracing":
                self._session.tracing.send(op["message"], op["visibility"])
            
            elif op_type == "video":
                self._session.video.send(op["url"])
            
            elif op_type == "youtube":
                self._session.video.youtube(op["url"])
            
            elif op_type == "location":
                self._session.location.send(op["coordinates"])
            
            elif op_type == "card_list":
                self._session.card.send(op["cards"])
            
            elif op_type == "audio":
                self._session.audio.send(op["tracks"])
            
            elif op_type == "usage":
                self._session.usage.track(
                    tokens=op["tokens"],
                    token_type=op["token_type"],
                    cost=op.get("cost"),
                    label=op.get("label")
                )
            
            elif op_type == "process":
                op["func"](self._session)
        
        logger.info(f"Executed {len(operations_to_execute)} operations")
    
    def build(self) -> 'SessionBuilder':
        """
        Build (execute) the session flow.
        
        Executes all queued operations but does NOT close the session.
        Use complete() or close() to finalize and send to frontend.
        
        Returns:
            Self for final operations
        """
        self.execute()
        return self
    
    def finalize(self) -> 'SessionBuilder':
        """
        Finalize (execute) the session flow.
        
        Alias for build() for better readability.
        Note: Does NOT close the session. Use complete() to close and send to frontend.
        
        Returns:
            Self for final operations
        """
        return self.build()
    
    def complete(self, usage_info=None, file_url=None) -> str:
        """
        Complete the session and send response to frontend.
        
        Executes all queued operations and closes the session.
        This is the method to use when you want to finalize everything
        and send the complete response to the frontend.
        
        Args:
            usage_info: Optional usage information dict
            file_url: Optional file URL
            
        Returns:
            Full response content as string
            
        Raises:
            ValueError: If session is not available
        """
        self.execute()
        
        if self._session is None:
            raise ValueError("Session not available. Either provide session in constructor or call start_session(data) first.")
        
        return self._session.close(usage_info=usage_info, file_url=file_url)
    
    def close(self, usage_info=None, file_url=None) -> str:
        """
        Close session and send response to frontend (alias for complete()).
        
        Args:
            usage_info: Optional usage information dict
            file_url: Optional file URL
            
        Returns:
            Full response content as string
        """
        return self.complete(usage_info=usage_info, file_url=file_url)
    
    async def acomplete(self, usage_info=None, file_url=None) -> str:
        """
        Async version of complete() for use in async contexts.
        
        Executes all queued operations and closes the session in a thread,
        making it safe for use in async functions (FastAPI, async handlers, etc.).
        
        Args:
            usage_info: Optional usage information dict
            file_url: Optional file URL
            
        Returns:
            Full response content as string
            
        Raises:
            ValueError: If session is not available
            
        Example:
            >>> async def handler(data):
            ...     builder = SessionBuilder(handler).start_session(data)
            ...     response = await builder.acomplete()
            ...     return response
        """
        self.execute()
        
        if self._session is None:
            raise ValueError("Session not available. Either provide session in constructor or call start_session(data) first.")
        
        # Run blocking session.close() in thread
        return await asyncio.to_thread(self._session.close, usage_info=usage_info, file_url=file_url)
    
    async def aclose(self, usage_info=None, file_url=None) -> str:
        """
        Async version of close() for use in async contexts (alias for acomplete()).
        
        Args:
            usage_info: Optional usage information dict
            file_url: Optional file URL
            
        Returns:
            Full response content as string
        """
        return await self.acomplete(usage_info=usage_info, file_url=file_url)
    
    # ==================== Convenience Methods (Documentation API) ====================
    
    def show_loading(self, kind: str = LoadingKind.THINKING.value) -> 'SessionBuilder':
        """
        Show loading indicator (convenience method).
        
        Args:
            kind: Type of loading indicator
            
        Returns:
            Self for chaining
        """
        return self.add_loading(kind, "start")
    
    def hide_loading(self, kind: str = LoadingKind.THINKING.value) -> 'SessionBuilder':
        """
        Hide loading indicator (convenience method).
        
        Args:
            kind: Type of loading indicator
            
        Returns:
            Self for chaining
        """
        return self.add_loading(kind, "end")
    
    def add_button(
        self,
        label: str,
        url_or_id: str,
        row: int = 1,
        color: Optional[str] = None
    ) -> 'SessionBuilder':
        """
        Add button (convenience method - auto-detects link vs action).
        
        Args:
            label: Button label
            url_or_id: URL (if starts with http) or action ID
            row: Button row
            color: Button color
            
        Returns:
            Self for chaining
        """
        if url_or_id.startswith("http://") or url_or_id.startswith("https://"):
            return self.add_button_link(label, url_or_id, row, color)
        else:
            return self.add_button_action(label, url_or_id, row, color)
    
    def track_trace(
        self,
        message: str,
        visibility: str = "all"
    ) -> 'SessionBuilder':
        """
        Track trace (convenience method).
        
        Args:
            message: Trace message
            visibility: Visibility level
            
        Returns:
            Self for chaining
        """
        return self.add_tracing(message, visibility)
    
    def track_usage(
        self,
        tokens: int,
        token_type: str,
        cost: Optional[str] = None,
        label: Optional[str] = None
    ) -> 'SessionBuilder':
        """
        Track usage (adds usage operation to queue).
        
        Args:
            tokens: Token count
            token_type: Type of tokens
            cost: Optional cost
            label: Optional label
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "usage",
            "tokens": tokens,
            "token_type": token_type,
            "cost": cost,
            "label": label,
        })
        return self
    
    def process(self, func) -> 'SessionBuilder':
        """
        Process with custom function.
        
        Args:
            func: Function that takes session and processes it
            
        Returns:
            Self for chaining
        """
        self._operations.append({
            "type": "process",
            "func": func,
        })
        return self


__all__ = [
    'OrcaBuilder',
    'SessionBuilder',
]

