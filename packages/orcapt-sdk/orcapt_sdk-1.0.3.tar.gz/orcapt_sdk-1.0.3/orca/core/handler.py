"""
Unified Orca Handler - Clean & Minimal
========================================

Main orchestrator for Orca platform communication.
Follows SOLID principles with dependency injection.

This file contains ONLY the core handler logic.
Session, helpers, and utilities are in separate modules.
"""

import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from ..domain.interfaces import (
    IStreamClient, IBufferManager, IButtonRenderer, ILoadingMarkerProvider,
    IUsageTracker, ITracingService, IErrorHandler, IAPIClient, IResponseBuilder
)
from ..factories import StreamClientFactory
from ..services import (
    BufferManager, ButtonRenderer, LoadingMarkerProvider, UsageTracker,
    TracingService, ErrorHandler, ResponseBuilder
)
from ..infrastructure.api_client import APIClient
from .session import Session

logger = logging.getLogger(__name__)


class OrcaHandler:
    """
    Main handler for Orca communication.
    
    Orchestrates services via dependency injection.
    Keeps business logic minimal and delegates to services.
    """
    
    def __init__(
        self,
        dev_mode: Optional[bool] = None,
        stream_client: Optional[IStreamClient] = None,
        api_client: Optional[IAPIClient] = None,
        buffer_manager: Optional[IBufferManager] = None,
        button_renderer: Optional[IButtonRenderer] = None,
        loading_marker_provider: Optional[ILoadingMarkerProvider] = None,
        usage_tracker: Optional[IUsageTracker] = None,
        tracing_service: Optional[ITracingService] = None,
        error_handler: Optional[IErrorHandler] = None,
        response_builder: Optional[IResponseBuilder] = None
    ):
        """Initialize with dependency injection (all optional with defaults)."""
        # Determine mode
        if dev_mode is None:
            dev_mode = os.environ.get('ORCA_DEV_MODE', 'false').lower() in ('true', '1', 'yes')
        self.dev_mode = dev_mode
        
        # Auto-setup logging in dev mode if not already configured
        if self.dev_mode:
            self._setup_dev_logging()
        
        # Inject dependencies
        self._api_client = api_client or APIClient()
        self._stream_client = stream_client or StreamClientFactory.create(dev_mode)
        self._buffer_manager = buffer_manager or BufferManager()
        self._button_renderer = button_renderer or ButtonRenderer()
        self._loading_marker_provider = loading_marker_provider or LoadingMarkerProvider()
        self._usage_tracker = usage_tracker or UsageTracker(self._api_client)
        self._tracing_service = tracing_service or TracingService()
        self._error_handler = error_handler or ErrorHandler()
        self._response_builder = response_builder or ResponseBuilder()
        
        mode = "DEV" if self.dev_mode else "PRODUCTION"
        logger.info(f"🚀 OrcaHandler initialized in {mode} mode")
    
    def _setup_dev_logging(self) -> None:
        """Setup logging for dev mode if not already configured."""
        # Check if orca logger already has handlers
        orca_logger = logging.getLogger("orca")
        
        # Only setup if no handlers exist
        if not orca_logger.handlers:
            # Setup basic console logging for dev mode
            import sys
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # Use simple colored format
            from ..common.logging_config import ColoredFormatter, SIMPLE_FORMAT
            if sys.stdout.isatty():
                formatter = ColoredFormatter(SIMPLE_FORMAT)
            else:
                formatter = logging.Formatter(SIMPLE_FORMAT)
            
            console_handler.setFormatter(formatter)
            orca_logger.setLevel(logging.DEBUG)
            orca_logger.addHandler(console_handler)
            
            # Ensure child loggers propagate to parent (default is True)
            # Set level for common orca sub-loggers to ensure they show up
            for logger_name in ['orca.core', 'orca.infrastructure', 'orca.services', 
                              'orca.core.handler', 'orca.infrastructure.dev_stream_client']:
                child_logger = logging.getLogger(logger_name)
                child_logger.setLevel(logging.DEBUG)
                # propagate is True by default, but ensure it's set
                child_logger.propagate = True
    
    def begin(self, data) -> Session:
        """Start a streaming session."""
        return Session(self, data)
    
    def update_centrifugo_config(self, stream_url: str, stream_token: str) -> None:
        """Update Centrifugo configuration (production only)."""
        if self.dev_mode:
            return
        if stream_url and stream_token:
            self._stream_client.update_config(stream_url, stream_token)
    
    def stream(self, data, content: str) -> None:
        """Stream chunk and buffer it."""
        resolved = self._loading_marker_provider.get_marker_by_alias(content.strip().lower()) or content
        self._buffer_manager.append(data.response_uuid, resolved)
        self._stream_chunk(data, resolved)
    
    def close(self, data, usage_info=None, file_url=None) -> str:
        """Finalize response."""
        full_response = self._buffer_manager.drain(data.response_uuid)
        self._complete_response(data, full_response, usage_info, file_url)
        return full_response
    
    def send_error(self, data, error_message: str, trace: Optional[str] = None, exception: Optional[Exception] = None) -> None:
        """Send error message."""
        display = self._error_handler.format_error_display(error_message)
        self._buffer_manager.drain(data.response_uuid)
        
        self._stream_client.send_delta(data.channel, data.response_uuid, data.thread_id, display)
        
        if self.dev_mode:
            self._stream_client.send_completion(data.channel, data.response_uuid, data.thread_id, display)
            return
        
        self._stream_client.send_error(data.channel, data.response_uuid, data.thread_id, error_message)
        
        if hasattr(data, 'url') and data.url:
            self._persist_error(data, error_message, trace, exception)
    
    # ==================== Internal Methods ====================
    
    def _stream_chunk(self, data, content: str) -> None:
        """Stream chunk to client."""
        if not self.dev_mode and hasattr(data, 'stream_url') and hasattr(data, 'stream_token'):
            self.update_centrifugo_config(data.stream_url, data.stream_token)
        self._stream_client.send_delta(data.channel, data.response_uuid, data.thread_id, content)
    
    def _complete_response(self, data, full_response: str, usage_info, file_url) -> None:
        """Complete response and persist."""
        if not self.dev_mode and hasattr(data, 'stream_url') and hasattr(data, 'stream_token'):
            self.update_centrifugo_config(data.stream_url, data.stream_token)
        
        self._stream_client.send_completion(data.channel, data.response_uuid, data.thread_id, full_response)
        
        backend_data = self._response_builder.build_complete_response(
            data.response_uuid, data.thread_id, full_response, usage_info, file_url
        )
        backend_data['conversation_id'] = data.conversation_id
        
        if self.dev_mode and (not hasattr(data, 'url') or not data.url):
            return
        
        if hasattr(data, 'url') and data.url:
            self._send_to_backend(data, backend_data)
    
    def _send_to_backend(self, data, payload: Dict[str, Any]) -> None:
        """Send to backend API."""
        headers = getattr(data, 'headers', {})
        try:
            response = self._api_client.post(data.url, payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"Backend error: {response.status_code}")
        except Exception as e:
            logger.error(f"Backend request failed: {e}")
    
    def _persist_error(self, data, error_message: str, trace: Optional[str], exception: Optional[Exception]) -> None:
        """Persist error to backend."""
        error_response = self._error_handler.handle_error(data, error_message, trace, exception)
        headers = getattr(data, 'headers', {})
        
        # Send to main API
        try:
            self._api_client.post(data.url, error_response, headers=headers)
        except Exception as e:
            logger.error(f"Error persistence failed: {e}")
        
        # Send to logging API
        try:
            parsed = urlparse(data.url)
            log_url = f"{parsed.scheme}://{parsed.netloc}/api/internal/v1/logs"
            trace_info = self._error_handler.extract_trace(trace, exception)
            log_payload = self._error_handler.create_log_payload(
                error_message, trace_info, data.response_uuid,
                data.conversation_id, data.thread_id, data.channel
            )
            self._api_client.post(log_url, log_payload, headers=headers)
        except Exception as e:
            logger.error(f"Error logging failed: {e}")
