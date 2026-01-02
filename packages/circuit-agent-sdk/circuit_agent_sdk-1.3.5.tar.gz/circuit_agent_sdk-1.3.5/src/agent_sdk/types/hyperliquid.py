"""
Hyperliquid type definitions for perpetuals trading operations.

These models match the execution-layer-SDK types for consistency.
"""

from typing import Any, Literal

from pydantic import ConfigDict, Field

from .base import BaseData, BaseRequest, BaseResponse
from .transactions import SuggestedTransactionData

# =====================
# Request Types (from execution-layer-SDK)
# =====================


class HyperliquidPlaceOrderRequest(BaseRequest):
    """
    Request to place an order on Hyperliquid.

    Attributes:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        side: Order side ("buy" or "sell")
        size: Order size (e.g., 0.0001)
        price: Order price (e.g., 110000)
        market: Market type ("perp" or "spot")
        type: Order type (optional: "market", "limit", "stop", "take_profit")
        triggerPrice: Trigger price for stop/take-profit orders (optional)
        reduceOnly: Whether this is a reduce-only order (optional)
        postOnly: Whether this is a post-only order (optional)
        bypass_manual_approval: When True, forces immediate execution even in manual mode
        expires_at: ISO 8601 timestamp for when the suggestion expires (manual mode only)

    Examples:
        ```python
        # Market buy order
        order = HyperliquidPlaceOrderRequest(
            symbol="BTC-USD",
            side="buy",
            size=0.0001,
            price=110000,
            market="perp",
            type="market"
        )

        # Limit buy order
        order = HyperliquidPlaceOrderRequest(
            symbol="BTC-USD",
            side="buy",
            size=0.0001,
            price=100000,
            market="perp",
            type="limit"
        )
        ```
    """

    symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTC-USD')")
    side: Literal["buy", "sell"] = Field(..., description="Order side")
    size: float = Field(..., description="Order size")
    price: float = Field(..., description="Order price")
    market: Literal["perp", "spot"] = Field(..., description="Market type")
    type: Literal["market", "limit", "stop", "take_profit"] | None = Field(
        None, description="Order type"
    )
    triggerPrice: float | None = Field(
        None, description="Trigger price for stop/take-profit orders"
    )
    reduceOnly: bool | None = Field(
        None, description="Whether this is a reduce-only order"
    )
    postOnly: bool | None = Field(None, description="Whether this is a post-only order")
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


class HyperliquidTransferRequest(BaseRequest):
    """
    Request to transfer between spot and perp accounts.

    Attributes:
        amount: Amount to transfer
        toPerp: True to transfer to perp account, False to transfer to spot
        bypass_manual_approval: When True, forces immediate execution even in manual mode
        expires_at: ISO 8601 timestamp for when the suggestion expires (manual mode only)

    Examples:
        ```python
        # Transfer to perp account
        transfer = HyperliquidTransferRequest(amount=1000.0, toPerp=True)
        ```
    """

    amount: float = Field(..., description="Amount to transfer")
    toPerp: bool = Field(
        ..., description="True to transfer to perp, False to transfer to spot"
    )
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


# =====================
# Response Data Types (from execution-layer-SDK)
# =====================


class HyperliquidOrderInfo(BaseData):
    """Order information."""

    orderId: str = Field(..., description="Order ID")
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="Order side. Expected values: 'buy', 'sell'")
    price: float = Field(..., description="Order price")
    size: float = Field(..., description="Order size")
    filled: float = Field(..., description="Filled amount")
    status: str = Field(..., description="Order status")
    market: str = Field(..., description="Market type. Expected values: 'perp', 'spot'")
    clientOrderId: str | None = Field(None, description="Client order ID")


class HyperliquidPerpBalance(BaseData):
    """Perp account balance information."""

    accountValue: str = Field(..., description="Account value")
    totalMarginUsed: str = Field(..., description="Total margin used")
    withdrawable: str = Field(..., description="Withdrawable amount")


class HyperliquidSpotBalance(BaseData):
    """Spot token balance."""

    coin: str = Field(..., description="Coin symbol")
    total: str = Field(..., description="Total balance")
    hold: str = Field(..., description="Amount on hold")


class HyperliquidBalances(BaseData):
    """Combined balance information."""

    perp: HyperliquidPerpBalance = Field(..., description="Perp account balance")
    spot: list[HyperliquidSpotBalance] = Field(..., description="Spot balances")


class HyperliquidPosition(BaseData):
    """Position information."""

    symbol: str = Field(..., description="Position symbol")
    side: str = Field(
        ..., description="Position side. Expected values: 'long', 'short'"
    )
    size: str = Field(..., description="Position size")
    entryPrice: str = Field(..., description="Entry price")
    markPrice: str = Field(..., description="Mark price")
    liquidationPrice: str | None = Field(None, description="Liquidation price")
    unrealizedPnl: str = Field(..., description="Unrealized PnL")
    leverage: str = Field(..., description="Leverage")
    marginUsed: str = Field(..., description="Margin used")


