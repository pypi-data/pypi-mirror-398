"""
File Utilities
==============

File handling and decoding utilities.
Focused module for file operations in Orca.
"""

import base64
import tempfile
import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def decode_base64_file(file_base64: str, filename: str = None) -> Tuple[str, bool]:
    """
    Decode a base64 encoded file and save to temporary file.
    
    Args:
        file_base64: Base64 encoded file data (data URI format: "data:mime;base64,...")
        filename: Optional filename to use for extension detection
        
    Returns:
        Tuple of (file_path, is_temp_file)
        
    Example:
        file_path, is_temp = decode_base64_file(data.file_base64, data.file_name)
        # Use the file
        if is_temp:
            os.unlink(file_path)  # Clean up
    """
    if not file_base64:
        raise ValueError("file_base64 is empty")
    
    try:
        # Parse data URI: "data:audio/wav;base64,UklGRiQAAABXQVZF..."
        if file_base64.startswith('data:'):
            # Split header and data
            header, base64_data = file_base64.split(',', 1)
            # Extract MIME type
            mime_type = header.split(':')[1].split(';')[0]
            logger.info(f"Detected MIME type: {mime_type}")
        else:
            # Assume it's just base64 without data URI prefix
            base64_data = file_base64
            mime_type = None
        
        # Decode base64
        file_bytes = base64.b64decode(base64_data)
        logger.info(f"Decoded {len(file_bytes)} bytes from base64")
        
        # Determine file extension
        if filename:
            # Use extension from provided filename
            ext = os.path.splitext(filename)[1]
        elif mime_type:
            # Derive extension from MIME type
            from ..config import MIME_TYPE_MAPPING
            ext = MIME_TYPE_MAPPING.get(mime_type, '.bin')
        else:
            ext = '.bin'
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        temp_file.write(file_bytes)
        temp_file.close()
        
        logger.info(f"Saved decoded file to: {temp_file.name}")
        return temp_file.name, True
        
    except Exception as e:
        logger.error(f"Error decoding base64 file: {e}")
        raise ValueError(f"Failed to decode base64 file: {e}")

