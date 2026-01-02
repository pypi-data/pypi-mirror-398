"""
Variables Utilities
===================

Variable management and extraction utilities.
Focused module for handling Orca request variables.
"""

import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class Variables:
    """
    Helper class for easy access to variables from Orca requests.
    
    Usage:
        variables = Variables(data.variables)
        openai_key = variables.get("OPENAI_API_KEY")
        anthropic_key = variables.get("ANTHROPIC_API_KEY")
    """
    
    def __init__(self, variables_list):
        """
        Initialize with a list of Variable objects or dictionaries.
        
        Args:
            variables_list: List of Variable objects or dictionaries from request
        """
        self.variables_list = variables_list or []
        self._cache = {}
        
        # Build a cache for faster lookups
        for var in self.variables_list:
            try:
                # Handle Pydantic models
                if hasattr(var, 'name') and hasattr(var, 'value'):
                    self._cache[var.name] = var.value
                # Handle dictionaries
                elif isinstance(var, dict) and 'name' in var and 'value' in var:
                    self._cache[var['name']] = var['value']
            except Exception as e:
                logger.error(f"Error processing variable: {e}")
    
    def get(self, variable_name: str) -> Optional[str]:
        """
        Get a variable value by name.
        
        Args:
            variable_name: Name of the variable to get
            
        Returns:
            Variable value string or None if not found
        """
        return self._cache.get(variable_name)
    
    def has(self, variable_name: str) -> bool:
        """
        Check if a variable exists.
        
        Args:
            variable_name: Name of the variable to check
            
        Returns:
            True if variable exists, False otherwise
        """
        return variable_name in self._cache
    
    def list_names(self) -> List[str]:
        """
        Get list of all variable names.
        
        Returns:
            List of variable names
        """
        return list(self._cache.keys())
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert all variables to a dictionary.
        
        Returns:
            Dictionary of variable names to values
        """
        return self._cache.copy()


def get_variable_value(variables, variable_name: str) -> Optional[str]:
    """
    Extract a specific variable value from variables list by name.
    
    Supports both Pydantic models and dictionaries.
    
    Args:
        variables: List of Variable objects or dictionaries from request
        variable_name: Name of the variable to extract (e.g., "OPENAI_API_KEY")
        
    Returns:
        Variable value string or None if not found
    """
    if not variables:
        logger.warning(f"No variables provided to get_variable_value for '{variable_name}'")
        return None
        
    for var in variables:
        try:
            # Handle Pydantic models
            if hasattr(var, 'name') and hasattr(var, 'value'):
                if var.name == variable_name:
                    logger.info(f"Found variable '{variable_name}'")
                    return var.value
            # Handle dictionaries
            elif isinstance(var, dict) and 'name' in var and 'value' in var:
                if var['name'] == variable_name:
                    logger.info(f"Found variable '{variable_name}'")
                    return var['value']
            else:
                logger.warning(f"Invalid variable format: {var}")
        except Exception as e:
            logger.error(f"Error processing variable: {e}")
    
    logger.warning(f"Variable '{variable_name}' not found in variables")
    return None


def get_openai_api_key(variables) -> Optional[str]:
    """
    Extract OpenAI API key from variables list.
    
    This is a convenience function that uses get_variable_value internally.
    
    Args:
        variables: List of Variable objects or dictionaries from request
        
    Returns:
        OpenAI API key string or None if not found
    """
    return get_variable_value(variables, "OPENAI_API_KEY")

