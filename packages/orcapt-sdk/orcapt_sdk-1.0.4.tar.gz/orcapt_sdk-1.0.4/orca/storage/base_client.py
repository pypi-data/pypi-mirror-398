"""
Storage Base Client
===================

Low-level HTTP client for storage API.
Single Responsibility: HTTP communication only.
"""

import requests
from typing import Optional, Dict, Any


class StorageException(Exception):
    """Base exception for storage errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class BaseStorageClient:
    """
    Base HTTP client for storage API.
    
    Responsibilities:
    - HTTP request handling
    - Error handling
    - Authentication headers
    
    SOLID Principles:
    - SRP: Only handles HTTP communication
    - OCP: Can be extended without modification
    - DIP: Depends on abstractions (requests library)
    """
    
    def __init__(
        self,
        workspace: str,
        token: str,
        base_url: str,
        mode: str = 'dev',
        timeout: int = 30
    ):
        """
        Initialize base client.
        
        Args:
            workspace: Workspace identifier
            token: API token
            base_url: Base API URL
            mode: Environment mode (dev/prod)
            timeout: Request timeout in seconds
        """
        if not workspace or not token:
            raise ValueError('Workspace and token are required')
        
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {
            'x-workspace': workspace,
            'x-token': token,
            'x-mode': mode
        }
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            data: Form data
            files: Files to upload
            params: Query parameters
            json_data: JSON payload
            
        Returns:
            Response JSON
            
        Raises:
            StorageException: On API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Prepare request kwargs
            kwargs = {
                'headers': self.headers.copy(),
                'timeout': self.timeout
            }
            
            if params:
                kwargs['params'] = params
            if json_data:
                kwargs['json'] = json_data
                kwargs['headers']['Content-Type'] = 'application/json'
            if data:
                kwargs['data'] = data
            if files:
                kwargs['files'] = files
                # Remove Content-Type for multipart
                kwargs['headers'].pop('Content-Type', None)
            
            # Make request
            response = requests.request(method, url, **kwargs)
            
            # Handle response
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get('message', f'HTTP {response.status_code}')
                except:
                    message = f'HTTP {response.status_code}: {response.text[:100]}'
                
                raise StorageException(
                    message,
                    status_code=response.status_code,
                    response=error_data if 'error_data' in locals() else None
                )
            
            # Return JSON response
            try:
                return response.json()
            except:
                return {'status': 'success'}
                
        except requests.exceptions.RequestException as e:
            raise StorageException(f'Request failed: {str(e)}') from e
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request"""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request"""
        return self.request('POST', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        return self.request('DELETE', endpoint, **kwargs)

