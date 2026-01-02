"""
Configuration type definitions for the Agent SDK.

This module provides configuration models and constants used throughout the SDK.
"""

from pydantic import BaseModel, ConfigDict, Field

# Base URLs for the API
API_BASE_URL_LOCAL = "https://agents.circuit.org"
# Internal VPC URL for Circuit agents (resolves to proxy instance)
API_BASE_URL_DEPLOYED = "http://transaction-service.agent.internal"
# CLI local development URL (when CIRCUIT_DEV_MODE=local)
API_BASE_URL_DEV_LOCAL = "http://localhost:4001"


class SDKConfig(BaseModel):
    """
    Configuration for the SDK client.

    This is the main configuration object passed to AgentSdk constructor.

    Attributes:
        session_id: Numeric session identifier that scopes auth and actions

    Example:
        ```python
        config = SDKConfig(session_id=123)
        ```
    """

    session_id: int = Field(
        ...,
        description="Session ID for the current agent instance",
        gt=0,  # Must be positive
    )
    base_url: str | None = Field(None, description="Optional base URL for API requests")
    authorization_header: str | None = Field(
        None, description="Optional Authorization header from incoming request"
    )

    model_config = ConfigDict(extra="forbid")
