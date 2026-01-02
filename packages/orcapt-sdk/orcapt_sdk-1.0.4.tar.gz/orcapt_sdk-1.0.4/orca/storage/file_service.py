"""
File Service
============

Service for file operations.
Single Responsibility: File management only.
"""

import os
from typing import Dict, Any, List, Optional, BinaryIO, Union
from pathlib import Path
from .base_client import BaseStorageClient


class FileService:
    """
    File operations service.
    
    Responsibilities:
    - Upload files
    - Download files
    - List files
    - Delete files
    - Get file info
    
    SOLID Principles:
    - SRP: Only handles file operations
    - DIP: Depends on BaseStorageClient abstraction
    - OCP: Can be extended without modification
    """
    
    def __init__(self, client: BaseStorageClient):
        """
        Initialize file service.
        
        Args:
            client: Base storage client for HTTP requests
        """
        self._client = client
    
    def upload(
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
            folder: Destination folder path
            visibility: 'public' or 'private'
            metadata: File metadata
            tags: File tags
            
        Returns:
            File information with download URL
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'File not found: {file_path}')
        
        filename = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            data = {
                'folder_path': folder,
                'visibility': visibility,
                'generate_url': 'true'
            }
            
            if metadata:
                data['metadata'] = str(metadata)
            if tags:
                data['tags'] = ','.join(tags)
            
            return self._client.post(f'/{bucket}/upload', data=data, files=files)
    
    def upload_buffer(
        self,
        bucket: str,
        buffer: BinaryIO,
        filename: str,
        folder: str = '',
        **options
    ) -> Dict[str, Any]:
        """
        Upload from memory buffer.
        
        Args:
            bucket: Bucket name
            buffer: File-like object
            filename: Filename for uploaded file
            folder: Destination folder
            **options: Additional upload options
            
        Returns:
            File information
        """
        files = {'file': (filename, buffer)}
        data = {
            'folder_path': folder,
            'visibility': options.get('visibility', 'private'),
            'generate_url': 'true'
        }
        
        return self._client.post(f'/{bucket}/upload', data=data, files=files)
    
    def list(
        self,
        bucket: str,
        folder: str = '',
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        List files in bucket.
        
        Args:
            bucket: Bucket name
            folder: Folder path filter
            page: Page number
            per_page: Items per page
            
        Returns:
            Files list with pagination
        """
        params = {
            'folder_path': folder,
            'page': page,
            'per_page': per_page
        }
        return self._client.get(f'/{bucket}/files', params=params)
    
    def download(
        self,
        bucket: str,
        key: str,
        destination: Union[str, Path]
    ) -> None:
        """
        Download file to local path.
        
        Args:
            bucket: Bucket name
            key: File key/path
            destination: Local destination path
        """
        import requests
        
        # Get download URL
        url_info = self.get_download_url(bucket, key)
        download_url = url_info.get('download_url')
        
        if not download_url:
            raise ValueError('No download URL returned')
        
        # Download file
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # Save to file
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    def get_download_url(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Get pre-signed download URL.
        
        Args:
            bucket: Bucket name
            key: File key/path
            
        Returns:
            Download URL info
        """
        return self._client.get(f'/{bucket}/download/{key}')
    
    def get_info(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            bucket: Bucket name
            key: File key/path
            
        Returns:
            File metadata
        """
        return self._client.get(f'/{bucket}/file-info/{key}')
    
    def delete(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            bucket: Bucket name
            key: File key/path
            
        Returns:
            Deletion result
        """
        return self._client.delete(f'/{bucket}/file/{key}')

