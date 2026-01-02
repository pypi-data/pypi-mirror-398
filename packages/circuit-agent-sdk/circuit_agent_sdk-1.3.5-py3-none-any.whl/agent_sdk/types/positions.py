"""
Position type definitions for agent operations.

This module provides types for retrieving and working with current positions,
including Polymarket metadata enrichment for ERC1155 positions.
"""

from pydantic import Field

from .base import BaseData, BaseResponse


class PolymarketMetadata(BaseData):
    """
    Polymarket-specific position metadata.

    Contains detailed market information for ERC1155 Polymarket positions including
    current prices, PNL tracking, and redeemability status.

    Attributes:
        contractAddress: ERC1155 contract address for the market
        tokenId: Token ID for the specific outcome
        decimals: Token decimals (typically 6)
        conditionId: Unique condition identifier
        formattedShares: Human-readable share count
        shares: Raw share count in smallest unit
        valueUsd: Current position value in USD
        question: Market question text
        outcome: Outcome name (e.g., "Yes", "No")
        priceUsd: Current price per share in USD
        averagePriceUsd: Average purchase price per share in USD
        isRedeemable: Whether position can be redeemed
        isNegativeRisk: Whether position uses negative risk collateral
        imageUrl: Market image URL
        initialValue: Initial position value in USD
        pnlUsd: Unrealized profit/loss in USD
        pnlPercent: Unrealized profit/loss percentage
        pnlRealizedUsd: Realized profit/loss in USD
        pnlRealizedPercent: Realized profit/loss percentage
        endDate: Market end date (ISO 8601 string)
    """

    contractAddress: str = Field(..., description="ERC1155 contract address")
    tokenId: str | None = Field(None, description="Token ID for the outcome")
    decimals: int = Field(..., description="Token decimals")
    conditionId: str = Field(..., description="Unique condition identifier")
    formattedShares: str = Field(..., description="Human-readable share count")
    shares: str = Field(..., description="Raw share count in smallest unit")
    valueUsd: str = Field(..., description="Current position value in USD")
    question: str = Field(..., description="Market question text")
    outcome: str = Field(..., description="Outcome name (e.g., 'Yes', 'No')")
    priceUsd: str = Field(..., description="Current price per share in USD")
    averagePriceUsd: str = Field(
        ..., description="Average purchase price per share in USD"
    )
    isRedeemable: bool = Field(..., description="Whether position can be redeemed")
    isNegativeRisk: bool = Field(
        ..., description="Whether position uses negative risk collateral"
    )
    imageUrl: str = Field(..., description="Market image URL")
    initialValue: str = Field(..., description="Initial position value in USD")
    pnlUsd: str = Field(..., description="Unrealized profit/loss in USD")
    pnlPercent: str = Field(..., description="Unrealized profit/loss percentage")
    pnlRealizedUsd: str = Field(..., description="Realized profit/loss in USD")
    pnlRealizedPercent: str = Field(..., description="Realized profit/loss percentage")
    endDate: str = Field(..., description="Market end date (ISO 8601 string)")


class EnrichedPosition(BaseData):
    """
    Current position with optional Polymarket metadata enrichment.

    Represents a position held by the session wallet, with optional detailed
    Polymarket market information for ERC1155 positions.

    Attributes:
        network: Network identifier (e.g., "ethereum:137", "solana")
        assetAddress: Asset contract address
        tokenId: Token ID for NFTs/ERC1155 (None for fungible tokens)
        avgUnitCost: Average unit cost in USD
        currentQty: Current quantity held (raw amount)
        polymarketMetadata: Optional Polymarket metadata (only for ERC1155 positions)
    """

    network: str = Field(..., description="Network identifier")
    assetAddress: str = Field(..., description="Asset contract address")
    tokenId: str | None = Field(
        None, description="Token ID for NFTs/ERC1155 (None for fungible tokens)"
    )
    avgUnitCost: str = Field(..., description="Average unit cost in USD")
    currentQty: str = Field(..., description="Current quantity held (raw amount)")
    polymarketMetadata: PolymarketMetadata | None = Field(
        None, description="Optional Polymarket metadata (only for ERC1155 positions)"
    )


class GetCurrentPositionsData(BaseData):
    """
    Data returned from get_current_positions() operations.

    Contains the list of current positions and a flag indicating if there are
    pending transactions that may affect balances.

    Attributes:
        positions: Array of current positions with optional Polymarket metadata
        hasPendingTxs: Whether there are pending transactions
    """

    positions: list[EnrichedPosition] = Field(
        ..., description="Array of current positions with optional Polymarket metadata"
    )
    hasPendingTxs: bool = Field(
        ..., description="Whether there are pending transactions"
    )


class GetCurrentPositionsResponse(BaseResponse[GetCurrentPositionsData]):
    """
    Response from get_current_positions() operations.

    Returns current live positions for the session with optional Polymarket
    metadata enrichment for ERC1155 positions.

    Attributes:
        success: Whether the operation was successful
        data: Current positions data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = sdk.get_current_positions()
        if response.success and response.data:
            print(f"Found {len(response.data.positions)} positions")

            if response.data.hasPendingTxs:
                print("⚠️  Warning: Pending transactions may affect balances")

            for position in response.data.positions:
                print(f"{position.assetAddress}: {position.currentQty} units")
                print(f"  Average cost: ${position.avgUnitCost}")

                # Check for Polymarket enrichment
                if position.polymarketMetadata:
                    pm = position.polymarketMetadata
                    print(f"  📈 {pm.question}")
                    print(f"  Outcome: {pm.outcome}")
                    print(f"  Shares: {pm.formattedShares}")
                    print(f"  Value: ${pm.valueUsd}")
                    print(f"  PNL: ${pm.pnlUsd} ({pm.pnlPercent}%)")
                    print(f"  Redeemable: {'Yes' if pm.isRedeemable else 'No'}")
        else:
            print(f"Failed: {response.error}")
        ```
    """

    data: GetCurrentPositionsData | None = Field(
        None, description="Current positions data (only present on success)"
    )
