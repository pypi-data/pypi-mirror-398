"""
Storage Module
==============

Orca Storage SDK with clean architecture.

Architecture:
- base_client.py: Low-level HTTP client (SRP)
- bucket_service.py: Bucket operations (SRP)
- file_service.py: File operations (SRP)
- permission_service.py: Permission operations (SRP)
- client.py: Facade for all operations (Facade Pattern)

SOLID Principles:
- SRP: Each service has single responsibility
- OCP: Services are open for extension
- LSP: Services implement clear contracts
- ISP: Services expose only relevant methods
- DIP: All depend on abstractions
"""

from .client import OrcaStorage, OrcaStorageException
from .base_client import BaseStorageClient, StorageException
from .bucket_service import BucketService
from .file_service import FileService
from .permission_service import PermissionService

__all__ = [
    # Main client (Facade)
    'OrcaStorage',
    'OrcaStorageException',
    
    # Base client (for advanced usage)
    'BaseStorageClient',
    'StorageException',
    
    # Services (for advanced usage/testing)
    'BucketService',
    'FileService',
    'PermissionService',
]
