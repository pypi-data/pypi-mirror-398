"""
App Utils - Agent Application Factory
=====================================
"""

import logging
import os
from typing import Callable, Optional

from orca.common import setup_logging, get_logger
from orca.core import OrcaHandler
from orca.web import create_orca_app, add_standard_endpoints

def create_agent_app(
    process_message_func: Callable,
    title: str = "Orca AI Agent",
    version: str = "1.0.0",
    description: str = "AI agent with Orca platform integration",
    level: int = logging.INFO
):
    """
    Creates and configures a standard Orca FastAPI application with minimal boilerplate.
    
    This factory simplifies the setup of an Orca-compatible FastAPI agent by handling
    logging, core OrcaHandler initialization, and standard endpoint registration.

    Args:
        process_message_func: The main async function to process agent messages.
        title: Application title.
        version: Application version.
        description: Application description.
        level: Logging level for the application.
        
    Returns:
        tuple: A tuple containing (fastapi_app, orca_handler)
    """
    # Initialize logging using the Orca common setup
    setup_logging(level=level, enable_colors=True)
    logger = get_logger(__name__)
    
    # Determine dev mode from environment (defaults to False)
    dev_mode = os.getenv("ORCA_DEV_MODE", "false").lower() == "true"
    
    # Initialize the core Orca handler
    orca_handler = OrcaHandler(dev_mode=dev_mode)
    
    # Create the FastAPI application instance
    app = create_orca_app(
        title=title,
        version=version,
        description=description,
        debug=dev_mode
    )
    
    # Register standard Orca endpoints (/health, /api/v1/send_message, etc.)
    add_standard_endpoints(
        app,
        conversation_manager=None,
        orca_handler=orca_handler,
        process_message_func=process_message_func,
    )
    
    logger.info(f"Agent app '{title}' v{version} initialized (dev_mode={dev_mode})")
    
    return app, orca_handler
