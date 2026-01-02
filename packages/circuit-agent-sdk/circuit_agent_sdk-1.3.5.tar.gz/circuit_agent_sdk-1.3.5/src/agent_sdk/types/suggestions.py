"""
Suggestion management type definitions for agent operations.

This module provides types for managing suggested transactions in manual mode,
including clearing pending suggestions.
"""

from pydantic import Field

from .base import BaseResponse


class ClearSuggestionsResponse(BaseResponse[None]):
    """
    Response from clear_suggested_transactions() operations.

    Returned after clearing (soft deleting) all pending suggested transactions
    for the session.

    Attributes:
        success: Whether the operation was successful
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = agent.clear_suggested_transactions()
        if response.success:
            print("Cleared all pending suggestions")
        else:
            print(f"Failed: {response.error}")
        ```
    """

    data: None = Field(None, description="No data returned for clear operations")
