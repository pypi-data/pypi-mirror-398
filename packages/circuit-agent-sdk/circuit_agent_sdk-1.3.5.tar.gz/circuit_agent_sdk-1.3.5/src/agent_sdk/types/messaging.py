"""
Message signing type definitions for agent operations.

This module provides types for signing messages on EVM networks using
EIP712 and EIP191 standards.
"""

from typing import Literal

from pydantic import Field

from .base import BaseData, BaseRequest, BaseResponse


class EvmMessageSignRequest(BaseRequest):
    """EVM message signing request."""

    messageType: Literal["eip712", "eip191"]
    data: dict  # Will contain either EIP712 or EIP191 structure
    chainId: int


class EvmMessageSignData(BaseData):
    """EVM message signature data."""

    v: int
    r: str
    s: str
    formattedSignature: str
    type: str = Field(..., description="Signature type. Expected value: 'evm'")
    signedMessage: str | None = Field(None, description="Signed message hex string")


class EvmMessageSignResponse(BaseResponse[EvmMessageSignData]):
    """
    Response from EVM message signing operations.

    Attributes:
        success: Whether the operation was successful
        data: Signature data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    data: EvmMessageSignData | None = Field(
        None, description="Signature data (only present on success)"
    )
