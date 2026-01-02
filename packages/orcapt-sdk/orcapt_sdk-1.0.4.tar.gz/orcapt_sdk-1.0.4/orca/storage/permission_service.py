"""
Permission Service
==================

Service for permission management.
Single Responsibility: Permissions only.
"""

from typing import Dict, Any, List
from .base_client import BaseStorageClient


class PermissionService:
    """
    Permission operations service.
    
    Responsibilities:
    - Add permissions
    - List permissions
    - Remove permissions
    
    SOLID Principles:
    - SRP: Only handles permissions
    - DIP: Depends on BaseStorageClient abstraction
    - OCP: Can be extended without modification
    """
    
    def __init__(self, client: BaseStorageClient):
        """
        Initialize permission service.
        
        Args:
            client: Base storage client for HTTP requests
        """
        self._client = client
    
    def add(
        self,
        bucket: str,
        target_type: str,
        target_id: str,
        resource_type: str = 'bucket',
        resource_path: str = '',
        can_read: bool = True,
        can_write: bool = False,
        can_list: bool = True
    ) -> Dict[str, Any]:
        """
        Add permission.
        
        Args:
            bucket: Bucket name
            target_type: 'user', 'workspace', or 'role'
            target_id: Target identifier
            resource_type: 'bucket', 'folder', or 'file'
            resource_path: Resource path
            can_read: Read permission
            can_write: Write permission
            can_list: List permission
            
        Returns:
            Permission information
        """
        payload = {
            'target_type': target_type,
            'target_id': target_id,
            'resource_type': resource_type,
            'resource_path': resource_path,
            'can_read': can_read,
            'can_write': can_write,
            'can_list': can_list
        }
        return self._client.post(f'/{bucket}/permission/add', json_data=payload)
    
    def list(self, bucket: str) -> List[Dict[str, Any]]:
        """
        List all permissions for bucket.
        
        Args:
            bucket: Bucket name
            
        Returns:
            List of permissions
        """
        response = self._client.get(f'/{bucket}/permissions')
        return response.get('permissions', [])
    
    def remove(self, permission_id: int) -> Dict[str, Any]:
        """
        Remove a permission.
        
        Args:
            permission_id: Permission ID
            
        Returns:
            Deletion result
        """
        return self._client.delete(f'/permission/{permission_id}')

