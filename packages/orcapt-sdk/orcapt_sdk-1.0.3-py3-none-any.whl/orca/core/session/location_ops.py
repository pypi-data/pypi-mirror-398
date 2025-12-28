"""
Location Operations
===================

Handles location/map operations for a session.
Ultra-focused: ONLY location handling.
"""

import logging

logger = logging.getLogger(__name__)


class LocationOperations:
    """
    Manages location/map streaming.
    
    Ultra-focused on location operations only.
    Single Responsibility: Location/map handling.
    """
    
    def __init__(self, stream_func):
        """
        Initialize location operations.
        
        Args:
            stream_func: Function to stream content
        """
        self._stream = stream_func
    
    def send(self, coordinates: str) -> None:
        """
        Stream location with Orca markers.
        
        Args:
            coordinates: Location coordinates (e.g., "35.6892, 51.3890" or lat,lng)
        """
        if not coordinates:
            logger.warning("Location coordinates are empty, skipping")
            return
        
        payload = f"[orca.location.start]{coordinates}[orca.location.end]"
        self._stream(payload)
    
    def send_coordinates(self, lat: float, lng: float) -> None:
        """
        Stream location with coordinates.
        
        Args:
            lat: Latitude
            lng: Longitude
        """
        coordinates = f"{lat}, {lng}"
        self.send(coordinates)

