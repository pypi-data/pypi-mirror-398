"""
Tools Utilities
===============

Tool forcing utilities.
Focused module for handling force_tools in Orca requests.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ForceToolsHelper:
    """
    Helper class for easy access to force_tools data from Orca requests.
    
    Usage:
        tools = ForceToolsHelper(data.force_tools)
        if tools.has('search'):
            # Perform search
            pass
        if tools.has('code'):
            # Use code tool
            pass
    """
    
    def __init__(self, force_tools: Optional[List[str]] = None):
        """
        Initialize with force_tools list from request.
        
        Args:
            force_tools: List of tool names from request (e.g., ['code', 'search', 'xyz'])
        """
        self.tools = force_tools if force_tools is not None else []
    
    def has(self, tool_name: str) -> bool:
        """
        Check if a specific tool is forced.
        
        Args:
            tool_name: Name of the tool to check (e.g., 'code', 'search')
            
        Returns:
            True if tool is forced, False otherwise
        """
        return tool_name in self.tools
    
    def get_all(self) -> List[str]:
        """
        Get all forced tools.
        
        Returns:
            List of forced tool names
        """
        return self.tools.copy()
    
    def is_empty(self) -> bool:
        """
        Check if no tools are forced.
        
        Returns:
            True if no tools are forced, False otherwise
        """
        return len(self.tools) == 0
    
    def count(self) -> int:
        """
        Get count of forced tools.
        
        Returns:
            Number of forced tools
        """
        return len(self.tools)

