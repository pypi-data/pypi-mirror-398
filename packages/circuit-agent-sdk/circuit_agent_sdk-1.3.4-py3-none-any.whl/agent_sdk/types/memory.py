"""
Memory type definitions for agent session storage.

Memory operations provide key-value storage scoped to the current agent session.
All keys are automatically namespaced by agentId and sessionId.
"""

from pydantic import Field

from .base import BaseData, BaseRequest, BaseResponse

# =====================
# Request Types
# =====================


class MemorySetRequest(BaseRequest):
    """
    Request to set a key-value pair in memory.

    Attributes:
        key: Unique identifier for the value (1-255 characters)
        value: String value to store

    Examples:
        ```python
        # Store user preferences
        request = MemorySetRequest(
            key="lastSwapNetwork",
            value="ethereum:42161"
        )
        ```
    """

    key: str = Field(..., min_length=1, description="Key identifier")
    value: str = Field(..., description="Value to store")


class MemoryGetRequest(BaseRequest):
    """
    Request to get a value by key from memory.

    Attributes:
        key: The key to retrieve

    Examples:
        ```python
        request = MemoryGetRequest(key="lastSwapNetwork")
        ```
    """

    key: str = Field(..., min_length=1, description="Key to retrieve")


class MemoryDeleteRequest(BaseRequest):
    """
    Request to delete a key from memory.

    Attributes:
        key: The key to delete

    Examples:
        ```python
        request = MemoryDeleteRequest(key="tempSwapQuote")
        ```
    """

    key: str = Field(..., min_length=1, description="Key to delete")


class MemoryListRequest(BaseRequest):
    """
    Request to list all keys in memory (no parameters needed).

    Examples:
        ```python
        request = MemoryListRequest()
        ```
    """


# =====================
# Response Data Types
# =====================


class MemorySetData(BaseData):
    """
    Data returned when setting a key.

    Attributes:
        key: The key that was set
    """

    key: str = Field(..., description="The key that was set")


class MemoryGetData(BaseData):
    """
    Data returned when getting a key.

    Attributes:
        key: The requested key
        value: The stored value
    """

    key: str = Field(..., description="The requested key")
    value: str = Field(..., description="The stored value")


class MemoryDeleteData(BaseData):
    """
    Data returned when deleting a key.

    Attributes:
        key: The key that was deleted
    """

    key: str = Field(..., description="The key that was deleted")


class MemoryListData(BaseData):
    """
    Data returned when listing keys.

    Attributes:
        keys: Array of all stored keys
        count: Number of keys
    """

    keys: list[str] = Field(..., description="Array of all stored keys")
    count: int = Field(..., description="Number of keys")


# =====================
# SDK Response Wrappers
# =====================


class MemorySetResponse(BaseResponse[MemorySetData]):
    """Memory set response wrapper."""

    data: MemorySetData | None = Field(None, description="Set operation data")


class MemoryGetResponse(BaseResponse[MemoryGetData]):
    """Memory get response wrapper."""

    data: MemoryGetData | None = Field(None, description="Get operation data")


class MemoryDeleteResponse(BaseResponse[MemoryDeleteData]):
    """Memory delete response wrapper."""

    data: MemoryDeleteData | None = Field(None, description="Delete operation data")


class MemoryListResponse(BaseResponse[MemoryListData]):
    """Memory list response wrapper."""

    data: MemoryListData | None = Field(None, description="List operation data")
