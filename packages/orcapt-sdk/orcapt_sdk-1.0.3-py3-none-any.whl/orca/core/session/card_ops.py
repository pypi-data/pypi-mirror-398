"""
Card List Operations
====================

Handles card list operations for a session.
Ultra-focused: ONLY card list handling.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class CardListOperations:
    """
    Manages card list streaming.
    
    Ultra-focused on card list operations only.
    Single Responsibility: Card list handling.
    """
    
    def __init__(self, stream_func):
        """
        Initialize card list operations.
        
        Args:
            stream_func: Function to stream content
        """
        self._stream = stream_func
    
    def send(self, cards: List[Dict[str, Any]]) -> None:
        """
        Stream card list with Orca markers.
        
        Args:
            cards: List of card dictionaries with keys like:
                   - photo: Image URL (optional)
                   - header: Card title (optional)
                   - subheader: Card description (optional)
                   - text: Additional content (optional)
        """
        if not cards:
            logger.warning("Card list is empty, skipping")
            return
        
        # Build YAML-like format
        payload = "[orca.list.card.start]\n"
        
        for card in cards:
            payload += "- "
            card_items = []
            
            if card.get("photo"):
                card_items.append(f"photo: {card['photo']}")
            if card.get("header"):
                card_items.append(f"header: {card['header']}")
            if card.get("subheader"):
                card_items.append(f"subheader: {card['subheader']}")
            if card.get("text"):
                card_items.append(f"text: {card['text']}")
            
            payload += "\n  ".join(card_items) + "\n"
        
        payload += "[orca.list.card.end]"
        self._stream(payload)

