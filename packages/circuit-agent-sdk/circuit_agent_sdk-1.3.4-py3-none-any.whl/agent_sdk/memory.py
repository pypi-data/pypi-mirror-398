"""
Memory operations for agent session storage.

This module provides the MemoryApi class for storing and retrieving key-value
pairs scoped to the current agent session.
"""

import json
from typing import TYPE_CHECKING, Any

from .client import APIError
from .types.memory import (
    MemoryDeleteData,
    MemoryDeleteResponse,
    MemoryGetData,
    MemoryGetResponse,
    MemoryListData,
    MemoryListResponse,
    MemorySetData,
    MemorySetResponse,
)

if TYPE_CHECKING:
    from .agent_sdk import AgentSdk


def _ensure_string_error(error: Any) -> str:
    """
    Ensure error is always a string, converting dicts/objects to JSON if needed.

    Args:
        error: Error value that might be a string, dict, or other type

    Returns:
        String representation of the error
    """
    if error is None:
        return "Unknown error"
    elif isinstance(error, dict):
        return json.dumps(error)
    else:
        return str(error)


class MemoryApi:
    """
    Session-scoped key-value storage operations.

    All keys are automatically namespaced by agentId and sessionId, providing
    isolated storage for each agent session. Perfect for maintaining state
    across execution cycles.
    """

    def __init__(self, sdk: "AgentSdk"):
        self._sdk = sdk

    def set(self, key: str, value: str) -> MemorySetResponse:
        """Set a key-value pair in session memory.

        Store a string value with a unique key. The key is automatically scoped to your
        agent and session, so you don't need to worry about collisions.

        **Input**: `key: str, value: str`
            - `key` (str): Unique identifier for the value (1-255 characters)
            - `value` (str): String value to store

        **Output**: `MemorySetResponse`
            - `success` (bool): Whether the operation succeeded
            - `data` (MemorySetData | None): Present on success
              - `key` (str): The key that was set
            - `error` (str | None): Error message on failure

        **Key Functionality**:
            - Automatic namespacing by agentId and sessionId
            - Overwrites existing values if key already exists
            - Persistent across agent execution cycles

        Args:
            key: Unique identifier for the value
            value: String value to store

        Returns:
            MemorySetResponse: Wrapped response with success status and key

        Example:
            ```python
            # Store user preferences
            result = sdk.memory.set("lastSwapNetwork", "ethereum:42161")

            if result.success and result.data:
                print(f"Stored key: {result.data.key}")
            else:
                print(f"Failed to store: {result.error}")
            ```
        """
        return self._handle_memory_set(key, value)

    def get(self, key: str) -> MemoryGetResponse:
        """Get a value by key from session memory.

        Retrieve a previously stored value. Returns an error if the key doesn't exist.

        **Input**: `key: str`
            - `key` (str): The key to retrieve

        **Output**: `MemoryGetResponse`
            - `success` (bool): Whether the operation succeeded
            - `data` (MemoryGetData | None): Present on success
              - `key` (str): The requested key
              - `value` (str): The stored value
            - `error` (str | None): Error message (e.g., "Key not found")

        **Key Functionality**:
            - Retrieves values stored with set()
            - Returns error if key doesn't exist
            - Automatic namespace resolution

        Args:
            key: The key to retrieve

        Returns:
            MemoryGetResponse: Wrapped response with key and value, or error details

        Example:
            ```python
            # Retrieve stored preferences
            result = sdk.memory.get("lastSwapNetwork")

            if result.success and result.data:
                print(f"Network: {result.data.value}")
            else:
                print(f"Key not found: {result.error}")
            ```
        """
        return self._handle_memory_get(key)

    def delete(self, key: str) -> MemoryDeleteResponse:
        """Delete a key from session memory.

        Remove a key-value pair. Succeeds even if the key doesn't exist.

        **Input**: `key: str`
            - `key` (str): The key to delete

        **Output**: `MemoryDeleteResponse`
            - `success` (bool): Whether the operation succeeded
            - `data` (MemoryDeleteData | None): Present on success
              - `key` (str): The key that was deleted
            - `error` (str | None): Error message on failure

        **Key Functionality**:
            - Removes key-value pair from storage
            - Idempotent - succeeds even if key doesn't exist
            - Frees up storage space

        Args:
            key: The key to delete

        Returns:
            MemoryDeleteResponse: Wrapped response with success status and deleted key

        Example:
            ```python
            # Clean up temporary data
            result = sdk.memory.delete("tempSwapQuote")

            if result.success and result.data:
                print(f"Deleted key: {result.data.key}")
            ```
        """
        return self._handle_memory_delete(key)

    def list(self) -> MemoryListResponse:
        """List all keys in session memory.

        Get an array of all keys stored for this agent session. Useful for debugging
        or iterating through stored data.

        **Input**: None

        **Output**: `MemoryListResponse`
            - `success` (bool): Whether the operation succeeded
            - `data` (MemoryListData | None): Present on success
              - `keys` (list[str]): Array of all stored keys
              - `count` (int): Number of keys
            - `error` (str | None): Error message on failure

        **Key Functionality**:
            - Returns all keys in current session
            - Empty list if no keys stored
            - Useful for cleanup or iteration

        Returns:
            MemoryListResponse: Wrapped response with array of keys and count

        Example:
            ```python
            # List all stored keys
            result = sdk.memory.list()

            if result.success and result.data:
                print(f"Found {result.data.count} keys:")
                for key in result.data.keys:
                    print(f"  - {key}")
            ```
        """
        return self._handle_memory_list()

    def _handle_memory_set(self, key: str, value: str) -> MemorySetResponse:
        """Handle memory set requests."""
        self._sdk._log("MEMORY_SET", {"key": key})

        try:
            response = self._sdk.client.post(f"/v1/memory/{key}", {"value": value})

            if not isinstance(response, dict):
                raise ValueError("Expected dict response from memory set endpoint")
            return MemorySetResponse(
                success=True,
                data=MemorySetData(**response["data"]),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            self._sdk._log("=== MEMORY SET ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("========================")

            return MemorySetResponse(
                success=False,
                data=None,
                error=_ensure_string_error(api_error.error_message),
                error_details=api_error.error_details,
            )
        except Exception as error:
            error_message = str(error) or "Failed to set memory"
            return MemorySetResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )

    def _handle_memory_get(self, key: str) -> MemoryGetResponse:
        """Handle memory get requests."""
        self._sdk._log("MEMORY_GET", {"key": key})

        try:
            response = self._sdk.client.get(f"/v1/memory/{key}")

            if not isinstance(response, dict):
                raise ValueError("Expected dict response from memory get endpoint")
            return MemoryGetResponse(
                success=True,
                data=MemoryGetData(**response["data"]),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            self._sdk._log("=== MEMORY GET ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("========================")

            return MemoryGetResponse(
                success=False,
                data=None,
                error=_ensure_string_error(api_error.error_message),
                error_details=api_error.error_details,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get memory"
            return MemoryGetResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )

    def _handle_memory_delete(self, key: str) -> MemoryDeleteResponse:
        """Handle memory delete requests."""
        self._sdk._log("MEMORY_DELETE", {"key": key})

        try:
            response = self._sdk.client.delete(f"/v1/memory/{key}")

            if not isinstance(response, dict):
                raise ValueError("Expected dict response from memory delete endpoint")
            return MemoryDeleteResponse(
                success=True,
                data=MemoryDeleteData(**response["data"]),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            self._sdk._log("=== MEMORY DELETE ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("===========================")

            return MemoryDeleteResponse(
                success=False,
                data=None,
                error=_ensure_string_error(api_error.error_message),
                error_details=api_error.error_details,
            )
        except Exception as error:
            error_message = str(error) or "Failed to delete memory"
            return MemoryDeleteResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )

    def _handle_memory_list(self) -> MemoryListResponse:
        """Handle memory list requests."""
        self._sdk._log("MEMORY_LIST", {})

        try:
            response = self._sdk.client.get("/v1/memory/list")

            if not isinstance(response, dict):
                raise ValueError("Expected dict response from memory list endpoint")
            return MemoryListResponse(
                success=True,
                data=MemoryListData(**response["data"]),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            self._sdk._log("=== MEMORY LIST ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("=========================")

            return MemoryListResponse(
                success=False,
                data=None,
                error=_ensure_string_error(api_error.error_message),
                error_details=api_error.error_details,
            )
        except Exception as error:
            error_message = str(error) or "Failed to list memory keys"
            return MemoryListResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )
