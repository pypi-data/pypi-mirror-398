"""
Response Handler Utils
======================

Response creation utilities.

DEPRECATED: Use ResponseBuilder service instead.
These functions are kept for backwards compatibility only.
"""

from ..domain.models import ChatResponse
from ..services import ResponseBuilder

# Singleton instance for backwards compatibility
_response_builder = ResponseBuilder()


def create_success_response(response_uuid: str, thread_id: str, message: str = "Processing started") -> ChatResponse:
    """
    Create a standard success response for Orca.
    
    DEPRECATED: This is a legacy function kept for backwards compatibility.
    """
    return ChatResponse(
        status="success",
        message=message,
        response_uuid=response_uuid,
        thread_id=thread_id
    )


def create_complete_response(response_uuid: str, thread_id: str, content: str, usage_info=None, file_url=None) -> dict:
    """
    Create a complete response with all required fields for Orca API.
    
    DEPRECATED: Use ResponseBuilder.build_complete_response() instead.
    This function delegates to ResponseBuilder for consistency.
    """
    return _response_builder.build_complete_response(
        response_uuid,
        thread_id,
        content,
        usage_info,
        file_url
    )

