"""
Polymarket type definitions for prediction market operations.

These models match the TypeScript SDK implementation for consistency across
all Circuit agent SDKs.
"""

from typing import Any, Literal

from pydantic import ConfigDict, Field

from .base import BaseData, BaseRequest, BaseResponse
from .transactions import SuggestedTransactionData

# =====================
# Position Types
# =====================


class PolymarketPosition(BaseData):
    """
    Individual position on Polymarket.

    Represents a prediction market position with current value, PNL tracking,
    and market details.

    Attributes:
        contractAddress: ERC1155 contract address for the market
        tokenId: Token ID for the specific outcome (nullable)
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


class PolymarketPositionsData(BaseData):
    """
    Complete positions data from Polymarket.

    Attributes:
        totalValue: Total portfolio value in USD
        positions: List of position objects
    """

    totalValue: float = Field(..., description="Total portfolio value in USD")
    positions: list[PolymarketPosition] = Field(..., description="List of positions")


# =====================
# Market Order Types
# =====================


class PolymarketMarketOrderRequest(BaseRequest):
    """
    Request to place a market order on Polymarket.

    **Important**: The `size` parameter meaning differs by order side:
    - **BUY**: `size` is the USD amount to spend (e.g., 10 = $10 worth of shares)
    - **SELL**: `size` is the number of shares/tokens to sell (e.g., 10 = 10 shares)

    Attributes:
        tokenId: Market token ID for the position
        size: For BUY: USD amount to spend. For SELL: Number of shares to sell
        side: Order side - "BUY" or "SELL"
        bypass_manual_approval: When True, forces immediate execution even in manual mode
        expires_at: ISO 8601 timestamp for when the suggestion expires (manual mode only)

    Examples:
        ```python
        # BUY order - size is USD amount
        buy_request = PolymarketMarketOrderRequest(
            tokenId="123456",
            size=10,  # Spend $10 to buy shares
            side="BUY"
        )

        # SELL order - size is number of shares
        sell_request = PolymarketMarketOrderRequest(
            tokenId="123456",
            size=5,  # Sell 5 shares
            side="SELL"
        )
        ```
    """

    tokenId: str = Field(
        ..., validation_alias="token_id", description="Market token ID"
    )
    size: float = Field(
        ...,
        description="For BUY: USD amount to spend. For SELL: Number of shares to sell",
    )
    side: Literal["BUY", "SELL"] = Field(..., description="Order side")
    bypass_manual_approval: bool = Field(
        default=False,
        alias="bypassManualApproval",
        description="When True, forces immediate execution even if session is in manual mode",
    )
    expires_at: str | None = Field(
        default=None,
        alias="expiresAt",
        description="ISO 8601 timestamp for when the suggestion expires (only used in manual mode)",
    )

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class PolymarketOrder(BaseData):
    """
    Polymarket order details.

    Contains the complete order structure including amounts, fees, and metadata.

    Attributes:
        salt: Random salt for order uniqueness
        maker: Maker address
        signer: Signer address
        taker: Taker address
        tokenId: Market token ID
        makerAmount: Maker amount in smallest unit
        takerAmount: Taker amount in smallest unit
        expiration: Order expiration timestamp
        nonce: Order nonce
        feeRateBps: Fee rate in basis points
        side: Order side (0 = BUY, 1 = SELL)
        signatureType: Signature type (0 = EIP712)
    """

    salt: str = Field(..., description="Random salt for order uniqueness")
    maker: str = Field(..., description="Maker address")
    signer: str = Field(..., description="Signer address")
    taker: str = Field(..., description="Taker address")
    tokenId: str = Field(..., description="Market token ID")
    makerAmount: str = Field(..., description="Maker amount in smallest unit")
    takerAmount: str = Field(..., description="Taker amount in smallest unit")
    expiration: str = Field(..., description="Order expiration timestamp")
    nonce: str = Field(..., description="Order nonce")
    feeRateBps: str = Field(..., description="Fee rate in basis points")
    side: int = Field(..., description="Order side (0 = BUY, 1 = SELL)")
    signatureType: int = Field(..., description="Signature type (0 = EIP712)")


class PolymarketEip712Type(BaseData):
    """EIP712 type definition."""

    name: str = Field(..., description="Field name")
    type: str = Field(..., description="Field type")


class PolymarketEip712Domain(BaseData):
    """EIP712 domain definition."""

    name: str = Field(..., description="Domain name")
    version: str = Field(..., description="Domain version")
    chainId: int = Field(..., description="Chain ID")
    verifyingContract: str = Field(..., description="Verifying contract address")


class PolymarketEip712Message(BaseData):
    """
    EIP712 typed data message for signing.

    Attributes:
        types: Type definitions for the message
        domain: Domain separator
        primaryType: Primary type name
        message: Message data
    """

    types: dict[str, list[PolymarketEip712Type]] = Field(
        ..., description="Type definitions"
    )
    domain: PolymarketEip712Domain = Field(..., description="Domain separator")
    primaryType: str = Field(..., description="Primary type name")
    message: dict[str, Any] = Field(..., description="Message data")


class PolymarketOrderInfo(BaseData):
    """
    Order information after submission.

    Attributes:
        orderId: Unique order identifier
        side: Order side ("BUY" or "SELL")
        size: Order size
        priceUsd: Price per share in USD
        totalPriceUsd: Total order value in USD
        txHashes: List of transaction hashes
    """

    orderId: str = Field(..., description="Unique order identifier")
    side: str = Field(..., description="Order side")
    size: str = Field(..., description="Order size")
    priceUsd: str = Field(..., description="Price per share in USD")
    totalPriceUsd: str = Field(..., description="Total order value in USD")
    txHashes: list[str] = Field(..., description="List of transaction hashes")


# DEPRECATED
class PolymarketSubmitOrderResult(BaseData):
    """
    Result of order submission.

    Attributes:
        orderId: Unique order identifier
        success: Whether submission was successful
        errorMessage: Error message if submission failed (optional)
    """

    orderId: str = Field(..., description="Unique order identifier")
    success: bool = Field(..., description="Whether submission was successful")
    errorMessage: str | None = Field(
        None, description="Error message if submission failed"
    )


class PolymarketOrderData(BaseData):
    """
    Order data container.

    Attributes:
        eip712Message: EIP712 typed data for signing
        order: Order details
    """

    eip712Message: PolymarketEip712Message = Field(
        ..., description="EIP712 typed data for signing"
    )
    order: PolymarketOrder = Field(..., description="Order details")


class PolymarketMarketOrderData(BaseData):
    """
    Complete market order data.

    Attributes:
        success: Whether the order was successfully submitted
        orderInfo: Order information with transaction details
    """

    success: bool = Field(
        ..., description="Whether the order was successfully submitted"
    )
    orderInfo: PolymarketOrderInfo = Field(
        ..., description="Order information with transaction details"
    )


# =====================
# Redeem Positions Types
# =====================


class PolymarketRedeemPositionsRequest(BaseRequest):
    """
    Request to redeem settled positions.

    Attributes:
        tokenIds: List of token IDs to redeem specific positions. Empty list redeems all redeemable positions.

    Examples:
        ```python
        # Redeem all positions
        redeem_all = PolymarketRedeemPositionsRequest()

        # Redeem specific positions
        redeem_specific = PolymarketRedeemPositionsRequest(tokenIds=["123456", "789012"])
        ```
    """

    tokenIds: list[str] = Field(
        default_factory=list,
        validation_alias="token_ids",
        description="List of token IDs to redeem specific positions. Empty list redeems all.",
    )

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class PolymarketRedeemPositionResult(BaseData):
    """
    Result of redeeming a single position.

    Attributes:
        success: Whether redemption was successful
        position: Position that was redeemed (null for non-position transactions like unwrapping collateral)
        transactionHash: Transaction hash (null if redemption failed)
    """

    success: bool = Field(..., description="Whether redemption was successful")
    position: PolymarketPosition | None = Field(
        None,
        description="Position that was redeemed (null for non-position transactions like unwrapping collateral)",
    )
    transactionHash: str | None = Field(
        None, description="Transaction hash (null if redemption failed)"
    )


# Type alias for the array of redemption results
PolymarketRedeemPositionsData = list[PolymarketRedeemPositionResult]


# =====================
# SDK Response Wrappers
# =====================


class PolymarketPositionsResponse(BaseResponse[PolymarketPositionsData]):
    """Polymarket positions response wrapper."""

    data: PolymarketPositionsData | None = Field(None, description="Positions data")


class PolymarketMarketOrderResponse(
    BaseResponse[PolymarketMarketOrderData | SuggestedTransactionData]
):
    """
    Polymarket market order response wrapper.

    In auto mode, returns PolymarketMarketOrderData with order details.
    In manual mode (without bypass), returns SuggestedTransactionData.
    """

    data: PolymarketMarketOrderData | SuggestedTransactionData | None = Field(
        None, description="Market order or suggestion data"
    )


class PolymarketRedeemPositionsResponse(BaseResponse[PolymarketRedeemPositionsData]):
    """Polymarket redeem positions response wrapper."""

    data: PolymarketRedeemPositionsData | None = Field(
        None, description="Redeem positions data"
    )
