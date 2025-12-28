"""
Orca Storage Client
====================

Facade for Orca Storage operations.
Delegates to specialized services (SOLID principles).
"""

import os
from typing import Optional, Dict, Any, List, BinaryIO, Union
from pathlib import Path

from .base_client import BaseStorageClient, StorageException
from .bucket_service import BucketService
from .file_service import FileService
from .permission_service import PermissionService


# Re-export exception
class OrcaStorageException(StorageException):
    """Alias for StorageException (backward compatibility)"""
    pass


class OrcaStorage:
    """
    Orca Storage S3-Compatible Client (Facade Pattern).
    
    This class delegates to specialized services:
    - BucketService: Bucket operations
    - FileService: File operations
    - PermissionService: Permission operations
    
    SOLID Principles Applied:
    - SRP: Each service has single responsibility
    - OCP: Services can be extended without modifying this class
    - LSP: Services implement clear contracts
    - ISP: Services expose only relevant methods
    - DIP: Depends on abstractions (BaseStorageClient)
    
    Example:
        >>> storage = OrcaStorage(
        ...     workspace='my-workspace',
        ...     token='my-token',
        ...     base_url='https://api.example.com/api/v1/storage'
        ... )
        >>> 
        >>> # Create bucket
        >>> bucket = storage.create_bucket('my-bucket')
        >>> 
        >>> # Upload file
        >>> file = storage.upload_file('my-bucket', 'report.pdf', 'reports/')
        >>> 
        >>> # List files
        >>> files = storage.list_files('my-bucket')
    """
    
    def __init__(
        self,
        workspace: str,
        token: str,
        base_url: str = 'http://localhost:8000/api/v1/storage',
        mode: str = 'dev',
        timeout: int = 30
    ):
        """
        Initialize Orca Storage client.
        
        Args:
            workspace: Workspace slug/handle
            token: API token
            base_url: Storage API base URL
            mode: 'dev' or 'prod'
            timeout: Request timeout in seconds
        """
        # Initialize base client
        self._client = BaseStorageClient(
            workspace=workspace,
            token=token,
            base_url=base_url,
            mode=mode,
            timeout=timeout
        )
        
        # Initialize services (Dependency Injection)
        self._buckets = BucketService(self._client)
        self._files = FileService(self._client)
        self._permissions = PermissionService(self._client)
    
    # ==================== Bucket Operations ====================
    
    def create_bucket(
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
        return self._buckets.create(name, visibility, encryption)
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all buckets."""
        return self._buckets.list()
    
    def get_bucket_info(self, name: str) -> Dict[str, Any]:
        """Get bucket information."""
        return self._buckets.get_info(name)
    
    def delete_bucket(self, name: str, force: bool = False) -> Dict[str, Any]:
        """Delete a bucket."""
        return self._buckets.delete(name, force)
    
    # ==================== File Operations ====================
    
    def upload_file(
        self,
        bucket: str,
        file_path: Union[str, Path],
        folder: str = '',
        visibility: str = 'private',
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file.
        
        Args:
            bucket: Bucket name
            file_path: Path to local file
            folder: Destination folder
            visibility: 'public' or 'private'
            metadata: File metadata
            tags: File tags
            
        Returns:
            File information with download URL
        """
        return self._files.upload(bucket, file_path, folder, visibility, metadata, tags)
    
    def upload_buffer(
        self,
        bucket: str,
        buffer: BinaryIO,
        filename: str,
        folder: str = '',
        **options
    ) -> Dict[str, Any]:
        """Upload from memory buffer."""
        return self._files.upload_buffer(bucket, buffer, filename, folder, **options)
    
    def list_files(
        self,
        bucket: str,
        folder: str = '',
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """List files in bucket."""
        return self._files.list(bucket, folder, page, per_page)
    
    def download_file(
        self,
        bucket: str,
        key: str,
        destination: Union[str, Path]
    ) -> None:
        """Download file to local path."""
        self._files.download(bucket, key, destination)
    
    def get_download_url(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get pre-signed download URL."""
        return self._files.get_download_url(bucket, key)
    
    def get_file_info(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get file information."""
        return self._files.get_info(bucket, key)
    
    def delete_file(self, bucket: str, key: str) -> Dict[str, Any]:
        """Delete a file."""
        return self._files.delete(bucket, key)
    
    # ==================== Permission Operations ====================
    
    def add_permission(
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
        """Add permission."""
        return self._permissions.add(
            bucket, target_type, target_id,
            resource_type, resource_path,
            can_read, can_write, can_list
        )
    
    def list_permissions(self, bucket: str) -> List[Dict[str, Any]]:
        """List bucket permissions."""
        return self._permissions.list(bucket)
    
    def remove_permission(self, permission_id: int) -> Dict[str, Any]:
        """Remove a permission."""
        return self._permissions.remove(permission_id)
