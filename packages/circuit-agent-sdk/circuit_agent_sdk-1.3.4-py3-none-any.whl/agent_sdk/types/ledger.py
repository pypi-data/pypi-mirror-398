"""
Transaction ledger type definitions for agent operations.

This module provides types for retrieving transaction history and asset changes
from confirmed transactions across all networks.
"""

from pydantic import ConfigDict, Field

from .base import BaseData, BaseResponse


class AssetChange(BaseData):
    """
    Asset change representing a token transfer in a confirmed transaction.

    Attributes:
        network: Network identifier (e.g., "ethereum:1", "solana")
        transactionHash: Transaction hash
        from_: Sender address (using from_ to avoid Python keyword)
        to: Recipient address
        amount: Amount transferred (as string to preserve precision)
        token: Token contract address (None for native tokens)
        tokenId: Token ID for NFTs (None for fungible tokens)
        tokenType: Token type (e.g., "native", "ERC20", "ERC721")
        tokenUsdPrice: Token price in USD at time of transaction (None if unavailable)
        timestamp: Timestamp of the transaction
    """

    network: str = Field(..., description="Network identifier")
    transactionHash: str = Field(
        ..., description="Transaction hash", alias="transactionHash"
    )
    from_: str = Field(..., description="Sender address", alias="from")
    to: str = Field(..., description="Recipient address")
    amount: str = Field(..., description="Amount transferred (as string)")
    token: str | None = Field(None, description="Token contract address")
    tokenId: str | None = Field(None, description="Token ID for NFTs")
    tokenType: str = Field(..., description="Token type")
    tokenUsdPrice: str | None = Field(None, description="Token price in USD")
    timestamp: str = Field(..., description="Transaction timestamp")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class TransactionsResponse(BaseResponse[list[AssetChange]]):
    """
    Response from agent.transactions() operations.

    This response contains all confirmed transaction asset changes for the session.

    Attributes:
        success: Whether the operation was successful
        data: Array of asset changes (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = agent.transactions()
        if response.success and response.data:
            print(f"Found {len(response.data)} asset changes")
            for change in response.data:
                print(f"{change.from_} → {change.to}: {change.amount}")
        else:
            print(f"Failed: {response.error}")
        ```
    """

    data: list[AssetChange] | None = Field(
        None, description="Array of asset changes (only present on success)"
    )