class HyperliquidFill(BaseData):
    """Fill/trade information from order history."""

    orderId: str = Field(..., description="Order ID")
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="Fill side. Expected values: 'buy', 'sell'")
    price: str = Field(..., description="Fill price")
    size: str = Field(..., description="Fill size")
    fee: str = Field(..., description="Fee paid")
    timestamp: int = Field(..., description="Fill timestamp")
    isMaker: bool = Field(..., description="Whether this was a maker fill")


class HyperliquidHistoricalOrder(BaseData):
    """Detailed historical order information with status."""

    orderId: str = Field(..., description="Order ID")
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="Order side. Expected values: 'buy', 'sell'")
    price: float = Field(..., description="Order price")
    size: float = Field(..., description="Order size")
    filled: float = Field(..., description="Filled amount")
    status: str = Field(
        ...,
        description="Order status. Expected values: 'open', 'filled', 'canceled', 'triggered', 'rejected', 'marginCanceled', 'liquidatedCanceled'",
    )
    market: str = Field(..., description="Market type. Expected values: 'perp', 'spot'")
    timestamp: int = Field(..., description="Order creation timestamp")
    statusTimestamp: int = Field(..., description="Status update timestamp")
    orderType: str = Field(
        ...,
        description="Order type. Expected values: 'Market', 'Limit', 'Stop Market', 'Stop Limit', 'Take Profit Market', 'Take Profit Limit'",
    )
    clientOrderId: str | None = Field(None, description="Client order ID")


class HyperliquidLiquidatedPosition(BaseData):
    """Individual liquidated position."""

    symbol: str = Field(..., description="Position symbol")
    side: str = Field(
        ..., description="Position side. Expected values: 'long', 'short'"
    )
    size: str = Field(..., description="Position size")


class HyperliquidLiquidation(BaseData):
    """Liquidation event information."""

    timestamp: int = Field(..., description="Liquidation timestamp")
    liquidatedPositions: list[HyperliquidLiquidatedPosition] = Field(
        ..., description="Liquidated positions"
    )
    totalNotional: str = Field(..., description="Total notional value")
    accountValue: str = Field(..., description="Account value at liquidation")
    leverageType: str = Field(
        ..., description="Leverage type. Expected values: 'Cross', 'Isolated'"
    )
    txHash: str = Field(..., description="Transaction hash")


# =====================
# SDK Response Wrappers
# =====================


class HyperliquidPlaceOrderResponse(
    BaseResponse[HyperliquidOrderInfo | SuggestedTransactionData]
):
    """
    Hyperliquid place order response wrapper.

    In auto mode, returns HyperliquidOrderInfo with order details.
    In manual mode (without bypass), returns SuggestedTransactionData.
    """

    data: HyperliquidOrderInfo | SuggestedTransactionData | None = Field(
        None, description="Order info or suggestion data"
    )


class HyperliquidOrderResponse(BaseResponse[HyperliquidOrderInfo]):
    """Hyperliquid order response wrapper."""

    data: HyperliquidOrderInfo | None = Field(None, description="Order info")


class HyperliquidDeleteOrderResponse(BaseResponse[dict[str, Any]]):
    """
    Hyperliquid delete order response wrapper.

    Note: This is a void response - data is always None on success.
    """

    data: dict[str, Any] | None = Field(None, description="Always None (void response)")


class HyperliquidBalancesResponse(BaseResponse[HyperliquidBalances]):
    """Hyperliquid balances response wrapper."""

    data: HyperliquidBalances | None = Field(None, description="Balances data")


class HyperliquidPositionsResponse(BaseResponse[list[HyperliquidPosition]]):
    """Hyperliquid positions response wrapper."""

    data: list[HyperliquidPosition] | None = Field(None, description="Positions data")


class HyperliquidOpenOrdersResponse(BaseResponse[list[HyperliquidOrderInfo]]):
    """Hyperliquid open orders response wrapper."""

    data: list[HyperliquidOrderInfo] | None = Field(
        None, description="Open orders data"
    )


class HyperliquidOrderFillsResponse(BaseResponse[list[HyperliquidFill]]):
    """Hyperliquid order fills response wrapper."""

    data: list[HyperliquidFill] | None = Field(None, description="Order fills data")


class HyperliquidHistoricalOrdersResponse(
    BaseResponse[list[HyperliquidHistoricalOrder]]
):
    """Hyperliquid historical orders response wrapper."""

    data: list[HyperliquidHistoricalOrder] | None = Field(
        None, description="Historical orders data"
    )


class HyperliquidTransferResponse(BaseResponse[dict[str, Any]]):
    """
    Hyperliquid transfer response wrapper.

    Note: This is a void response - data is always None on success.
    """

    data: dict[str, Any] | None = Field(None, description="Always None (void response)")


class HyperliquidLiquidationsResponse(BaseResponse[list[HyperliquidLiquidation]]):
    """Hyperliquid liquidations response wrapper."""

    data: list[HyperliquidLiquidation] | None = Field(
        None, description="Liquidations data"
    )
