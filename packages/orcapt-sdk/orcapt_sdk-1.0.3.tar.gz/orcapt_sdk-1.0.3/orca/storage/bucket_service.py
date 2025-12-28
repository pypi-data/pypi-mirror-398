"""
Bucket Service
==============

Service for bucket operations.
Single Responsibility: Bucket management only.
"""

from typing import Dict, Any, List, Optional
from .base_client import BaseStorageClient


class BucketService:
    """
    Bucket operations service.
    
    Responsibilities:
    - Create buckets
    - List buckets
    - Get bucket info
    - Delete buckets
    
    SOLID Principles:
    - SRP: Only handles bucket operations
    - DIP: Depends on BaseStorageClient abstraction
    - OCP: Can be extended without modification
    """
    
    def __init__(self, client: BaseStorageClient):
        """
        Initialize bucket service.
        
        Args:
            client: Base storage client for HTTP requests
        """
        self._client = client
    
    def create(
        self,
        name: str,
        visibility: str = 'private',
        encryption: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new bucket.
        
        Args:
            name: Bucket name
            visibility: 'public' or 'private'
            encryption: Enable encryption
            
        Returns:
            Bucket information
        """
        payload = {
            'bucket_name': name,
            'visibility': visibility,
            'encryption_enabled': encryption
        }
        return self._client.post('/bucket/create', json_data=payload)
    
    def list(self) -> List[Dict[str, Any]]:
        """
        List all buckets.
        
        Returns:
            List of buckets
        """
        response = self._client.get('/bucket/list')
        return response.get('buckets', [])
    
    def get_info(self, name: str) -> Dict[str, Any]:
        """
        Get bucket information.
        
        Args:
            name: Bucket name
            
        Returns:
            Bucket details
        """
        return self._client.get(f'/bucket/{name}')
    
    def delete(self, name: str, force: bool = False) -> Dict[str, Any]:
        """
        Delete a bucket.
        
        Args:
            name: Bucket name
            force: Force delete (delete all files first)
            
        Returns:
            Deletion result
        """
        params = {'force': 'true'} if force else None
        return self._client.delete(f'/bucket/{name}', params=params)

