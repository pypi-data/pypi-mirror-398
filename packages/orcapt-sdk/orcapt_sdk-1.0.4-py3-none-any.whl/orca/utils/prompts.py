"""
Prompt Utilities
================

Prompt formatting utilities.
Focused module for formatting prompts and messages.
"""

import logging
from typing import List, Dict, Optional
from ..config import DEFAULT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def format_system_prompt(
    system_message: Optional[str] = None,
    project_system_message: Optional[str] = None
) -> str:
    """
    Format the system prompt for OpenAI API.
    
    Args:
        system_message: Custom system message
        project_system_message: Project-specific system message
        
    Returns:
        Formatted system prompt string
        
    Example:
        >>> prompt = format_system_prompt("You are a helpful assistant")
        >>> print(prompt)
    """
    # Use project system message if available, then custom system message, then default
    return project_system_message or system_message or DEFAULT_SYSTEM_PROMPT


def format_messages_for_openai(
    system_prompt: str,
    conversation_history: List[Dict[str, str]],
    current_message: str
) -> List[Dict[str, str]]:
    """
    Format messages for OpenAI API call.
    
    Args:
        system_prompt: System prompt to use
        conversation_history: Previous conversation messages
        current_message: Current user message
        
    Returns:
        List of messages formatted for OpenAI API
    """
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history (excluding the current user message)
    for hist_msg in conversation_history[:-1]:  # Exclude the last message (current user message)
        messages.append(hist_msg)
    
    # Add current user message
    messages.append({"role": "user", "content": current_message})
    
    return messages

