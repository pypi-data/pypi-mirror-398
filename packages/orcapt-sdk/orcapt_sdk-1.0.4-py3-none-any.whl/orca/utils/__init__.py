"""
Utils Module
============

Modular utility functions.
Organized into focused submodules for better maintainability.

Submodules:
- variables: Variable management and extraction
- memory: User memory management
- tools: Force tools handling
- files: File operations and decoding
- prompts: Prompt and message formatting
- environment: Environment variable management
- response: Response utilities (legacy)
"""

# Variables
from .variables import Variables, get_variable_value, get_openai_api_key

# Memory
from .memory import MemoryHelper

# Tools
from .tools import ForceToolsHelper

# Files
from .files import decode_base64_file

# Prompts (optional, not exported by default)
# from .prompts import format_system_prompt, format_messages_for_openai

# Environment (optional, not exported by default)
# from .environment import set_env_variables

# Response (legacy, kept for backwards compatibility)
from .response_handler import create_success_response
from .lambda_utils import create_hybrid_handler, simulate_lambda_handler
from .app_utils import create_agent_app

__all__ = [
    # Variables
    'Variables',
    'get_variable_value',
    'get_openai_api_key',
    # Memory
    'MemoryHelper',
    # Tools
    'ForceToolsHelper',
    # Files
    'decode_base64_file',
    # Response (legacy)
    'create_success_response',
    # Lambda
    'create_hybrid_handler',
    'simulate_lambda_handler',
    # App
    'create_agent_app',
]
