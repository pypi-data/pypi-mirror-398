"""
Session Module
==============

Modular session implementation using composition.

Architecture:
- core.py: Main Session class (coordination)
- loading_ops.py: Loading operations (~50 lines)
- image_ops.py: Image operations (~40 lines)
- tracing_ops.py: Tracing operations (~80 lines)
- usage_ops.py: Usage tracking (~80 lines)
- button_ops.py: Deprecated button operations (~140 lines)

Total: ~500 lines split into 6 focused files
Average: ~83 lines per file ✅
"""

from .core import Session

__all__ = ['Session']

