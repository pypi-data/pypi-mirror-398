"""
Button Utilities
================

Standalone utility functions for button creation.
"""

from typing import Optional
from ..services import ButtonRenderer


def create_link_button_block(label: str, url: str, row: int = 1, color: Optional[str] = None) -> str:
    """
    Create a markdown block representing a single link button.
    
    Args:
        label: Button label
        url: Target URL
        row: Row number
        color: Optional color
        
    Returns:
        Formatted button block string
    """
    renderer = ButtonRenderer()
    button = renderer.create_link_button(label, url, row, color)
    return renderer.render_button_block([button])


def create_action_button_block(label: str, action_id: str, row: int = 1, color: Optional[str] = None) -> str:
    """
    Create a markdown block representing a single action button.
    
    Args:
        label: Button label
        action_id: Action identifier
        row: Row number
        color: Optional color
        
    Returns:
        Formatted button block string
    """
    renderer = ButtonRenderer()
    button = renderer.create_action_button(label, action_id, row, color)
    return renderer.render_button_block([button])

