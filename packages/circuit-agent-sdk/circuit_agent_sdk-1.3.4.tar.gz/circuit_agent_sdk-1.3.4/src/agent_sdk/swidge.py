"""
Swidge cross-chain swap operations.

This module provides the SwidgeApi class for cross-chain swaps and bridges
using the Swidge protocol.
"""

import json
from typing import TYPE_CHECKING, Any, overload

from .client import APIError
from .types import (
    SuggestedTransactionResponse,
    SwidgeData,
    SwidgeExecuteResponse,
    SwidgeExecuteResponseData,
    SwidgeQuoteRequest,
    SwidgeQuoteResponse,
)
from .types.swidge import SwidgeExecuteRequest

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


def _drop_none_keys(d: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    """Return a shallow copy with the specified keys removed when their value is None."""
    return {k: v for k, v in d.items() if not (k in keys and v is None)}


def _normalize_swidge_execute_quote_payload(quote: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a single quote payload for POST /v1/swap/execute to match the API's Zod schema.

    This is intentionally path-aware to avoid accidental stripping of required fields.

    Key rule (current execution-layer-sdk schema):
    - `assetSend.token` and `assetReceive.token` are `.nullable()` but NOT `.optional()`.
      They MUST be present. Native tokens are represented by `null`.
    """
    q = dict(quote)  # shallow copy

    # Ensure asset objects exist and always include `token` (nullable but required).
    for asset_key in ("assetSend", "assetReceive"):
        asset_val = q.get(asset_key)
        asset: dict[str, Any] = dict(asset_val) if isinstance(asset_val, dict) else {}

        if "token" not in asset:
            asset["token"] = None

        # zQuoteAsset optional fields
        asset = _drop_none_keys(asset, {"minimumAmount", "amountUsd"})
        q[asset_key] = asset

    # zPriceImpact.usd is optional
    if isinstance(q.get("priceImpact"), dict):
        q["priceImpact"] = _drop_none_keys(dict(q["priceImpact"]), {"usd"})

    # zFees.amount / amountFormatted / amountUsd are optional
    fees_val = q.get("fees")
    if isinstance(fees_val, list):
        normalized_fees: list[Any] = []
        for fee in fees_val:
            if isinstance(fee, dict):
                normalized_fees.append(
                    _drop_none_keys(
                        dict(fee), {"amount", "amountFormatted", "amountUsd"}
                    )
                )
            else:
                normalized_fees.append(fee)
        q["fees"] = normalized_fees

    # steps[].transactionDetails optional EVM gas fields must be omitted when None
    steps_val = q.get("steps")
    if isinstance(steps_val, list):
        normalized_steps: list[Any] = []
        for step in steps_val:
            if not isinstance(step, dict):
                normalized_steps.append(step)
                continue

            step_copy = dict(step)
            td = step_copy.get("transactionDetails")
            if isinstance(td, dict) and td.get("type") == "evm":
                step_copy["transactionDetails"] = _drop_none_keys(
                    dict(td), {"gas", "maxFeePerGas", "maxPriorityFeePerGas"}
                )
            normalized_steps.append(step_copy)
        q["steps"] = normalized_steps

    # zQuoteOutput.quoteContext is optional
    if q.get("quoteContext") is None:
        q.pop("quoteContext", None)

    # agent-api manual mode extensions on execute:
    # - bypassManualApproval: optional boolean (omit if None)
    # - expiresAt: optional + nullable date (omit if None; null would also be accepted)
    if q.get("bypassManualApproval") is None:
        q.pop("bypassManualApproval", None)
    if q.get("expiresAt") is None:
        q.pop("expiresAt", None)

    return q


class SwidgeApi:
    """Cross-chain swap operations using Swidge.

    Workflow: quote() -> execute(quote.data) -> check result.data.status
    """

    def __init__(self, sdk: "AgentSdk"):
        self._sdk = sdk

    def quote(self, request: SwidgeQuoteRequest | dict) -> SwidgeQuoteResponse:
        """Get a cross-chain swap or bridge quote.

        Args:
            request: Quote parameters with wallet info, amount, and optional tokens/slippage.
                from: Source wallet {"network": "ethereum:1", "address": "0x..."}
                to: Destination wallet {"network": "ethereum:42161", "address": "0x..."}
                amount: Amount in smallest unit (e.g., "1000000000000000000" for 1 ETH)
                fromToken: Source token address (optional, omit for native tokens)
                toToken: Destination token address (optional, omit for native tokens)
                slippage: Slippage tolerance % as string (default: "0.5")
                engines: List of swap engines to use (options: ["lifi", "relay"])
        Returns:
            SwidgeQuoteResponse with pricing, fees, and transaction steps.

        Example:
            quote = sdk.swidge.quote({
                "from": {"network": "ethereum:1", "address": user_address},
                "to": {"network": "ethereum:42161", "address": user_address},
                "amount": "1000000000000000000",  # 1 ETH
                "toToken": "0x2f2a2543B76A4166549F7aaB2e75BEF0aefC5b0f"  # WBTC
            })
        """
        return self._handle_swidge_quote(request)

    @overload
    def execute(
        self, quote_data: SwidgeData | SwidgeExecuteRequest
    ) -> SwidgeExecuteResponse | SuggestedTransactionResponse: ...

    @overload
    def execute(
        self, quote_data: list[SwidgeData | SwidgeExecuteRequest]
    ) -> list[SwidgeExecuteResponse | SuggestedTransactionResponse]: ...

    def execute(
        self,
        quote_data: SwidgeData
        | SwidgeExecuteRequest
        | list[SwidgeData | SwidgeExecuteRequest],
    ) -> (
        SwidgeExecuteResponse
        | SuggestedTransactionResponse
        | list[SwidgeExecuteResponse | SuggestedTransactionResponse]
    ):
        """Execute a cross-chain swap or bridge using a quote.

        Supports both single and bulk execution:
        - Pass a single quote → get a single response
        - Pass a list of quotes → get a list of responses

        **Manual Mode**: When the session is in manual or hybrid execution mode, this method
        returns a `SuggestedTransactionResponse` instead of executing immediately. The transaction
        will be queued for user approval in the Circuit interface. For bulk execution, each
        transaction in the list may independently be executed or suggested based on the session mode.

        **Output (Auto Mode)**: `SwidgeExecuteResponse`
            - `success` (bool): Whether the operation was successful
            - `data` (SwidgeExecuteResponseData): Execution details
              - `status` (str): Transaction status
              - `txHash` (str | None): Transaction hash when available
              - Additional status and tracking information
            - `error` (str | None): Error message (only present on failure)

        **Output (Manual Mode)**: `SuggestedTransactionResponse`
            - `success` (bool): Whether the suggestion was created successfully
            - `data` (SuggestedTransactionData): Suggestion details
              - `suggested` (bool): Always True
              - `suggestionId` (int): Unique suggestion identifier
              - `details` (dict): Transaction details for user review
            - `error` (str | None): Error message (only present on failure)

        Args:
            quote_data: Complete quote object(s) from sdk.swidge.quote().

        Returns:
            SwidgeExecuteResponse | SuggestedTransactionResponse: Single response when passed a
            single quote, or list of responses when passed a list of quotes

        Example:
            # Single execution (type-safe pattern)
            quote = sdk.swidge.quote({...})
            if quote.success and quote.data is not None:
                result = sdk.swidge.execute(quote.data)
                if result.success and result.data is not None:
                    # Check if transaction was suggested (manual mode) vs executed (auto mode)
                    if hasattr(result.data, 'suggested') and result.data.suggested:
                        print(f"Swap suggested: #{result.data.suggestionId}")
                        print("Awaiting user approval in Circuit interface")
                    else:
                        print(f"Status: {result.data.status}")
                        if result.data.txHash:
                            print(f"Transaction: {result.data.txHash}")

            # Bulk execution (type-safe pattern)
            quote1 = sdk.swidge.quote({...})
            quote2 = sdk.swidge.quote({...})
            if (quote1.success and quote1.data is not None and
                quote2.success and quote2.data is not None):
                results = sdk.swidge.execute([quote1.data, quote2.data])
                for result in results:
                    if result.success and result.data is not None:
                        if hasattr(result.data, 'suggested') and result.data.suggested:
                            print(f"Swap suggested: #{result.data.suggestionId}")
                        else:
                            print(f"Status: {result.data.status}")
        """
        return self._handle_swidge_execute(quote_data)

    def _handle_swidge_quote(
        self, request: SwidgeQuoteRequest | dict
    ) -> SwidgeQuoteResponse:
        """Handle swidge quote requests."""
        self._sdk._log("SWIDGE_QUOTE", {"request": request})

        try:
            # Handle both dict and Pydantic model inputs
            if isinstance(request, dict):
                request_obj = SwidgeQuoteRequest(**request)
            else:
                request_obj = request

            response = self._sdk.client.post(
                "/v1/swap/quote",
                request_obj.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )

            # Parse into SwidgeData with extra="allow" to preserve all API fields
            # This is critical - we must not drop any fields the API returns
            if not isinstance(response, dict):
                raise ValueError("Expected dict response from swidge quote endpoint")
            return SwidgeQuoteResponse(
                success=True,
                error=None,
                data=SwidgeData(**response["data"]),
                error_details=None,
            )
        except APIError as api_error:
            # APIError has both error and message from API response
            self._sdk._log("=== SWIDGE QUOTE ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("=========================")

            return SwidgeQuoteResponse(
                success=False,
                data=None,
                error=_ensure_string_error(
                    api_error.error_message
                ),  # Always ensure it's a string
                error_details=api_error.error_details,  # Contains both 'error' and 'message' from API
            )
        except Exception as error:
            # Handle unexpected non-API errors
            error_message = _ensure_string_error(
                str(error) or "Failed to get swidge quote"
            )
            return SwidgeQuoteResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )

    @overload
    def _handle_swidge_execute(
        self, quote_data: SwidgeData | SwidgeExecuteRequest
    ) -> SwidgeExecuteResponse | SuggestedTransactionResponse: ...

    @overload
    def _handle_swidge_execute(
        self, quote_data: list[SwidgeData | SwidgeExecuteRequest]
    ) -> list[SwidgeExecuteResponse | SuggestedTransactionResponse]: ...

    def _handle_swidge_execute(
        self,
        quote_data: SwidgeData
        | SwidgeExecuteRequest
        | list[SwidgeData | SwidgeExecuteRequest],
    ) -> (
        SwidgeExecuteResponse
        | SuggestedTransactionResponse
        | list[SwidgeExecuteResponse | SuggestedTransactionResponse]
    ):
        """Handle swidge execute requests (single or bulk)."""

        # Log execution type
        if isinstance(quote_data, list):
            self._sdk._log("SWIDGE_EXECUTE", {"quotes": f"{len(quote_data)} quotes"})
        else:
            self._sdk._log("SWIDGE_EXECUTE", {"quote": quote_data})

        try:
            # Prepare payload - handle both single and list cases
            payload: list[dict[str, Any]] | dict[str, Any]
            if isinstance(quote_data, list):
                # Serialize each quote in the list
                payload = []
                for quote in quote_data:
                    quote_payload = quote.model_dump(
                        mode="json", by_alias=True, exclude_none=False
                    )
                    payload.append(
                        _normalize_swidge_execute_quote_payload(quote_payload)
                    )
            else:
                payload = quote_data.model_dump(
                    mode="json", by_alias=True, exclude_none=False
                )
                payload = _normalize_swidge_execute_quote_payload(payload)

            # Always use the single /execute endpoint
            response = self._sdk.client.post(
                "/v1/swap/execute",
                payload,
            )

            # Extract data from standardized API response
            if not isinstance(response, dict):
                raise ValueError("Expected dict response from swidge execute endpoint")

            response_data = response["data"]

            # Handle response based on input type
            if isinstance(quote_data, list):
                # Response should be a list
                if not isinstance(response_data, list):
                    raise ValueError("Expected list response for bulk execution")

                wrapped_responses: list[
                    SwidgeExecuteResponse | SuggestedTransactionResponse
                ] = []
                for item in response_data:
                    # Check if this is a suggested transaction (manual mode)
                    if isinstance(item, dict) and item.get("suggested") is True:
                        from .types import SuggestedTransactionData

                        suggested_data = SuggestedTransactionData(**item)
                        wrapped_responses.append(
                            SuggestedTransactionResponse(
                                success=True,
                                data=suggested_data,
                                error=None,
                                error_details=None,
                            )
                        )
                    else:
                        execute_data = SwidgeExecuteResponseData(**item)
                        # success=True only if status is 'success'
                        is_success = execute_data.status == "success"
                        wrapped_responses.append(
                            SwidgeExecuteResponse(
                                success=is_success,
                                error=execute_data.error if not is_success else None,
                                data=execute_data,
                                error_details=None,
                            )
                        )
                return wrapped_responses
            else:
                # Single response
                if not isinstance(response_data, dict):
                    raise ValueError("Expected dict response for single execution")

                # Check if this is a suggested transaction (manual mode)
                if response_data.get("suggested") is True:
                    from .types import SuggestedTransactionData

                    suggested_data = SuggestedTransactionData(**response_data)
                    return SuggestedTransactionResponse(
                        success=True,
                        data=suggested_data,
                        error=None,
                        error_details=None,
                    )

                execute_data = SwidgeExecuteResponseData(**response_data)
                # success=True only if status is 'success'
                is_success = execute_data.status == "success"
                return SwidgeExecuteResponse(
                    success=is_success,
                    error=execute_data.error if not is_success else None,
                    data=execute_data,
                    error_details=None,
                )

        except APIError as api_error:
            # APIError has both error and message from API response
            self._sdk._log("=== SWIDGE EXECUTE ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("============================")

            error_response = SwidgeExecuteResponse(
                success=False,
                data=None,
                error=_ensure_string_error(api_error.error_message),
                error_details=api_error.error_details,
            )

            # Return matching type based on input
            if isinstance(quote_data, list):
                return [error_response]
            else:
                return error_response

        except Exception as error:
            # Handle unexpected non-API errors
            error_message = _ensure_string_error(
                str(error) or "Failed to execute swidge swap"
            )
            error_response = SwidgeExecuteResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )

            # Return matching type based on input
            if isinstance(quote_data, list):
                return [error_response]
            else:
                return error_response
