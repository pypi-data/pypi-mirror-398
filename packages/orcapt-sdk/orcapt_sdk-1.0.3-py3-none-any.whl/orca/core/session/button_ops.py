"""
Button Operations (Deprecated)
===============================

Deprecated button operations for backwards compatibility.
Delegates to ButtonHelper.

DEPRECATED: Use session.button.* methods instead.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ButtonOperations:
    """
    Deprecated button operations wrapper.
    
    Maintains backwards compatibility.
    Delegates all calls to ButtonHelper.
    """
    
    def __init__(self, button_helper):
        """
        Initialize with button helper.
        
        Args:
            button_helper: ButtonHelper instance
        """
        self._button_helper = button_helper
        self._handler = None  # Will be set by Session
        self._stream = None   # Will be set by Session
    
    def set_context(self, handler, stream_func):
        """Set handler and stream function context."""
        self._handler = handler
        self._stream = stream_func
    
    # Deprecated single button methods
    def button_link(self, label: str, url: str, row: int = 1, color: Optional[str] = None) -> None:
        """Deprecated: Use session.button.link()"""
        self._button_helper.link(label, url, row=row, color=color)
    
    def button_action(self, label: str, action_id: str, row: int = 1, color: Optional[str] = None) -> None:
        """Deprecated: Use session.button.action()"""
        self._button_helper.action(label, action_id, row=row, color=color)
    
    # Deprecated progressive methods
    def buttons_begin(self, default_row: int = 1, default_color: Optional[str] = None) -> None:
        """Deprecated: Use session.button.begin()"""
        self._button_helper.begin(default_row=default_row, default_color=default_color)
    
    def buttons_add_link(self, label: str, url: str, row: Optional[int] = None, color: Optional[str] = None) -> None:
        """Deprecated: Use session.button.add_link()"""
        self._button_helper.add_link(label, url, row=row, color=color)
    
    def buttons_add_action(self, label: str, action_id: str, row: Optional[int] = None, color: Optional[str] = None) -> None:
        """Deprecated: Use session.button.add_action()"""
        self._button_helper.add_action(label, action_id, row=row, color=color)
    
    def buttons_add_link_button(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.add_link()"""
        self._button_helper.add_link(*args, **kwargs)
    
    def buttons_add_action_button(self, *args, **kwargs) -> None:
        """Deprecated: Use session.button.add_action()"""
        self._button_helper.add_action(*args, **kwargs)
    
    def buttons_end(self) -> None:
        """Deprecated: Use session.button.end()"""
        self._button_helper.end()
    
    def buttons(self, *button_defs: Dict[str, Any], defaults: Optional[Dict[str, Any]] = None) -> None:
        """Deprecated dictionary-based button API."""
        if not button_defs or not self._handler:
            return
        
        button_iterable = self._handler._button_renderer.normalize_button_args(button_defs)
        default_row = (defaults or {}).get("row", 1)
        default_color = (defaults or {}).get("color")
        collected: List[Dict[str, Any]] = []
        
        for idx, raw_button in enumerate(button_iterable, start=1):
            if not isinstance(raw_button, dict):
                continue
            
            kind = raw_button.get("type") or raw_button.get("button_type")
            if not kind:
                if "url" in raw_button:
                    kind = "link"
                elif "id" in raw_button:
                    kind = "action"
            
            label = raw_button.get("label") or raw_button.get("title") or raw_button.get("text")
            row = raw_button.get("row", default_row)
            color = raw_button["color"] if "color" in raw_button else default_color
            
            try:
                if kind == "link":
                    button = self._handler._button_renderer.create_link_button(
                        label, raw_button.get("url"), row, color
                    )
                elif kind == "action":
                    button = self._handler._button_renderer.create_action_button(
                        label, raw_button.get("id"), row, color
                    )
                else:
                    continue
                
                for key, value in raw_button.items():
                    if key in ("type", "label", "button_type", "title", "text", "id", "url", "row", "color"):
                        continue
                    if value is not None:
                        button[key] = value
                
                collected.append(button)
            except ValueError:
                continue
        
        if collected and self._stream:
            payload = self._handler._button_renderer.render_button_block(collected)
            self._stream(payload)

