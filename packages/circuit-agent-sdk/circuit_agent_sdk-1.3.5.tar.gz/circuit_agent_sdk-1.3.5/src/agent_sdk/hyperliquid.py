"""
Hyperliquid perpetuals trading operations.

This module provides the HyperliquidApi class for interacting with Hyperliquid
DEX, including order placement, position management, and transfers.
"""

import json
from typing import TYPE_CHECKING, Any

from .client import APIError
from .types import (
    SuggestedTransactionData,
    SuggestedTransactionResponse,
)
from .types.hyperliquid import (
    HyperliquidBalancesResponse,
    HyperliquidDeleteOrderResponse,
    HyperliquidHistoricalOrdersResponse,
    HyperliquidLiquidationsResponse,
    HyperliquidOpenOrdersResponse,
    HyperliquidOrderFillsResponse,
    HyperliquidOrderResponse,
    HyperliquidPlaceOrderRequest,
    HyperliquidPlaceOrderResponse,
    HyperliquidPositionsResponse,
    HyperliquidTransferRequest,
    HyperliquidTransferResponse,
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


def _unwrap_execution_sdk_response(
    response: dict[str, Any],
) -> tuple[bool, Any, str | None]:
    """
    Unwrap execution-layer-SDK response format.

    The backend returns responses from the execution-layer-SDK which have the format:
    - Success with data: {success: true, data: any}
    - Success (void): {success: true}
    - Failure: {success: false, error: string}

    This function extracts the wrapped data or error.

    Args:
        response: Response dict from API

    Returns:
        Tuple of (success, data, error)
    """
    # If response has success field, it's wrapped by execution-layer-SDK
    if "success" in response:
        success = response.get("success", False)
        data = response.get("data")
        error = response.get("error")
        return (success, data, error)
    else:
        # Not wrapped, return as-is (legacy case)
        return (True, response, None)


def _unwrap_execution_sdk_array_response(
    response: dict[str, Any] | list[Any],
) -> tuple[bool, list[Any], str | None]:
    """
    Unwrap execution-layer-SDK response that should be an array.

    Handles cases where response might be:
    1. {success: bool, data: array, error?: string} - wrapped
    2. array - direct array response

    Args:
        response: Response from API (dict or list)

    Returns:
        Tuple of (success, data_array, error)
    """
    if isinstance(response, list):
        # Direct array response
        return (True, response, None)
    elif isinstance(response, dict) and "success" in response:
        # Wrapped response
        success = response.get("success", False)
        data = response.get("data", [])
        error = response.get("error")

        # Ensure data is a list
        if not isinstance(data, list):
            data = []

        return (success, data, error)
    else:
        # Unexpected format, treat as empty array
        return (False, [], "Unexpected response format")


class HyperliquidApi:
    """
    Hyperliquid perpetuals trading operations.

    Provides access to perpetuals trading, position management, and transfers
    on the Hyperliquid DEX using your session wallet.
    """

    def __init__(self, sdk: "AgentSdk"):
        self._sdk = sdk

    def place_order(
        self, request: HyperliquidPlaceOrderRequest | dict
    ) -> HyperliquidPlaceOrderResponse | SuggestedTransactionResponse:
        """
        Place an order on Hyperliquid.

        Submit a market, limit, stop, or take-profit order for perpetuals or spot trading.

        **Manual Mode**: When the session is in manual or hybrid execution mode, this method
        returns a `SuggestedTransactionResponse` instead of executing immediately. The transaction
        will be queued for user approval in the Circuit interface.

        **Input**: `HyperliquidPlaceOrderRequest`
            - `symbol` (str): Trading pair symbol (e.g., "BTC-USD")
            - `side` ("buy" | "sell"): Order side
            - `size` (float): Order size
            - `price` (float): Order price (for market orders, acts as slippage limit)
            - `market` ("perp" | "spot"): Market type
            - `type` (str, optional): Order type ("limit", "market", "stop", "take_profit")
            - `triggerPrice` (float, optional): Trigger price for stop/take-profit orders
            - `reduceOnly` (bool, optional): Whether this is a reduce-only order
            - `postOnly` (bool, optional): Whether this is a post-only order

        **Output (Auto Mode)**: `HyperliquidPlaceOrderResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (HyperliquidOrderInfo | None): Order information (only present on success)
              - `data.orderId` (str): Order ID
              - `data.symbol` (str): Trading pair symbol
              - `data.side` ("buy" | "sell"): Order side
              - `data.price` (float): Order price
              - `data.size` (float): Order size
              - `data.filled` (float): Filled amount
              - `data.status` (str): Order status
              - `data.market` ("perp" | "spot"): Market type
              - `data.clientOrderId` (str | None): Client order ID
            - `error` (str | None): Error message (only present on failure)

        **Output (Manual Mode)**: `SuggestedTransactionResponse`
            - `success` (bool): Whether the suggestion was created successfully
            - `data` (SuggestedTransactionData): Suggestion details
              - `suggested` (bool): Always True
              - `suggestionId` (int): Unique suggestion identifier
              - `details` (dict): Transaction details for user review
            - `error` (str | None): Error message (only present on failure)

        Args:
            request: Order parameters as HyperliquidPlaceOrderRequest or dict

        Returns:
            HyperliquidPlaceOrderResponse | SuggestedTransactionResponse: Response with order
            information (auto mode) or suggestion details (manual mode)

        Example:
            ```python
            # Market order
            result = agent.platforms.hyperliquid.place_order({
                "symbol": "BTC-USD",
                "side": "buy",
                "size": 0.0001,
                "price": 110000,
                "market": "perp",
                "type": "market",
            })

            # Limit order
            result = agent.platforms.hyperliquid.place_order({
                "symbol": "BTC-USD",
                "side": "buy",
                "size": 0.0001,
                "price": 100000,
                "market": "perp",
                "type": "limit",
            })

            # Check if transaction was suggested (manual mode) vs executed (auto mode)
            if result.success and result.data:
                if hasattr(result.data, 'suggested') and result.data.suggested:
                    agent.log(f"Order suggested: #{result.data.suggestionId}")
                    agent.log("Awaiting user approval in Circuit interface")
                else:
                    agent.log(f"Order placed: {result.data.orderId}")
                    agent.log(f"Status: {result.data.status}")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_place_order(request)

    def order(self, order_id: str) -> HyperliquidOrderResponse:
        """
        Get order information by order ID.

        Retrieve details for a specific order including status, filled amount, and price.

        **Input**: `order_id` (str): Unique order identifier

        **Output**: `HyperliquidOrderResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (HyperliquidOrderInfo | None): Order details (only present on success)
              - `data.orderId` (str): Order ID
              - `data.symbol` (str): Trading pair symbol
              - `data.side` ("buy" | "sell"): Order side
              - `data.price` (float): Order price
              - `data.size` (float): Order size
              - `data.filled` (float): Filled amount
              - `data.status` (str): Order status
              - `data.market` ("perp" | "spot"): Market type
              - `data.clientOrderId` (str | None): Client order ID
            - `error` (str | None): Error message (only present on failure)

        Args:
            order_id: Order ID to query

        Returns:
            HyperliquidOrderResponse: Wrapped response with order information

        Example:
            ```python
            result = agent.platforms.hyperliquid.order("12345")
            if result.success and result.data:
                agent.log(f"Order {result.data.orderId}: {result.data.status}")
                agent.log(f"Filled: {result.data.filled}/{result.data.size}")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_get_order(order_id)

    def delete_order(
        self, order_id: str, symbol: str
    ) -> HyperliquidDeleteOrderResponse:
        """
        Cancel an order.

        Cancel an open order by order ID and symbol.

        **Input**:
            - `order_id` (str): Order ID to cancel
            - `symbol` (str): Trading symbol

        **Output**: `HyperliquidDeleteOrderResponse`
            - `success` (bool): Whether the operation was successful
            - `error` (str | None): Error message (only present on failure)

        Note: This operation returns no data on success (void response).

        Args:
            order_id: Order ID to cancel
            symbol: Trading symbol

        Returns:
            HyperliquidDeleteOrderResponse: Wrapped response with cancellation result

        Example:
            ```python
            result = agent.platforms.hyperliquid.delete_order("12345", "BTC-USD")
            if result.success:
                agent.log("Order cancelled successfully")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_delete_order(order_id, symbol)

    def balances(self) -> HyperliquidBalancesResponse:
        """
        Get account balances.

        Retrieve perp and spot account balances.

        **Output**: `HyperliquidBalancesResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (HyperliquidBalances | None): Balance data (only present on success)
              - `data.perp` (HyperliquidPerpBalance): Perp account balance
                - `data.perp.accountValue` (str): Total account value
                - `data.perp.totalMarginUsed` (str): Total margin used
                - `data.perp.withdrawable` (str): Withdrawable amount
              - `data.spot` (list[HyperliquidSpotBalance]): Spot token balances
                - `data.spot[].coin` (str): Token symbol
                - `data.spot[].total` (str): Total balance
                - `data.spot[].hold` (str): Amount on hold
            - `error` (str | None): Error message (only present on failure)

        Returns:
            HyperliquidBalancesResponse: Wrapped response with account balances

        Example:
            ```python
            result = agent.platforms.hyperliquid.balances()
            if result.success and result.data:
                agent.log(f"Account value: {result.data.perp.accountValue}")
                agent.log(f"Withdrawable: {result.data.perp.withdrawable}")
                for balance in result.data.spot:
                    agent.log(f"{balance.coin}: {balance.total}")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_get_balances()

    def positions(self) -> HyperliquidPositionsResponse:
        """
        Get open positions.

        Retrieve all open perpetual positions with PnL and position details.

        **Output**: `HyperliquidPositionsResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (list[HyperliquidPosition] | None): Array of open positions (only present on success)
              - `data[].symbol` (str): Trading pair symbol (e.g., "BTC-USD")
              - `data[].side` ("long" | "short"): Position side
              - `data[].size` (str): Position size
              - `data[].entryPrice` (str): Average entry price
              - `data[].markPrice` (str): Current mark price
              - `data[].liquidationPrice` (str | None): Liquidation price (null if no risk)
              - `data[].unrealizedPnl` (str): Unrealized profit/loss
              - `data[].leverage` (str): Current leverage
              - `data[].marginUsed` (str): Margin allocated to position
            - `error` (str | None): Error message (only present on failure)

        Returns:
            HyperliquidPositionsResponse: Wrapped response with open positions

        Example:
            ```python
            result = agent.platforms.hyperliquid.positions()
            if result.success and result.data:
                for pos in result.data:
                    agent.log(f"{pos.symbol}: {pos.side} {pos.size}")
                    agent.log(f"Entry: {pos.entryPrice}, Mark: {pos.markPrice}")
                    agent.log(f"Unrealized PnL: {pos.unrealizedPnl}")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_get_positions()

    def open_orders(self) -> HyperliquidOpenOrdersResponse:
        """
        Get open orders.

        Retrieve all currently open orders.

        **Output**: `HyperliquidOpenOrdersResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (list[HyperliquidOrderInfo] | None): Array of open orders (only present on success)
              - `data[].orderId` (str): Order ID
              - `data[].symbol` (str): Trading pair symbol
              - `data[].side` ("buy" | "sell"): Order side
              - `data[].price` (float): Order price
              - `data[].size` (float): Order size
              - `data[].filled` (float): Filled amount
              - `data[].status` (str): Order status
              - `data[].market` ("perp" | "spot"): Market type
              - `data[].clientOrderId` (str | None): Client order ID
            - `error` (str | None): Error message (only present on failure)

        Returns:
            HyperliquidOpenOrdersResponse: Wrapped response with open orders

        Example:
            ```python
            result = agent.platforms.hyperliquid.open_orders()
            if result.success and result.data:
                agent.log(f"You have {len(result.data)} open orders")
                for order in result.data:
                    agent.log(f"{order.symbol}: {order.side} {order.size} @ {order.price}")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_get_open_orders()

    def order_fills(self) -> HyperliquidOrderFillsResponse:
        """
        Get order fill history.

        Retrieve order fill history including partial and complete fills.

        **Output**: `HyperliquidOrderFillsResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (list[HyperliquidFill] | None): Array of order fills (only present on success)
              - `data[].orderId` (str): Order ID
              - `data[].symbol` (str): Trading pair symbol
              - `data[].side` ("buy" | "sell"): Fill side
              - `data[].price` (str): Fill price
              - `data[].size` (str): Fill size
              - `data[].fee` (str): Trading fee paid
              - `data[].timestamp` (int): Fill timestamp in milliseconds
              - `data[].isMaker` (bool): True if maker, false if taker
            - `error` (str | None): Error message (only present on failure)

        Returns:
            HyperliquidOrderFillsResponse: Wrapped response with order fill history

        Example:
            ```python
            result = agent.platforms.hyperliquid.order_fills()
            if result.success and result.data:
                agent.log(f"Total fills: {len(result.data)}")
                for fill in result.data:
                    fill_type = "maker" if fill.isMaker else "taker"
                    agent.log(f"{fill.symbol}: {fill.size} @ {fill.price} ({fill_type}, fee: {fill.fee})")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_get_order_fills()

    def orders(self) -> HyperliquidHistoricalOrdersResponse:
        """
        Get historical orders.

        Retrieve order history including filled, cancelled, and expired orders.

        **Output**: `HyperliquidHistoricalOrdersResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (list[HyperliquidHistoricalOrder] | None): Array of historical orders (only present on success)
              - `data[].orderId` (str): Order ID
              - `data[].symbol` (str): Trading pair symbol
              - `data[].side` ("buy" | "sell"): Order side
              - `data[].price` (float): Order price
              - `data[].size` (float): Order size
              - `data[].filled` (float): Filled amount
              - `data[].status` (str): Order status ("open", "filled", "canceled", "triggered", "rejected", "marginCanceled", "liquidatedCanceled")
              - `data[].market` ("perp" | "spot"): Market type
              - `data[].timestamp` (int): Order creation timestamp in milliseconds
              - `data[].statusTimestamp` (int): Status update timestamp in milliseconds
              - `data[].orderType` (str): Order type ("Market", "Limit", "Stop Market", "Stop Limit", "Take Profit Market", "Take Profit Limit")
              - `data[].clientOrderId` (str | None): Client order ID
            - `error` (str | None): Error message (only present on failure)

        Returns:
            HyperliquidHistoricalOrdersResponse: Wrapped response with historical orders

        Example:
            ```python
            result = agent.platforms.hyperliquid.orders()
            if result.success and result.data:
                agent.log(f"Order history: {len(result.data)} orders")
                filled = [o for o in result.data if o.status == "filled"]
                agent.log(f"Filled orders: {len(filled)}")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_get_historical_orders()

    def transfer(
        self, request: HyperliquidTransferRequest | dict
    ) -> HyperliquidTransferResponse:
        """
        Transfer between spot and perp accounts.

        Move funds between your spot wallet and perpetuals trading account.

        **Input**: `HyperliquidTransferRequest`
            - `amount` (float): Amount to transfer
            - `toPerp` (bool): True to transfer to perp account, False to transfer to spot

        **Output**: `HyperliquidTransferResponse`
            - `success` (bool): Whether the operation was successful
            - `error` (str | None): Error message (only present on failure)

        Note: This operation returns no data on success (void response).

        Args:
            request: Transfer parameters as HyperliquidTransferRequest or dict

        Returns:
            HyperliquidTransferResponse: Wrapped response with transfer result

        Example:
            ```python
            # Transfer 1000 USDC to perp account
            result = agent.platforms.hyperliquid.transfer({
                "amount": 1000,
                "toPerp": True
            })

            if result.success:
                agent.log("Transfer completed successfully")
            else:
                agent.log(f"Error: {result.error}")
            ```
        """
        return self._handle_transfer(request)

    def liquidations(
        self, start_time: int | None = None
    ) -> HyperliquidLiquidationsResponse:
        """
        Get liquidation events.

        Retrieve liquidation events for the account, optionally filtered by start time.

        **Input**: `start_time` (int, optional): Unix timestamp in milliseconds to filter liquidations from

        **Output**: `HyperliquidLiquidationsResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (list[HyperliquidLiquidation] | None): Array of liquidation events (only present on success)
              - `data[].timestamp` (int): Liquidation timestamp in milliseconds
              - `data[].liquidatedPositions` (list[HyperliquidLiquidatedPosition]): Liquidated positions
                - `data[].liquidatedPositions[].symbol` (str): Position symbol (e.g., "BTC-USD")
                - `data[].liquidatedPositions[].side` ("long" | "short"): Position side
                - `data[].liquidatedPositions[].size` (str): Position size that was liquidated
              - `data[].totalNotional` (str): Total notional value liquidated
              - `data[].accountValue` (str): Account value at liquidation
              - `data[].leverageType` ("Cross" | "Isolated"): Leverage type
              - `data[].txHash` (str): Transaction hash
            - `error` (str | None): Error message (only present on failure)

        Args:
            start_time: Optional start time for filtering (Unix timestamp in milliseconds)

        Returns:
            HyperliquidLiquidationsResponse: Wrapped response with liquidation events

        Example:
            ```python
            # Get all liquidations (defaults to last 30 days)
            all_liq = agent.platforms.hyperliquid.liquidations()

            # Get liquidations from last 24h
            import time
            yesterday = int(time.time() * 1000) - (24 * 60 * 60 * 1000)
            recent = agent.platforms.hyperliquid.liquidations(yesterday)

            if recent.success and recent.data:
                agent.log(f"Liquidations in last 24h: {len(recent.data)}")
                for liq in recent.data:
                    agent.log(f"Liquidated {len(liq.liquidatedPositions)} positions")
            else:
                agent.log(f"Error: {recent.error}")
            ```
        """
        return self._handle_get_liquidations(start_time)

    # Private implementation methods

    def _handle_place_order(
        self, request: HyperliquidPlaceOrderRequest | dict
    ) -> HyperliquidPlaceOrderResponse | SuggestedTransactionResponse:
        """Handle place order requests."""
        self._sdk._log("HYPERLIQUID_PLACE_ORDER", {"request": request})

        try:
            # Handle both dict and Pydantic model inputs
            if isinstance(request, dict):
                request_obj = HyperliquidPlaceOrderRequest(**request)
            else:
                request_obj = request

            response = self._sdk.client.post(
                "/v1/platforms/hyperliquid/order",
                request_obj.model_dump(mode="json", exclude_unset=True),
            )

            from .types.hyperliquid import HyperliquidOrderInfo

            # Handle response
            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid order endpoint"
                )

            # Extract data from standardized API format
            response_data = response.get("data", {})

            # Check if this is a suggested transaction (manual mode)
            if (
                isinstance(response_data, dict)
                and response_data.get("suggested") is True
            ):
                return SuggestedTransactionResponse(
                    success=True,
                    data=SuggestedTransactionData(**response_data),
                    error=None,
                    error_details=None,
                )

            # Normal execution response - parse as OrderInfo
            return HyperliquidPlaceOrderResponse(
                success=True,
                data=HyperliquidOrderInfo(**response_data),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            self._sdk._log("=== HYPERLIQUID PLACE ORDER ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("=====================================")

            return HyperliquidPlaceOrderResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to place order"
            return HyperliquidPlaceOrderResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_get_order(self, order_id: str) -> HyperliquidOrderResponse:
        """Handle get order requests."""
        self._sdk._log("HYPERLIQUID_GET_ORDER", {"order_id": order_id})

        try:
            response = self._sdk.client.get(
                f"/v1/platforms/hyperliquid/order/{order_id}"
            )

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid order endpoint"
                )

            from .types.hyperliquid import HyperliquidOrderInfo

            # Extract data from standardized API format
            response_data = response["data"]

            return HyperliquidOrderResponse(
                success=True,
                data=HyperliquidOrderInfo(**response_data),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidOrderResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get order"
            return HyperliquidOrderResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_delete_order(
        self, order_id: str, symbol: str
    ) -> HyperliquidDeleteOrderResponse:
        """Handle delete order requests."""
        self._sdk._log(
            "HYPERLIQUID_DELETE_ORDER", {"order_id": order_id, "symbol": symbol}
        )

        try:
            response = self._sdk.client.delete(
                f"/v1/platforms/hyperliquid/order/{order_id}/{symbol}"
            )

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid delete order endpoint"
                )

            # Extract data from standardized API format (void response)
            # No data to extract for delete operation

            return HyperliquidDeleteOrderResponse(
                success=True,
                data=None,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidDeleteOrderResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to delete order"
            return HyperliquidDeleteOrderResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_get_balances(self) -> HyperliquidBalancesResponse:
        """Handle get balances requests."""
        self._sdk._log("HYPERLIQUID_GET_BALANCES", {})

        try:
            response = self._sdk.client.get("/v1/platforms/hyperliquid/balances")

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid balances endpoint"
                )

            from .types.hyperliquid import HyperliquidBalances

            # Extract data from standardized API format
            response_data = response["data"]

            # Parse as Balances type
            return HyperliquidBalancesResponse(
                success=True,
                data=HyperliquidBalances(**response_data),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidBalancesResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get balances"
            return HyperliquidBalancesResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_get_positions(self) -> HyperliquidPositionsResponse:
        """Handle get positions requests."""
        self._sdk._log("HYPERLIQUID_GET_POSITIONS", {})

        try:
            response = self._sdk.client.get("/v1/platforms/hyperliquid/positions")

            from .types.hyperliquid import HyperliquidPosition

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid positions endpoint"
                )

            # Extract data from standardized API format
            response_data = response["data"]

            # Parse each position (response_data is an array)
            if not isinstance(response_data, list):
                response_data = []

            parsed_data = [HyperliquidPosition(**item) for item in response_data]

            return HyperliquidPositionsResponse(
                success=True,
                data=parsed_data,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidPositionsResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get positions"
            return HyperliquidPositionsResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_get_open_orders(self) -> HyperliquidOpenOrdersResponse:
        """Handle get open orders requests."""
        self._sdk._log("HYPERLIQUID_GET_OPEN_ORDERS", {})

        try:
            response = self._sdk.client.get("/v1/platforms/hyperliquid/orders")

            from .types.hyperliquid import HyperliquidOrderInfo

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid orders endpoint"
                )

            # Extract data from standardized API format
            response_data = response["data"]

            # Parse each order (response_data is an array)
            if not isinstance(response_data, list):
                response_data = []

            parsed_data = [HyperliquidOrderInfo(**item) for item in response_data]

            return HyperliquidOpenOrdersResponse(
                success=True,
                data=parsed_data,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidOpenOrdersResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get open orders"
            return HyperliquidOpenOrdersResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_get_order_fills(self) -> HyperliquidOrderFillsResponse:
        """Handle get order fills requests."""
        self._sdk._log("HYPERLIQUID_GET_ORDER_FILLS", {})

        try:
            response = self._sdk.client.get(
                "/v1/platforms/hyperliquid/orders/fill-history"
            )

            from .types.hyperliquid import HyperliquidFill

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid order fills endpoint"
                )

            # Extract data from standardized API format
            response_data = response["data"]

            # Parse each fill (response_data is an array)
            if not isinstance(response_data, list):
                response_data = []

            parsed_data = [HyperliquidFill(**item) for item in response_data]

            return HyperliquidOrderFillsResponse(
                success=True,
                data=parsed_data,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidOrderFillsResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get order fills"
            return HyperliquidOrderFillsResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_get_historical_orders(self) -> HyperliquidHistoricalOrdersResponse:
        """Handle get historical orders requests."""
        self._sdk._log("HYPERLIQUID_GET_HISTORICAL_ORDERS", {})

        try:
            response = self._sdk.client.get(
                "/v1/platforms/hyperliquid/orders/historical"
            )

            from .types.hyperliquid import HyperliquidHistoricalOrder

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid historical orders endpoint"
                )

            # Extract data from standardized API format
            response_data = response["data"]

            # Parse each historical order (response_data is an array)
            if not isinstance(response_data, list):
                response_data = []

            parsed_data = [HyperliquidHistoricalOrder(**item) for item in response_data]

            return HyperliquidHistoricalOrdersResponse(
                success=True,
                data=parsed_data,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidHistoricalOrdersResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get historical orders"
            return HyperliquidHistoricalOrdersResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_transfer(
        self, request: HyperliquidTransferRequest | dict
    ) -> HyperliquidTransferResponse:
        """Handle transfer requests."""
        self._sdk._log("HYPERLIQUID_TRANSFER", {"request": request})

        try:
            # Handle both dict and Pydantic model inputs
            if isinstance(request, dict):
                request_obj = HyperliquidTransferRequest(**request)
            else:
                request_obj = request

            response = self._sdk.client.post(
                "/v1/platforms/hyperliquid/transfer",
                request_obj.model_dump(mode="json", exclude_unset=True),
            )

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid transfer endpoint"
                )

            # Extract data from standardized API format (void response)
            # No data to extract for transfer operation

            return HyperliquidTransferResponse(
                success=True,
                data=None,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidTransferResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to transfer"
            return HyperliquidTransferResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )

    def _handle_get_liquidations(
        self, start_time: int | None
    ) -> HyperliquidLiquidationsResponse:
        """Handle get liquidations requests."""
        self._sdk._log("HYPERLIQUID_GET_LIQUIDATIONS", {"start_time": start_time})

        try:
            endpoint = "/v1/platforms/hyperliquid/liquidations"
            if start_time is not None:
                endpoint = f"{endpoint}?startTime={start_time}"

            response = self._sdk.client.get(endpoint)

            from .types.hyperliquid import HyperliquidLiquidation

            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from hyperliquid liquidations endpoint"
                )

            # Extract data from standardized API format
            response_data = response["data"]

            # Parse each liquidation (response_data is an array)
            if not isinstance(response_data, list):
                response_data = []

            parsed_data = [HyperliquidLiquidation(**item) for item in response_data]

            return HyperliquidLiquidationsResponse(
                success=True,
                data=parsed_data,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            return HyperliquidLiquidationsResponse(
                success=False,
                data=None,
                error=api_error.error_message,
                error_details=None,
            )
        except Exception as error:
            error_message = str(error) or "Failed to get liquidations"
            return HyperliquidLiquidationsResponse(
                success=False,
                data=None,
                error=error_message,
                error_details=None,
            )
