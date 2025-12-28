"""
Usage Operations
================

Handles usage tracking operations for a session.
Ultra-focused: ONLY usage/token tracking.
"""

import logging
import os
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class UsageOperations:
    """
    Manages usage/token tracking.
    
    Ultra-focused on usage tracking only.
    Single Responsibility: Token usage tracking.
    """
    
    def __init__(self, handler, data):
        """
        Initialize usage operations.
        
        Args:
            handler: Parent handler (for accessing usage tracker)
            data: Request data
        """
        self._handler = handler
        self._data = data
    
    def track(
        self,
        tokens: int,
        token_type: str,
        cost: Optional[str] = None,
        label: Optional[str] = None
    ) -> None:
        """
        Track LLM token usage.
        
        Args:
            tokens: Token count
            token_type: Type (prompt, completion, etc.)
            cost: Optional cost string
            label: Optional label
        """
        try:
            # Get message UUID
            message_uuid = getattr(self._data, 'response_uuid', None)
            if not message_uuid:
                logger.warning('⚠️ No response_uuid. Usage tracking skipped.')
                return
            
            # Extract API base URL
            api_base_url = self._extract_api_base_url()
            
            # Get headers
            headers = getattr(self._data, 'headers', {})
            
            # Track usage
            self._handler._usage_tracker.track(
                message_uuid,
                api_base_url,
                tokens,
                token_type,
                headers,
                cost,
                label
            )
            
        except Exception as error:
            logger.error(f'❌ Usage tracking failed (non-critical): {error}')
    
    def _extract_api_base_url(self) -> str:
        """
        Extract API base URL from request data.
        
        Returns:
            API base URL string
        """
        if hasattr(self._data, 'url') and self._data.url:
            parsed = urlparse(self._data.url)
            return f"{parsed.scheme}://{parsed.netloc}"
        
        return os.environ.get('ORCA_API_BASE_URL', 'http://localhost')

