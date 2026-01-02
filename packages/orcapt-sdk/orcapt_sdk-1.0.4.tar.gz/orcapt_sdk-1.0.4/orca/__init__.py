"""
Orca Integration Package
========================

Clean, organized package for Orca platform integration.
Refactored with Clean Architecture and SOLID principles.

Architecture Layers:
- Core: Business logic and orchestration
- Domain: Models and interfaces  
- Services: Business logic services
- Infrastructure: External communication
- Helpers: Helper classes and utilities
- Factories: Object creation
- Config: Centralized configuration and constants
"""

from .config import VERSION as __version__

# Core exports
from .core import OrcaHandler, Session

# Domain models
from .domain import ChatResponse, ChatMessage, Variable, Memory

# Adapters
from .adapters import LambdaAdapter, create_lambda_handler

# Helpers and utilities
from .helpers import create_link_button_block, create_action_button_block
from .utils import (
    get_variable_value,
    get_openai_api_key,
    Variables,
    MemoryHelper,
    ForceToolsHelper,
    decode_base64_file,
    create_success_response,
    create_agent_app,
    create_hybrid_handler,
    simulate_lambda_handler
)

# Infrastructure (for advanced usage)
from .infrastructure import DevStreamClient, CentrifugoClient

# Factories (for advanced usage)
from .factories import StreamClientFactory

# Services (for advanced usage and testing)
from .services import (
    BufferManager,
    ButtonRenderer,
    LoadingMarkerProvider,
    UsageTracker,
    TracingService,
    ErrorHandler,
    ResponseBuilder
)

# Patterns (for advanced usage)
from .patterns import (
    OrcaBuilder,
    SessionBuilder,
    SessionContext,
    ResourceContext,
    timed_operation,
    suppress_exceptions,
    Middleware,
    LoggingMiddleware,
    ValidationMiddleware,
    TransformMiddleware,
    MiddlewareChain,
    MiddlewareManager,
)

# Common utilities (exceptions, decorators, logging)
from .common import (
    # Exceptions
    OrcaException,
    ConfigurationError,
    ValidationError,
    CommunicationError,
    StreamError,
    APIError,
    BufferError,
    # Decorators
    retry,
    log_execution,
    measure_time,
    handle_errors,
    deprecated,
    # Logging
    setup_logging,
    get_logger,
    enable_debug_logging,
)

# Build __all__ list
__all__ = [
    # Core
    'OrcaHandler',
    'Session',
    # Lambda
    'LambdaAdapter',
    'create_lambda_handler',
    # Domain
    'ChatResponse',
    'ChatMessage',
    'Variable',
    'Memory',
    # Helpers & Utils
    'create_link_button_block',
    'create_action_button_block',
    'create_success_response',
    'create_agent_app',
    'create_hybrid_handler',
    'simulate_lambda_handler',
    'get_variable_value',
    'get_openai_api_key',
    'Variables',
    'MemoryHelper',
    'ForceToolsHelper',
    'decode_base64_file',
    # Infrastructure
    'DevStreamClient',
    'CentrifugoClient',
    # Factories
    'StreamClientFactory',
    # Services
    'BufferManager',
    'ButtonRenderer',
    'LoadingMarkerProvider',
    'UsageTracker',
    'TracingService',
    'ErrorHandler',
    'ResponseBuilder',
    # Patterns
    'OrcaBuilder',
    'SessionBuilder',
    'SessionContext',
    'ResourceContext',
    'timed_operation',
    'suppress_exceptions',
    'Middleware',
    'LoggingMiddleware',
    'ValidationMiddleware',
    'TransformMiddleware',
    'MiddlewareChain',
    'MiddlewareManager',
    # Exceptions
    'OrcaException',
    'ConfigurationError',
    'ValidationError',
    'CommunicationError',
    'StreamError',
    'APIError',
    'BufferError',
    # Decorators
    'retry',
    'log_execution',
    'measure_time',
    'handle_errors',
    'deprecated',
    # Logging
    'setup_logging',
    'get_logger',
    'enable_debug_logging',
    # Version
    '__version__'
]

# Storage SDK
try:
    from .storage import OrcaStorage
    __all__.extend([
        'OrcaStorage',
    ])
except ImportError:
    pass

# Web framework utilities
try:
    from .web import create_orca_app, add_standard_endpoints
    __all__.extend([
        'create_orca_app',
        'add_standard_endpoints',
    ])
except ImportError:
    pass
