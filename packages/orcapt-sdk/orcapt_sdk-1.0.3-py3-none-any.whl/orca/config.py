"""
Configuration Module
====================

Central configuration and constants for Orca SDK.
All magic strings, URLs, and configuration values in one place.

This follows the Single Source of Truth principle.
"""

from enum import Enum
from typing import Final


# ==================== Version ====================

VERSION: Final[str] = "2.0.0"


# ==================== Default Values ====================

DEFAULT_SYSTEM_PROMPT: Final[str] = """You are a helpful AI assistant. You provide clear, accurate, and helpful responses.
    
Guidelines:
- Be concise but informative
- Use markdown formatting when helpful
- If you don't know something, say so
- Be friendly and professional
- Provide examples when helpful"""


# ==================== Loading Markers ====================

class LoadingKind(str, Enum):
    """Types of loading indicators."""
    THINKING = "thinking"
    SEARCHING = "searching"
    CODING = "coding"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    GENERAL = "general"
    IMAGE = "image"
    VIDEO = "video"
    CARD = "card.list"
    MAP = "map"
    CUSTOM = "custom"


LOADING_MARKERS = {
    LoadingKind.THINKING: "🤔 Thinking...",
    LoadingKind.SEARCHING: "🔍 Searching...",
    LoadingKind.CODING: "💻 Coding...",
    LoadingKind.ANALYZING: "📊 Analyzing...",
    LoadingKind.GENERATING: "✨ Generating...",
    LoadingKind.GENERAL: "⏳ Loading...",
    LoadingKind.IMAGE: "🖼️ Loading image...",
    LoadingKind.VIDEO: "🎥 Loading video...",
    LoadingKind.CARD: "🃏 Loading card...",
    LoadingKind.MAP: "🗺️ Loading map...",
}


# ==================== Button Colors ====================

class ButtonColor(str, Enum):
    """Available button colors."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    LIGHT = "light"
    DARK = "dark"


DEFAULT_BUTTON_COLOR: Final[str] = ButtonColor.PRIMARY.value


# ==================== Button Types ====================

class ButtonType(str, Enum):
    """Types of buttons."""
    LINK = "link"
    ACTION = "action"


# ==================== Tracing Visibility ====================

class TracingVisibility(str, Enum):
    """Tracing visibility levels."""
    ALL = "all"
    DEV = "dev"
    INTERNAL = "internal"


# ==================== Token Types ====================

class TokenType(str, Enum):
    """LLM token types for usage tracking."""
    PROMPT = "prompt"
    COMPLETION = "completion"
    TOTAL = "total"
    INPUT = "input"
    OUTPUT = "output"
    EMBEDDING = "embedding"


# ==================== HTTP Configuration ====================

DEFAULT_TIMEOUT: Final[int] = 30  # seconds
DEFAULT_RETRY_ATTEMPTS: Final[int] = 3


# ==================== Stream Configuration ====================

DEFAULT_BUFFER_SIZE: Final[int] = 1000
DEFAULT_FLUSH_INTERVAL: Final[float] = 0.5  # seconds


# ==================== API Endpoints ====================

class APIEndpoint(str, Enum):
    """API endpoint paths."""
    USAGE = "/usage"
    BACKEND = "/backend"
    REPORT = "/report"


# ==================== MIME Types ====================

MIME_TYPE_MAPPING: Final[dict] = {
    'audio/wav': '.wav',
    'audio/mpeg': '.mp3',
    'audio/mp3': '.mp3',
    'audio/ogg': '.ogg',
    'audio/flac': '.flac',
    'video/mp4': '.mp4',
    'video/avi': '.avi',
    'video/quicktime': '.mov',
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'application/pdf': '.pdf',
    'text/plain': '.txt',
}


# ==================== Error Messages ====================

class ErrorMessage(str, Enum):
    """Standard error messages."""
    NO_RESPONSE_UUID = "No response_uuid found in data"
    NO_VARIABLES = "No variables provided"
    INVALID_VARIABLE_FORMAT = "Invalid variable format"
    USAGE_TRACKING_FAILED = "Usage tracking failed (non-critical)"
    BUFFER_PUSH_FAILED = "Failed to push to buffer"
    STREAM_SEND_FAILED = "Failed to send stream delta"


# ==================== Log Messages ====================

class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ==================== Feature Flags ====================

class FeatureFlag(str, Enum):
    """Feature flags for optional features."""
    DEV_MODE = "dev_mode"
    STREAMING = "streaming"
    BUFFERING = "buffering"
    USAGE_TRACKING = "usage_tracking"
    TRACING = "tracing"
    ERROR_REPORTING = "error_reporting"


# ==================== Default Configuration ====================

DEFAULT_CONFIG = {
    "dev_mode": False,
    "stream_url": None,
    "stream_token": None,
    "api_base_url": None,
    "timeout": DEFAULT_TIMEOUT,
    "retry_attempts": DEFAULT_RETRY_ATTEMPTS,
    "buffer_size": DEFAULT_BUFFER_SIZE,
    "flush_interval": DEFAULT_FLUSH_INTERVAL,
}


# ==================== Validation ====================

def validate_button_color(color: str) -> bool:
    """
    Validate button color.
    
    Args:
        color: Color string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ButtonColor(color)
        return True
    except ValueError:
        return False


def validate_loading_kind(kind: str) -> bool:
    """
    Validate loading kind.
    
    Args:
        kind: Loading kind string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        LoadingKind(kind)
        return True
    except ValueError:
        return False


def validate_token_type(token_type: str) -> bool:
    """
    Validate token type.
    
    Args:
        token_type: Token type string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        TokenType(token_type)
        return True
    except ValueError:
        return False


__all__ = [
    # Version
    'VERSION',
    # Enums
    'LoadingKind',
    'ButtonColor',
    'ButtonType',
    'TracingVisibility',
    'TokenType',
    'APIEndpoint',
    'ErrorMessage',
    'LogLevel',
    'FeatureFlag',
    # Constants
    'DEFAULT_SYSTEM_PROMPT',
    'LOADING_MARKERS',
    'DEFAULT_BUTTON_COLOR',
    'DEFAULT_TIMEOUT',
    'DEFAULT_RETRY_ATTEMPTS',
    'DEFAULT_BUFFER_SIZE',
    'DEFAULT_FLUSH_INTERVAL',
    'MIME_TYPE_MAPPING',
    'DEFAULT_CONFIG',
    # Validation
    'validate_button_color',
    'validate_loading_kind',
    'validate_token_type',
]

