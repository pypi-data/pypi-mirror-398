"""
Centrifugo Client
================

Handles real-time messaging via Centrifugo for Orca integration.
"""

import os
import requests
import logging
from typing import Dict, Any
from ..domain.interfaces import IStreamClient

logger = logging.getLogger(__name__)

class CentrifugoClient(IStreamClient):
    """Client for communicating with Centrifugo real-time messaging service."""
    
    def __init__(self, url: str = None, api_key: str = None):
        """
        Initialize the Centrifugo client.
        
        Args:
            url: Centrifugo server URL (defaults to environment variable)
            api_key: Centrifugo API key (defaults to environment variable)
        """
        self.url = url or os.environ.get('CENTRIFUGO_URL', 'http://centrifugo:8000')
        self.api_key = api_key or os.environ.get('CENTRIFUGO_API_KEY', 'my_api_key')
        
        logger.info(f"Centrifugo client initialized with URL: {self.url}")
    
    def update_config(self, url: str, api_key: str):
        """
        Update the Centrifugo configuration dynamically.
        
        Args:
            url: New Centrifugo server URL
            api_key: New Centrifugo API key
        """
        self.url = url
        self.api_key = api_key
        logger.info(f"Centrifugo client configuration updated - URL: {self.url}")
    
    def send(self, channel: str, data: Dict[str, Any]):
        """
        Send data to a Centrifugo channel.
        
        Args:
            channel: Channel name to send to
            data: Data to send
        """
        try:
            headers = {
                'X-API-Key': self.api_key,
                'Authorization': f'apikey {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            payload = {
                'channel': channel,
                'data': data,
            }
            
            response = requests.post(
                f'{self.url}/api/publish',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Successfully sent message to channel: {channel}")
            else:
                logger.warning(f"Failed to send message to channel {channel}. Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending message to Centrifugo channel {channel}: {e}")
    
    def send_delta(self, channel: str, uuid: str, thread_id: str, delta: str):
        """
        Send a streaming delta message.
        
        Args:
            channel: Channel name
            uuid: Response UUID
            thread_id: Thread ID
            delta: Text delta to send
        """
        data = {
            'delta': delta,
            'finished': False,
            'uuid': uuid,
            'thread_id': thread_id
        }
        self.send(channel, data)
    
    def send_completion(self, channel: str, uuid: str, thread_id: str, full_response: str):
        """
        Send a completion signal.
        
        Args:
            channel: Channel name
            uuid: Response UUID
            thread_id: Thread ID
            full_response: Complete response text
        """
        data = {
            'finished': True,
            'uuid': uuid,
            'thread_id': thread_id,
            'full_response': full_response
        }
        self.send(channel, data)
    
    def send_error(self, channel: str, uuid: str, thread_id: str, error_message: str):
        """
        Send an error notification.
        
        Args:
            channel: Channel name
            uuid: Response UUID
            thread_id: Thread ID
            error_message: Error message
        """
        data = {
            'error': True,
            'content': error_message,
            'finished': True,
            'uuid': uuid,
            'thread_id': thread_id,
            'status': 'FAILED',
            'role': 'developer'
        }
        self.send(channel, data)
