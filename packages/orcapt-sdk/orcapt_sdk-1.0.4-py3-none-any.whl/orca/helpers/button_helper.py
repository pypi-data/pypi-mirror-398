"""
Button Helper Module
====================

Helper namespace for button operations.
Extracted from unified_handler for better separation of concerns.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ButtonHelper:
    """
    Helper namespace for button operations: session.button.*
    """
    
    def __init__(self, session):
        """
        Initialize button helper.
        
        Args:
            session: Parent session object
        """
        self._session = session
        self._pending: Optional[List[Dict[str, Any]]] = None
        self._defaults: Dict[str, Any] = {"row": 1, "color": None}
    
    def link(self, label: str, url: str, row: int = 1, color: Optional[str] = None) -> None:
        """Stream single link button immediately."""
        try:
            button = self._session._handler._button_renderer.create_link_button(
                label, url, row, color
            )
            payload = self._session._handler._button_renderer.render_button_block([button])
            self._session.stream(payload)
        except ValueError as e:
            logger.warning(f"Failed to create link button: {e}")
    
    def action(self, label: str, action_id: str, row: int = 1, color: Optional[str] = None) -> None:
        """Stream single action button immediately."""
        try:
            button = self._session._handler._button_renderer.create_action_button(
                label, action_id, row, color
            )
            payload = self._session._handler._button_renderer.render_button_block([button])
            self._session.stream(payload)
        except ValueError as e:
            logger.warning(f"Failed to create action button: {e}")
    
    def begin(self, default_row: int = 1, default_color: Optional[str] = None) -> None:
        """Start progressive button collection."""
        self._pending = []
        self._defaults = {"row": default_row or 1, "color": default_color}
        logger.debug("Progressive buttons collection started")
    
    def add_link(self, label: str, url: str, row: Optional[int] = None, color: Optional[str] = None) -> None:
        """Queue link button during progressive collection."""
        if self._pending is None:
            logger.warning("add_link() called without begin()")
            return
        
        effective_row = row if row is not None else self._defaults.get("row", 1)
        effective_color = color if color is not None else self._defaults.get("color")
        
        try:
            button = self._session._handler._button_renderer.create_link_button(
                label, url, effective_row, effective_color
            )
            self._pending.append(button)
        except ValueError as e:
            logger.warning(f"Failed to add link button: {e}")
    
    def add_action(self, label: str, action_id: str, row: Optional[int] = None, color: Optional[str] = None) -> None:
        """Queue action button during progressive collection."""
        if self._pending is None:
            logger.warning("add_action() called without begin()")
            return
        
        effective_row = row if row is not None else self._defaults.get("row", 1)
        effective_color = color if color is not None else self._defaults.get("color")
        
        try:
            button = self._session._handler._button_renderer.create_action_button(
                label, action_id, effective_row, effective_color
            )
            self._pending.append(button)
        except ValueError as e:
            logger.warning(f"Failed to add action button: {e}")
    
    # Aliases
    add_link_button = add_link
    add_action_button = add_action
    
    def end(self) -> None:
        """Finalize and stream progressive button block."""
        if self._pending is None:
            logger.warning("end() called without begin()")
            return
        
        if not self._pending:
            logger.warning("end() called but no buttons added")
            self._pending = None
            self._defaults = {"row": 1, "color": None}
            return
        
        payload = self._session._handler._button_renderer.render_button_block(self._pending)
        self._session.stream(payload)
        
        self._pending = None
        self._defaults = {"row": 1, "color": None}
        logger.debug("Progressive buttons block streamed")

