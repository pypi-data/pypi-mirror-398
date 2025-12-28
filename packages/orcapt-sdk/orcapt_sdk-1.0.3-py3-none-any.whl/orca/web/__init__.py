"""
Orca Web Package
================

Web framework utilities for creating FastAPI applications with Orca integration.
Provides standard endpoints, middleware, and app factory functions.
"""

from .app_factory import create_orca_app
from .endpoints import add_standard_endpoints

__all__ = [
    'create_orca_app',
    'add_standard_endpoints'
]
