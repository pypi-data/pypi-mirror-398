"""
Job status type definitions for agent operations.

This module provides types for updating job status during agent execution,
used internally by the Agent wrapper for automatic job tracking.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseRequest


class UpdateJobStatusRequest(BaseRequest):
    """Request to update job status."""

    jobId: str = Field(..., description="UUID of the job to update")
    status: Literal["pending", "success", "failed"] = Field(
        ..., description="New status for the job"
    )
    errorMessage: str | None = Field(
        None, description="Error message if status is failed"
    )


class UpdateJobStatusResponse(BaseModel):
    """Response from job status update."""

    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")

    model_config = ConfigDict(extra="allow")
