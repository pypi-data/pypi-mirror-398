"""
Stream Client Factory
=====================

Factory for creating stream clients based on environment.
Follows Factory and Strategy patterns (Open/Closed Principle).
"""

import os
import logging
from typing import Optional
from ..domain.interfaces import IStreamClient
from ..infrastructure.centrifugo_client import CentrifugoClient
from ..infrastructure.dev_stream_client import DevStreamClient

logger = logging.getLogger(__name__)


class StreamClientFactory:
    """
    Factory for creating streaming clients.
    
    Follows:
    - Factory Pattern: Encapsulates object creation
    - Strategy Pattern: Selects appropriate implementation
    - Open/Closed Principle: Easy to add new client types
    """
    
    # Registry of available client types
    _client_registry = {
        'production': CentrifugoClient,
        'dev': DevStreamClient,
    }
    
    @classmethod
    def create(
        cls,
        dev_mode: Optional[bool] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> IStreamClient:
        """
        Create appropriate stream client based on mode.
        
        Args:
            dev_mode: If True, creates DevStreamClient. If None, checks env var.
            url: Optional URL for production client
            api_key: Optional API key for production client
            
        Returns:
            IStreamClient implementation
        """
        # Determine mode
        if dev_mode is None:
            dev_mode = cls._is_dev_mode_enabled()
        
        # Select and create client
        if dev_mode:
            logger.info("🔧 Creating DEV mode stream client")
            return cls._create_dev_client()
        else:
            logger.info("🚀 Creating PRODUCTION mode stream client")
            return cls._create_production_client(url, api_key)
    
    @classmethod
    def create_custom(cls, client_type: str, **kwargs) -> IStreamClient:
        """
        Create a custom client type by name.
        
        Args:
            client_type: Type of client ('production' or 'dev')
            **kwargs: Additional arguments for client initialization
            
        Returns:
            IStreamClient implementation
            
        Raises:
            ValueError: If client_type is not registered
        """
        if client_type not in cls._client_registry:
            raise ValueError(
                f"Unknown client type: '{client_type}'. "
                f"Available types: {', '.join(cls._client_registry.keys())}"
            )
        
        client_class = cls._client_registry[client_type]
        logger.info(f"Creating custom stream client: {client_type}")
        
        return client_class(**kwargs)
    
    @classmethod
    def register_client(cls, client_type: str, client_class: type) -> None:
        """
        Register a new client type (Open/Closed Principle).
        
        Args:
            client_type: Unique identifier for client type
            client_class: Class implementing IStreamClient
            
        Raises:
            ValueError: If client doesn't implement IStreamClient
        """
        # Validate that class implements interface
        if not issubclass(client_class, IStreamClient):
            raise ValueError(
                f"Client class must implement IStreamClient interface"
            )
        
        cls._client_registry[client_type] = client_class
        logger.info(f"Registered new stream client type: {client_type}")
    
    @staticmethod
    def _is_dev_mode_enabled() -> bool:
        """
        Check if dev mode is enabled via environment variable.
        
        Returns:
            True if dev mode is enabled
        """
        dev_mode_value = os.environ.get('ORCA_DEV_MODE', 'false').lower()
        return dev_mode_value in ('true', '1', 'yes')
    
    @staticmethod
    def _create_dev_client() -> DevStreamClient:
        """
        Create development stream client.
        
        Returns:
            DevStreamClient instance
        """
        return DevStreamClient()
    
    @staticmethod
    def _create_production_client(
        url: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> CentrifugoClient:
        """
        Create production stream client.
        
        Args:
            url: Optional Centrifugo URL
            api_key: Optional Centrifugo API key
            
        Returns:
            CentrifugoClient instance
        """
        if url and api_key:
            return CentrifugoClient(url=url, api_key=api_key)
        return CentrifugoClient()

