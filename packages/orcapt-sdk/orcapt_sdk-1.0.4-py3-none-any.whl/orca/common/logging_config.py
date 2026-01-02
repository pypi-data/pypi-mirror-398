"""
Logging Configuration
=====================

Centralized logging configuration for Orca SDK.
Provides consistent, structured logging across all modules.

Features:
- Structured logging with JSON support
- Multiple log levels
- File and console handlers
- Automatic log rotation
- Performance tracking
"""

import logging
import logging.handlers
import sys
from typing import Optional
from pathlib import Path


# ==================== Log Formats ====================

SIMPLE_FORMAT = "%(levelname)s: %(message)s"

DETAILED_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(filename)s:%(lineno)d - %(message)s"
)

DEBUG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(pathname)s:%(lineno)d - %(funcName)s() - %(message)s"
)


# ==================== Color Codes (for console) ====================

class LogColors:
    """ANSI color codes for log levels."""
    RESET = "\033[0m"
    DEBUG = "\033[36m"      # Cyan
    INFO = "\033[32m"       # Green
    WARNING = "\033[33m"    # Yellow
    ERROR = "\033[31m"      # Red
    CRITICAL = "\033[35m"   # Magenta


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""
    
    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{LogColors.RESET}"
        return super().format(record)


# ==================== Configuration Functions ====================

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_style: str = "simple",
    enable_colors: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Setup logging configuration for Orca SDK.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Path to log file (optional)
        format_style: Format style ('simple', 'detailed', or 'debug')
        enable_colors: Enable colored output for console
        max_file_size: Maximum log file size before rotation (bytes)
        backup_count: Number of backup files to keep
        
    Example:
        >>> from orca.logging_config import setup_logging
        >>> setup_logging(level=logging.DEBUG, log_file="orca.log")
    """
    # Select format
    formats = {
        "simple": SIMPLE_FORMAT,
        "detailed": DETAILED_FORMAT,
        "debug": DEBUG_FORMAT,
    }
    log_format = formats.get(format_style, SIMPLE_FORMAT)
    
    # Get root logger for orca
    logger = logging.getLogger("orca")
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if enable_colors and sys.stdout.isatty():
        console_formatter = ColoredFormatter(log_format)
    else:
        console_formatter = logging.Formatter(log_format)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(DETAILED_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    logger.info("Orca logging configured successfully")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello, world!")
    """
    return logging.getLogger(f"orca.{name}")


def set_level(level: int) -> None:
    """
    Set logging level for all Orca loggers.
    
    Args:
        level: Logging level
        
    Example:
        >>> from orca.logging_config import set_level
        >>> import logging
        >>> set_level(logging.DEBUG)
    """
    logger = logging.getLogger("orca")
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def disable_logging() -> None:
    """
    Disable all Orca logging.
    
    Example:
        >>> from orca.logging_config import disable_logging
        >>> disable_logging()
    """
    logging.getLogger("orca").setLevel(logging.CRITICAL + 1)


def enable_debug_logging() -> None:
    """
    Enable debug logging for troubleshooting.
    
    Example:
        >>> from orca.logging_config import enable_debug_logging
        >>> enable_debug_logging()
    """
    setup_logging(level=logging.DEBUG, format_style="debug")


# ==================== Context Manager ====================

class LoggingContext:
    """
    Context manager for temporary logging configuration.
    
    Example:
        >>> with LoggingContext(logging.DEBUG):
        ...     # Debug logging enabled here
        ...     pass
        >>> # Original level restored
    """
    
    def __init__(self, level: int):
        """
        Initialize with new logging level.
        
        Args:
            level: Temporary logging level
        """
        self.level = level
        self.original_level = logging.getLogger("orca").level
    
    def __enter__(self) -> None:
        """Enter context - set new level."""
        set_level(self.level)
    
    def __exit__(self, *args: object) -> None:
        """Exit context - restore original level."""
        set_level(self.original_level)


__all__ = [
    'setup_logging',
    'get_logger',
    'set_level',
    'disable_logging',
    'enable_debug_logging',
    'LoggingContext',
    'LogColors',
    'ColoredFormatter',
]

