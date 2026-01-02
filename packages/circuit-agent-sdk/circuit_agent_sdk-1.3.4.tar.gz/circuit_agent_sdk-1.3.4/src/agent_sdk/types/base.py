"""
Base Pydantic models for all SDK types.

This module provides standardized base classes that ensure consistent
validation behavior across all request and response models.
"""

from pydantic import BaseModel, ConfigDict, Field


class BaseRequest(BaseModel):
    """
    Base class for all request models - strict validation, no extras allowed.

    All request types should inherit from this to ensure they reject
    any extra fields that aren't explicitly defined.
    """

    model_config = ConfigDict(extra="ignore")


class BaseResponse[T](BaseModel):
    """
    Base class for all SDK responses - allows extras for forward compatibility.

    All response types should inherit from this to ensure they accept
    additional fields from the API that may be added in future versions.

    Attributes:
        success: Whether the operation was successful
        data: Response data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: T | None = Field(None, description="Response data (only present on success)")
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    model_config = ConfigDict(extra="allow")


class BaseData(BaseModel):
    """
    Base class for data models inside responses - allows extras.

    All nested data types within responses should inherit from this
    to allow forward compatibility with API changes.
    """

    model_config = ConfigDict(extra="allow")
