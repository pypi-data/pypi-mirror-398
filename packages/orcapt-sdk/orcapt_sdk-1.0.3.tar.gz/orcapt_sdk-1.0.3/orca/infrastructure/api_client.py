"""
API Client
==========

Handles HTTP communication with external services for Orca integration.
"""

import requests
import logging
from typing import Dict, Any
from ..domain.interfaces import IAPIClient

logger = logging.getLogger(__name__)

class APIClient(IAPIClient):
    """Client for making HTTP requests to external services."""
    
    def __init__(self, default_headers: Dict[str, str] = None):
        """
        Initialize the API client.
        
        Args:
            default_headers: Default headers to use for all requests
        """
        self.default_headers = default_headers or {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        logger.info("API client initialized")
    
    def post(self, url: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> requests.Response:
        """
        Send POST request to external service.
        
        Args:
            url: URL endpoint to send request to
            data: JSON data to send in request body
            headers: Additional headers (merged with default headers)
            
        Returns:
            requests.Response: HTTP response object
        """
        # Validate inputs
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")
        if not data or not isinstance(data, dict):
            raise ValueError("Data must be a non-empty dictionary")
        
        return self._request('POST', url, data=data, headers=headers)
    
    def put(self, url: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> requests.Response:
        """
        Send PUT request to external service.
        
        url: URL endpoint to send request to
        data: JSON data to send in request body
        headers: Additional headers (merged with default headers)
        
        Returns:
            requests.Response: HTTP response object
        """
        # Validate inputs
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")
        if not data or not isinstance(data, dict):
            raise ValueError("Data must be a non-empty dictionary")
        
        return self._request('PUT', url, data=data, headers=headers)
    
    def get(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> requests.Response:
        """
        Send GET request to external service.
        
        Args:
            url: URL endpoint to send request to
            params: Query parameters
            headers: Additional headers (merged with default headers)
            
        Returns:
            requests.Response: HTTP response object
        """
        return self._request('GET', url, params=params, headers=headers)
    
    def delete(self, url: str, headers: Dict[str, str] = None) -> requests.Response:
        """
        Send DELETE request to external service.
        
        Args:
            url: URL endpoint to send request to
            headers: Additional headers (merged with default headers)
            
        Returns:
            requests.Response: HTTP response object
        """
        return self._request('DELETE', url, headers=headers)
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with common logging and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: URL endpoint
            **kwargs: Additional arguments for requests.request
            
        Returns:
            requests.Response: HTTP response object
        """
        # Ensure kwargs is a dict and not None
        if kwargs is None:
            kwargs = {}
        
        # Merge headers
        headers = self.default_headers.copy()
        if 'headers' in kwargs and kwargs['headers'] is not None:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # Convert 'data' to 'json' for JSON requests
        if 'data' in kwargs and method in ['POST', 'PUT']:
            kwargs['json'] = kwargs.pop('data')
        
        logger.info(f"=== API CLIENT {method} ===")
        logger.info(f"URL: {url}")
        logger.info(f"Headers: {headers}")
        if 'json' in kwargs:
            logger.info(f"JSON Data: {kwargs['json']}")
        if 'params' in kwargs:
            logger.info(f"Params: {kwargs['params']}")
        
        try:
            logger.info(f"About to call requests.request with method={method}, url={url}, kwargs={kwargs}")
            logger.info(f"kwargs type: {type(kwargs)}")
            logger.info(f"kwargs keys: {list(kwargs.keys()) if kwargs else 'None'}")
            for key, value in kwargs.items():
                logger.info(f"  {key}: {type(value)} = {value}")
            
            response = requests.request(method, url, **kwargs)
            
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            logger.info(f"Response Content: {response.text}")
            logger.info(f"=== END API CLIENT {method} ===")
            
            return response
            
        except Exception as e:
            logger.error(f"Error making {method} request to {url}: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            logger.error(f"Full exception details: {str(e)}")
            raise
