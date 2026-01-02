"""
Environment Utilities
=====================

Environment variable management utilities.
Focused module for setting environment variables from Orca requests.
"""

import os
import logging
from typing import List, Union, Dict, Any

logger = logging.getLogger(__name__)


def set_env_variables(variables: Union[List[Any], None]) -> None:
    """
    Set environment variables from the variables list.
    
    Orca sends variables in format: [{"name": "OPENAI_API_KEY", "value": "..."}]
    Supports both Pydantic models and dictionaries.
    
    Args:
        variables: List of Variable objects or dictionaries from request
        
    Returns:
        None
        
    Example:
        >>> set_env_variables([{"name": "API_KEY", "value": "123"}])
    """
    if not variables:
        logger.warning("No variables provided to set_env_variables")
        return
        
    for var in variables:
        try:
            # Handle Pydantic models
            if hasattr(var, 'name') and hasattr(var, 'value'):
                os.environ[var.name] = var.value
                logger.info(f"Set environment variable: {var.name}")
            # Handle dictionaries
            elif isinstance(var, dict) and 'name' in var and 'value' in var:
                os.environ[var['name']] = var['value']
                logger.info(f"Set environment variable: {var['name']}")
            else:
                logger.warning(f"Invalid variable format: {var}")
        except Exception as e:
            logger.error(f"Error setting environment variable: {e}")

