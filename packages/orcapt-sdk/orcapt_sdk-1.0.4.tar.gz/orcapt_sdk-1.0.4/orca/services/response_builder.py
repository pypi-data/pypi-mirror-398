"""
Response Builder Service
========================

Builds API response payloads for Orca.
Follows Single Responsibility Principle (SRP).
"""

import logging
from typing import Any, Dict, Optional
from ..domain.interfaces import IResponseBuilder

logger = logging.getLogger(__name__)


class ResponseBuilder(IResponseBuilder):
    """
    Builds response payloads for Orca API.
    
    Responsibilities:
    - Build complete response payloads
    - Build error response payloads
    - Calculate token usage from response content
    - Handle both dict and object usage info
    """
    
    def __init__(self):
        logger.debug("ResponseBuilder initialized")
    
    def build_complete_response(
        self,
        response_uuid: str,
        thread_id: str,
        content: str,
        usage_info: Optional[Any] = None,
        file_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build complete response payload.
        
        Args:
            response_uuid: Response identifier
            thread_id: Thread identifier
            content: Response content
            usage_info: Optional usage information (dict or object)
            file_url: Optional file URL (for images, etc.)
            
        Returns:
            Complete response payload dict
        """
        # Extract token counts
        usage_data = self._extract_usage_data(content, usage_info)
        
        # Build base response
        response_data = {
            'uuid': response_uuid,
            'conversation_id': None,  # Will be set by caller
            'content': content,
            'role': 'assistant',
            'status': 'FINISHED',
            'usage': usage_data
        }
        
        # Add file URL if provided
        if file_url:
            response_data['file'] = file_url
        
        logger.debug(f"Built complete response: {len(content)} chars, {usage_data['total_tokens']} tokens")
        return response_data
    
    def build_error_response(
        self,
        response_uuid: str,
        conversation_id: int,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Build error response payload.
        
        Args:
            response_uuid: Response identifier
            conversation_id: Conversation identifier
            error_message: Error message
            
        Returns:
            Error response payload dict
        """
        response_data = {
            'uuid': response_uuid,
            'conversation_id': conversation_id,
            'content': error_message,
            'role': 'developer',
            'status': 'FAILED',
            'usage': {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'input_token_details': {'tokens': []},
                'output_token_details': {'tokens': []}
            }
        }
        
        logger.debug(f"Built error response: {error_message}")
        return response_data
    
    def _extract_usage_data(
        self,
        content: str,
        usage_info: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Extract usage data from usage info or estimate from content.
        
        Args:
            content: Response content
            usage_info: Optional usage information
            
        Returns:
            Usage data dict
        """
        if not usage_info:
            return self._estimate_usage(content)
        
        # Handle OpenAI CompletionUsage object
        if hasattr(usage_info, 'prompt_tokens'):
            return self._extract_from_object(usage_info)
        
        # Handle dict
        return self._extract_from_dict(usage_info, content)
    
    def _estimate_usage(self, content: str) -> Dict[str, Any]:
        """
        Estimate token usage from content length.
        
        Args:
            content: Response content
            
        Returns:
            Estimated usage data
        """
        estimated_tokens = len(content.split()) if content else 1
        input_tokens = 1
        output_tokens = estimated_tokens
        total_tokens = input_tokens + output_tokens
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_token_details': {
                'tokens': [{"token": "default", "logprob": 0.0}]
            },
            'output_token_details': {
                'tokens': [{"token": "default", "logprob": 0.0}]
            }
        }
    
    def _extract_from_object(self, usage_info: Any) -> Dict[str, Any]:
        """
        Extract usage data from OpenAI CompletionUsage object.
        
        Args:
            usage_info: OpenAI usage object
            
        Returns:
            Usage data dict
        """
        input_tokens = getattr(usage_info, 'prompt_tokens', 1)
        output_tokens = getattr(usage_info, 'completion_tokens', 1)
        total_tokens = getattr(usage_info, 'total_tokens', input_tokens + output_tokens)
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_token_details': {
                'tokens': [{"token": "default", "logprob": 0.0}] if input_tokens > 0 else []
            },
            'output_token_details': {
                'tokens': [{"token": "default", "logprob": 0.0}] if output_tokens > 0 else []
            }
        }
    
    def _extract_from_dict(self, usage_info: Dict, content: str) -> Dict[str, Any]:
        """
        Extract usage data from dict.
        
        Args:
            usage_info: Usage info dict
            content: Response content (for fallback estimation)
            
        Returns:
            Usage data dict
        """
        input_tokens = usage_info.get('prompt_tokens', 1)
        output_tokens = usage_info.get('completion_tokens', 1)
        total_tokens = usage_info.get('total_tokens', input_tokens + output_tokens)
        
        # Fallback to estimation if tokens are 0
        if input_tokens == 0 and output_tokens == 0:
            return self._estimate_usage(content)
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_token_details': {
                'tokens': [{"token": "default", "logprob": 0.0}] if input_tokens > 0 else []
            },
            'output_token_details': {
                'tokens': [{"token": "default", "logprob": 0.0}] if output_tokens > 0 else []
            }
        }

