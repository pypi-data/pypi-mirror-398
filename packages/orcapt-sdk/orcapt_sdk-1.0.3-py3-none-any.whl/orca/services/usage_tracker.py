"""
Usage Tracker Service
=====================

Tracks LLM token usage and costs.
Follows Single Responsibility Principle (SRP).
"""

import logging
from typing import Dict, Optional
from ..domain.interfaces import IUsageTracker, IAPIClient

logger = logging.getLogger(__name__)


class UsageTracker(IUsageTracker):
    """
    Tracks and reports LLM usage metrics to Orca API.
    
    Responsibilities:
    - Validate usage data
    - Format usage payloads
    - Send usage data to API
    """
    
    VALID_TOKEN_TYPES = (
        "prompt", "completion", "input", "output",
        "function_call", "tool_usage", "total"
    )
    
    def __init__(self, api_client: IAPIClient):
        """
        Initialize usage tracker.
        
        Args:
            api_client: HTTP client for API communication
        """
        self._api_client = api_client
        logger.debug("UsageTracker initialized")
    
    def track(
        self,
        message_uuid: str,
        api_base_url: str,
        tokens: int,
        token_type: str,
        headers: Dict[str, str],
        cost: Optional[str] = None,
        label: Optional[str] = None
    ) -> None:
        """
        Track usage metrics and send to API.
        
        Args:
            message_uuid: Message identifier
            api_base_url: API base URL
            tokens: Token count
            token_type: Type of usage (prompt, completion, etc.)
            headers: Request headers (tenant info, etc.)
            cost: Optional cost string (e.g., "0.001")
            label: Optional human-readable label
        """
        # Validate inputs
        if not message_uuid:
            logger.warning('⚠️ No message UUID provided. Usage tracking skipped.')
            return
        
        if not self._validate_token_type(token_type):
            logger.warning(f'⚠️ Invalid token type "{token_type}". Usage tracking skipped.')
            return
        
        # Build endpoint
        endpoint = f"{api_base_url}/api/internal/v1/usages"
        
        # Build payload
        payload = self._build_payload(message_uuid, tokens, token_type, cost, label)
        
        # Log tracking info
        self._log_tracking_info(endpoint, message_uuid, token_type, tokens, cost, label)
        
        # Send to API
        try:
            response = self._api_client.post(endpoint, payload, headers=headers)
            
            logger.info('✅ Usage tracking sent successfully')
            logger.info(f'   Response Status: {response.status_code}')
            
        except Exception as error:
            # Non-blocking - don't fail the request if usage tracking fails
            logger.error(f'❌ Usage tracking failed (non-critical): {error}')
    
    def _validate_token_type(self, token_type: str) -> bool:
        """
        Validate token type.
        
        Args:
            token_type: Token type to validate
            
        Returns:
            True if valid, False otherwise
        """
        if token_type not in self.VALID_TOKEN_TYPES:
            logger.warning(
                f"Invalid token type '{token_type}'. "
                f"Valid types: {', '.join(self.VALID_TOKEN_TYPES)}"
            )
            return False
        return True
    
    def _build_payload(
        self,
        message_uuid: str,
        tokens: int,
        token_type: str,
        cost: Optional[str],
        label: Optional[str]
    ) -> Dict[str, str]:
        """
        Build usage tracking payload.
        
        Args:
            message_uuid: Message identifier
            tokens: Token count
            token_type: Type of usage
            cost: Optional cost
            label: Optional label
            
        Returns:
            Payload dictionary
        """
        payload = {
            'message_id': str(message_uuid),
            'type': str(token_type),
            'token': str(tokens)
        }
        
        if cost is not None:
            payload['cost'] = str(cost)
        
        if label is not None:
            payload['label'] = str(label)
        
        return payload
    
    def _log_tracking_info(
        self,
        endpoint: str,
        message_uuid: str,
        token_type: str,
        tokens: int,
        cost: Optional[str],
        label: Optional[str]
    ) -> None:
        """
        Log usage tracking information.
        
        Args:
            endpoint: API endpoint
            message_uuid: Message identifier
            token_type: Type of usage
            tokens: Token count
            cost: Optional cost
            label: Optional label
        """
        logger.info('📊 Sending usage tracking to Orca API...')
        logger.info(f'   Endpoint: {endpoint}')
        logger.info(f'   Message UUID: {message_uuid}')
        logger.info(f'   Token Type: {token_type}')
        logger.info(f'   Tokens: {tokens}')
        
        if cost:
            logger.info(f'   Cost: {cost}')
        if label:
            logger.info(f'   Label: {label}')

