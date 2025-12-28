"""
Button Renderer Service
=======================

Handles rendering of button blocks in Orca format.
Follows Single Responsibility Principle (SRP).
"""

import logging
from typing import Any, Dict, List, Optional, Sequence
from ..domain.interfaces import IButtonRenderer

logger = logging.getLogger(__name__)


class ButtonRenderer(IButtonRenderer):
    """
    Renders button definitions to Orca-compatible format.
    
    Responsibilities:
    - Validate button definitions
    - Build button objects
    - Render button blocks in Orca format
    """
    
    SUPPORTED_KINDS = ("link", "action")
    PREFERRED_ORDER = ["label", "id", "url", "color", "row", "tooltip", "description", "icon"]
    
    def __init__(self):
        logger.debug("ButtonRenderer initialized")
    
    def create_link_button(
        self,
        label: str,
        url: str,
        row: int = 1,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a link button definition.
        
        Args:
            label: Button label text
            url: Target URL
            row: Row number (default: 1)
            color: Button color (optional)
            
        Returns:
            Button definition dict
            
        Raises:
            ValueError: If button definition is invalid
        """
        button = self._build_button("link", label, row, color, url=url)
        if not button:
            raise ValueError(f"Invalid link button definition: label='{label}', url='{url}'")
        return button
    
    def create_action_button(
        self,
        label: str,
        action_id: str,
        row: int = 1,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an action button definition.
        
        Args:
            label: Button label text
            action_id: Action identifier
            row: Row number (default: 1)
            color: Button color (optional)
            
        Returns:
            Button definition dict
            
        Raises:
            ValueError: If button definition is invalid
        """
        button = self._build_button("action", label, row, color, action_id=action_id)
        if not button:
            raise ValueError(f"Invalid action button definition: label='{label}', action_id='{action_id}'")
        return button
    
    def render_button_block(self, buttons: Sequence[Dict[str, Any]]) -> str:
        """
        Render a list of button definitions to Orca format.
        
        Args:
            buttons: List of button definition dicts
            
        Returns:
            Formatted button block string
        """
        if not buttons:
            logger.warning("render_button_block called with empty buttons list")
            return ""
        
        block_lines: List[str] = ["[orca.buttons.start]"]
        
        for idx, button in enumerate(buttons):
            entry_lines = self._render_single_button(button)
            block_lines.extend(entry_lines)
            
            # Add blank line between buttons (except after last)
            if idx != len(buttons) - 1:
                block_lines.append("")
        
        block_lines.append("[orca.buttons.end]")
        
        payload = "\n".join(block_lines)
        if not payload.endswith("\n"):
            payload += "\n"
        
        return payload
    
    def _build_button(
        self,
        kind: str,
        label: Optional[str],
        row: Optional[int],
        color: Optional[str],
        *,
        url: Optional[str] = None,
        action_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Build a button definition dict with validation.
        
        Returns:
            Button definition dict or None if invalid
        """
        # Validate kind
        kind = (kind or "").strip().lower()
        if kind not in self.SUPPORTED_KINDS:
            logger.warning(f"Unsupported button kind '{kind}'")
            return None
        
        # Validate label
        label_text = (label or "").strip()
        if not label_text:
            logger.warning("Button missing required 'label'")
            return None
        
        # Resolve row
        resolved_row = row if isinstance(row, int) and row > 0 else 1
        
        # Build base button
        button: Dict[str, Any] = {
            "type": kind,
            "label": label_text,
            "row": resolved_row,
        }
        
        # Add color if provided
        if color:
            color_text = str(color).strip()
            if color_text:
                button["color"] = color_text
        
        # Add kind-specific fields
        if kind == "link":
            url_text = (url or "").strip() if isinstance(url, str) else ""
            if not url_text:
                logger.warning(f"Link button '{label_text}' missing required URL")
                return None
            button["url"] = url_text
        else:  # action
            action_text = (action_id or "").strip() if isinstance(action_id, str) else ""
            if not action_text:
                logger.warning(f"Action button '{label_text}' missing required ID")
                return None
            button["id"] = action_text
        
        return button
    
    def _render_single_button(self, button: Dict[str, Any]) -> List[str]:
        """
        Render a single button definition to text lines.
        
        Args:
            button: Button definition dict
            
        Returns:
            List of text lines
        """
        lines = [f"- type: {button['type']}"]
        lines.append(f"  label: {button['label']}")
        
        # Add fields in preferred order
        for field in self.PREFERRED_ORDER:
            if field == "label":
                continue
            if field in button and button[field] is not None:
                lines.append(f"  {field}: {button[field]}")
        
        # Add any remaining fields not in preferred order
        for key, value in button.items():
            if key in ("type", "label") or key in self.PREFERRED_ORDER:
                continue
            if value is None:
                continue
            lines.append(f"  {key}: {value}")
        
        return lines
    
    @staticmethod
    def normalize_button_args(button_defs: Sequence[Dict[str, Any]]) -> Sequence[Dict[str, Any]]:
        """
        Normalize button arguments (handles nested lists).
        
        Args:
            button_defs: Button definitions (may be nested)
            
        Returns:
            Flattened button definitions
        """
        if len(button_defs) == 1 and isinstance(button_defs[0], (list, tuple)):
            return button_defs[0]
        return button_defs

