"""
Orca Interfaces
================

Abstract base classes and interfaces for SOLID-compliant architecture.
Following Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IStreamClient(ABC):
    """Interface for streaming clients (Centrifugo, DevStream, etc.)"""
    
    @abstractmethod
    def send_delta(self, channel: str, response_uuid: str, thread_id: str, content: str) -> None:
        """Send a streaming chunk/delta to the client."""
        pass
    
    @abstractmethod
    def send_completion(self, channel: str, response_uuid: str, thread_id: str, content: str) -> None:
        """Send completion signal to the client."""
        pass
    
    @abstractmethod
    def send_error(self, channel: str, response_uuid: str, thread_id: str, error_message: str) -> None:
        """Send error signal to the client."""
        pass
    
    @abstractmethod
    def update_config(self, url: str, token: str) -> None:
        """Update client configuration dynamically."""
        pass


class IBufferManager(ABC):
    """Interface for managing streaming buffers."""
    
    @abstractmethod
    def append(self, response_uuid: str, content: str) -> None:
        """Append content to buffer for given response UUID."""
        pass
    
    @abstractmethod
    def drain(self, response_uuid: str) -> str:
        """Retrieve and clear buffer for given response UUID."""
        pass
    
    @abstractmethod
    def has_buffer(self, response_uuid: str) -> bool:
        """Check if buffer exists for given response UUID."""
        pass


class IButtonRenderer(ABC):
    """Interface for rendering button blocks."""
    
    @abstractmethod
    def render_button_block(self, buttons: list) -> str:
        """Render a list of button definitions to Orca format."""
        pass
    
    @abstractmethod
    def create_link_button(self, label: str, url: str, row: int = 1, color: Optional[str] = None) -> Dict[str, Any]:
        """Create a link button definition."""
        pass
    
    @abstractmethod
    def create_action_button(self, label: str, action_id: str, row: int = 1, color: Optional[str] = None) -> Dict[str, Any]:
        """Create an action button definition."""
        pass


class ILoadingMarkerProvider(ABC):
    """Interface for providing loading markers."""
    
    @abstractmethod
    def get_marker(self, kind: str, action: str) -> str:
        """Get loading marker for given kind and action."""
        pass
    
    @abstractmethod
    def get_marker_by_alias(self, alias: str) -> Optional[str]:
        """Get loading marker by semantic alias."""
        pass


class IUsageTracker(ABC):
    """Interface for tracking usage metrics."""
    
    @abstractmethod
    def track(
        self,
        message_uuid: str,
        api_base_url: str,
        tokens: int,
        token_type: str,
        headers: Dict[str, str],
        cost: Optional[str] = None,
        label: Optional[str] = None
    ) -> None:
        """Track usage metrics."""
        pass


class ITracingService(ABC):
    """Interface for tracing service."""
    
    @abstractmethod
    def send_trace(self, content: str, visibility: str = "all") -> str:
        """Generate trace payload for given content and visibility."""
        pass
    
    @abstractmethod
    def validate_visibility(self, visibility: str) -> str:
        """Validate and normalize visibility parameter."""
        pass


class IErrorHandler(ABC):
    """Interface for error handling."""
    
    @abstractmethod
    def handle_error(
        self,
        data: Any,
        error_message: str,
        trace: Optional[str] = None,
        exception: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Handle error and return formatted error response."""
        pass
    
    @abstractmethod
    def format_error_display(self, error_message: str) -> str:
        """Format error message for user display."""
        pass
    
    @abstractmethod
    def create_log_payload(
        self,
        error_message: str,
        trace: str,
        response_uuid: str,
        conversation_id: int,
        thread_id: str,
        channel: str
    ) -> Dict[str, Any]:
        """Create log payload for error logging API."""
        pass


class IAPIClient(ABC):
    """Interface for HTTP API communication."""
    
    @abstractmethod
    def post(self, url: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> Any:
        """Send POST request."""
        pass
    
    @abstractmethod
    def put(self, url: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> Any:
        """Send PUT request."""
        pass
    
    @abstractmethod
    def get(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Any:
        """Send GET request."""
        pass


class IResponseBuilder(ABC):
    """Interface for building API responses."""
    
    @abstractmethod
    def build_complete_response(
        self,
        response_uuid: str,
        thread_id: str,
        content: str,
        usage_info: Optional[Any] = None,
        file_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build complete response payload."""
        pass
    
    @abstractmethod
    def build_error_response(
        self,
        response_uuid: str,
        conversation_id: int,
        error_message: str
    ) -> Dict[str, Any]:
        """Build error response payload."""
        pass

