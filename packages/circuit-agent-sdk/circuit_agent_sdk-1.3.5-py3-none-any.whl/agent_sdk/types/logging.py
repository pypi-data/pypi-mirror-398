"""
Logging type definitions for agent operations.

This module provides types for logging operations that send timeline logs
to session traces and UIs for observability and debugging.
"""

from typing import Literal

from pydantic import Field

from .base import BaseRequest, BaseResponse


class AddLogRequest(BaseRequest):
    """
    Message request for send_log function.

    Used to send timeline logs that show up in session traces and UIs for
    observability, human-in-the-loop reviews, and debugging.

    Attributes:
        type: Message type for categorization. Available options:
            • "observe"  - General observations and status updates
            • "validate" - Validation checks and confirmations
            • "reflect"  - Analysis and reasoning about actions
            • "error"    - Error logs and failures
            • "warning"  - Warnings and potential issues
        short_message: Brief message content (max 250 characters)

    Examples:
        ```python
        # Status observation
        sdk.send_log({
            "type": "observe",
            "short_message": "Starting swap operation"
        })

        # Validation result
        sdk.send_log({
            "type": "validate",
            "short_message": "Confirmed sufficient balance"
        })

        # Error reporting
        sdk.send_log({
            "type": "error",
            "short_message": "Transaction failed: insufficient gas"
        })
        ```
    """

    type: Literal["observe", "validate", "reflect", "error", "warning"] = Field(
        ..., description="Type of log for categorization"
    )
    short_message: str = Field(..., description="Brief message content", max_length=250)


class LogResponse(BaseResponse[None]):
    """
    Response from agent.log() operations.

    This response is returned after attempting to log a message to the console
    and optionally to the backend.

    Attributes:
        success: Whether the operation was successful
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = agent.log("Processing transaction")
        if not response.success:
            print(f"Failed to log: {response.error_message}")
        ```
    """

    data: None = Field(None, description="No data returned for log operations")
