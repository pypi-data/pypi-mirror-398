"""
Memory Utilities
================

User memory management utilities.
Focused module for handling Orca user memory data.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MemoryHelper:
    """
    Helper class for easy access to user memory data from Orca requests.
    
    Usage:
        memory = MemoryHelper(data.memory)
        user_name = memory.get_name()
        user_goals = memory.get_goals()
        user_location = memory.get_location()
    """
    
    def __init__(self, memory_data):
        """
        Initialize with memory data from request.
        
        Args:
            memory_data: Memory object, dictionary, or list from request
        """
        if memory_data is None:
            self.memory = {}
        elif hasattr(memory_data, 'dict'):
            # Pydantic model
            self.memory = memory_data.dict()
        elif isinstance(memory_data, dict):
            # Dictionary
            self.memory = memory_data
        elif isinstance(memory_data, list):
            # Empty list or old format - treat as empty memory
            self.memory = {}
        else:
            # Fallback for any other type
            self.memory = {}
    
    def get_name(self) -> str:
        """Get user's name."""
        return self.memory.get("name", "")
    
    def get_goals(self) -> List[str]:
        """Get user's goals."""
        return self.memory.get("goals", [])
    
    def get_location(self) -> str:
        """Get user's location."""
        return self.memory.get("location", "")
    
    def get_interests(self) -> List[str]:
        """Get user's interests."""
        return self.memory.get("interests", [])
    
    def get_preferences(self) -> List[str]:
        """Get user's preferences."""
        return self.memory.get("preferences", [])
    
    def get_past_experiences(self) -> List[str]:
        """Get user's past experiences."""
        return self.memory.get("past_experiences", [])
    
    def has_name(self) -> bool:
        """Check if user has a name."""
        return bool(self.get_name())
    
    def has_goals(self) -> bool:
        """Check if user has goals."""
        return len(self.get_goals()) > 0
    
    def has_location(self) -> bool:
        """Check if user has a location."""
        return bool(self.get_location())
    
    def has_interests(self) -> bool:
        """Check if user has interests."""
        return len(self.get_interests()) > 0
    
    def has_preferences(self) -> bool:
        """Check if user has preferences."""
        return len(self.get_preferences()) > 0
    
    def has_past_experiences(self) -> bool:
        """Check if user has past experiences."""
        return len(self.get_past_experiences()) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert memory to dictionary.
        
        Returns:
            Dictionary representation of memory
        """
        return {
            "name": self.get_name(),
            "goals": self.get_goals(),
            "location": self.get_location(),
            "interests": self.get_interests(),
            "preferences": self.get_preferences(),
            "past_experiences": self.get_past_experiences()
        }
    
    def is_empty(self) -> bool:
        """
        Check if memory is empty (no data).
        
        Returns:
            True if memory is empty, False otherwise
        """
        return not any([
            self.has_name(),
            self.has_goals(),
            self.has_location(),
            self.has_interests(),
            self.has_preferences(),
            self.has_past_experiences()
        ])

