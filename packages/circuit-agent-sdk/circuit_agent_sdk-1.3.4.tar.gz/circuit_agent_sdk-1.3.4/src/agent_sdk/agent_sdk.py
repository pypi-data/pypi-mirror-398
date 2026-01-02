"""
Main AgentSdk class with simplified API surface.

This module provides the primary AgentSdk class that serves as the main entry point
for all agent operations. It offers a clean, type-safe interface with just two
core methods that cover the majority of agent interactions.
"""

from typing import Any, cast

from .client import APIClient
from .memory import MemoryApi
from .platforms import PlatformsApi
from .swidge import SwidgeApi
from .types import (
    AddLogRequest,
    AssetChange,
    ClearSuggestionsResponse,
    EthereumSignRequest,
    EvmMessageSignRequest,
    EvmMessageSignResponse,
    GetCurrentPositionsData,
    GetCurrentPositionsResponse,
    SDKConfig,
    SignAndSendData,
    SignAndSendRequest,
    SignAndSendResponse,
    SolanaSignRequest,
    SuggestedTransactionResponse,
    TransactionsResponse,
    UpdateJobStatusRequest,
    UpdateJobStatusResponse,
    get_chain_id_from_network,
    is_ethereum_network,
    is_solana_network,
)


class AgentSdk:
    """
    Main SDK entrypoint used by agents to interact with the Circuit backend.

    Provides a minimal sdk with three core methods that cover the
    majority of agent interactions:

    - send_log() — emit timeline logs for observability and UX
    - sign_message() — sign EIP712 and EIP191 messages on EVM networks
    - sign_and_send() — sign and broadcast transactions across networks
    - swidge — cross-chain swap operations
    - platforms — platform-specific integrations (polymarket, etc.)
    - memory — session-scoped key-value storage
    """

    # Type annotation for the swidge property - this helps IDEs understand the type
    swidge: "SwidgeApi"
    platforms: "PlatformsApi"
    memory: "MemoryApi"

    def __init__(self, config: SDKConfig) -> None:
        """
        Create a new AgentSdk instance.

        Args:
            config: SDK configuration
                - session_id: Numeric session identifier that scopes auth and actions

        Example:
            ```python
            sdk = AgentSdk(SDKConfig(session_id=42))
            ```
        """
        self.config = config
        self.client = APIClient(config)
        # Pass the sign_and_send method to utils to avoid circular dependency
        # self.utils = AgentUtils(self.client, self.config, self.sign_and_send)

        # Initialize swidge property
        self.swidge = SwidgeApi(self)
        # Initialize platforms property
        self.platforms = PlatformsApi(self)
        # Initialize memory property
        self.memory = MemoryApi(self)

    # def set_base_url(self, base_url: str) -> None:
    #     """
    #     **DO NOT USE - WILL BREAK YOUR AGENTS**

    #     ⚠️ **WARNING**: This method will cause issues and break your agents.
    #     Do not use this method.

    #     Args:
    #         base_url: New base URL to use for API requests

    #     Note:
    #         This method is marked as internal and may not appear in IDE autocomplete.
    #     """
    #     self.config.base_url = base_url
    #     self.client = APIClient(self.config)

    def _mask_sensitive_data(self, data: Any) -> Any:
        """
        Mask sensitive information in data structures.

        Args:
            data: Data to mask

        Returns:
            Data with sensitive information masked
        """
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if key.lower() in ["authorization", "x-api-key", "bearer", "token"]:
                    if isinstance(value, str) and len(value) > 8:
                        # Show first 8 characters and mask the rest
                        masked_data[key] = f"{value[:8]}...***MASKED***"
                    else:
                        masked_data[key] = "***MASKED***"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data

    def _log(self, log: str, data: Any = None) -> None:
        """Internal logging for SDK operations - currently a no-op."""
        # SDK internal logging removed for simplicity
        pass

    def send_log(self, log: AddLogRequest | dict) -> None:
        """Add a log to the agent timeline.

        Args:
            log: Log entry with 'type' and 'short_message' fields.
                type: One of "observe", "validate", "reflect", "error", "warning"
                short_message: Brief message (max 250 chars, auto-truncated)

        Example:
            sdk.send_log({"type": "observe", "short_message": "Starting swap"})
        """
        # Handle both dict and Pydantic model inputs
        try:
            if isinstance(log, dict):
                # Automatically truncate logs that exceed 250 characters before validation
                if "short_message" in log and len(log["short_message"]) > 250:
                    original_message = log["short_message"]
                    truncated_message = original_message[:247] + "..."
                    self._log(
                        f"Message truncated from {len(original_message)} to 250 characters"
                    )
                    log["short_message"] = truncated_message

                # Convert dict to Pydantic model for validation and type safety
                message_obj = AddLogRequest(**log)
            else:
                # For Pydantic models, we need to handle truncation differently
                # since validation already happened. We'll create a new dict and truncate it.
                message_dict = log.model_dump()

                if len(message_dict["short_message"]) > 250:
                    original_message = message_dict["short_message"]
                    truncated_message = original_message[:247] + "..."
                    self._log(
                        f"Message truncated from {len(original_message)} to 250 characters"
                    )
                    message_dict["short_message"] = truncated_message
                    # Create a new Pydantic model with the truncated log
                    message_obj = AddLogRequest(**message_dict)
                else:
                    message_obj = log
        except Exception as validation_error:
            # Enhanced error logging for Pydantic validation failures
            error_type = type(validation_error).__name__
            error_message = str(validation_error)
            self._log(
                "SEND_LOG_VALIDATION_ERROR",
                {
                    "error_type": error_type,
                    "error": error_message,
                    "log_input": log,
                    "log_type": type(log).__name__,
                },
            )
            # Silently fail - validation errors shouldn't crash the agent
            return

        self._log("ADD_LOG", message_obj.model_dump())

        # Convert to the internal logs format
        logs_request = [
            {"type": message_obj.type, "message": message_obj.short_message}
        ]

        try:
            self._send_logs(logs_request)
        except Exception as e:
            # Log the error but don't let it bubble up to user code
            error_type = type(e).__name__
            error_message = str(e)
            self._log(
                "SEND_LOG_ERROR",
                {
                    "error_type": error_type,
                    "error": error_message,
                    "log_data": logs_request,
                },
            )
            # Silently fail - logging errors shouldn't crash the agent

    def sign_and_send(self, request: SignAndSendRequest | dict) -> SignAndSendResponse:
        """Sign and broadcast a transaction on the specified network.

        Args:
            request: Transaction request with 'network', 'request', and optional 'message' fields.
                network: "solana" or "ethereum:chainId" (e.g., "ethereum:1", "ethereum:42161")
                message: Optional context message for observability (max 250 chars)
                request: Transaction payload
                    For Ethereum:
                        to_address: Recipient address as hex string
                        data: Calldata as hex string (use "0x" for transfers)
                        value: Wei amount as string
                        gas: Gas limit (optional)
                        max_fee_per_gas: Max fee per gas in wei as string (optional)
                        max_priority_fee_per_gas: Max priority fee per gas in wei as string (optional)
                        nonce: Transaction nonce (optional)
                        enforce_transaction_success: Enforce transaction success (optional)
                    For Solana:
                        hex_transaction: Serialized VersionedTransaction as hex string

        Returns:
            SignAndSendResponse with success status and transaction hash or error details.

        Example:
            sdk.sign_and_send({
                "network": "ethereum:42161",
                "request": {
                    "to_address": "0xabc...",
                    "data": "0x",
                    "value": "1000000000000000",
                    "gas": 21000,
                    "max_fee_per_gas": "20000000000"
                },
                "message": "Transfer"
            })
        """
        try:
            # Handle both dict and Pydantic model inputs (like TypeScript SDK)
            if isinstance(request, dict):
                # Convert dict to Pydantic model for validation and type safety
                request_obj = SignAndSendRequest(**request)
            else:
                request_obj = request
            self._log("SIGN_AND_SEND", {"request": request_obj.model_dump()})

            if is_ethereum_network(request_obj.network):
                chain_id = get_chain_id_from_network(request_obj.network)

                # Ensure we have an Ethereum request
                if not isinstance(request_obj.request, EthereumSignRequest):
                    return SignAndSendResponse(
                        success=False,
                        data=None,
                        error="Ethereum network requires EthereumSignRequest",
                        error_details={
                            "message": "Ethereum network requires EthereumSignRequest"
                        },
                    )

                # Build request payload, only including non-None values
                payload = {
                    "chainId": chain_id,
                    "toAddress": request_obj.request.to_address,
                    "data": request_obj.request.data,
                    "valueWei": request_obj.request.value,  # Map 'value' to 'valueWei'
                }

                if request_obj.message is not None:
                    payload["message"] = request_obj.message
                # Only add optional fields if they have values
                if request_obj.request.gas is not None:
                    payload["gas"] = request_obj.request.gas
                if request_obj.request.max_fee_per_gas is not None:
                    payload["maxFeePerGas"] = request_obj.request.max_fee_per_gas
                if request_obj.request.max_priority_fee_per_gas is not None:
                    payload["maxPriorityFeePerGas"] = (
                        request_obj.request.max_priority_fee_per_gas
                    )
                if request_obj.request.nonce is not None:
                    payload["nonce"] = request_obj.request.nonce
                if request_obj.request.enforce_transaction_success is not None:
                    payload["enforceTransactionSuccess"] = (
                        request_obj.request.enforce_transaction_success
                    )
                # Manual mode options
                if request_obj.bypass_manual_approval:
                    payload["bypassManualApproval"] = request_obj.bypass_manual_approval
                if request_obj.expires_at is not None:
                    payload["expiresAt"] = request_obj.expires_at

                return self._handle_evm_transaction(payload)

            if is_solana_network(request_obj.network):
                # Ensure we have a Solana request
                if not isinstance(request_obj.request, SolanaSignRequest):
                    return SignAndSendResponse(
                        success=False,
                        data=None,
                        error="Solana network requires SolanaSignRequest",
                        error_details={
                            "message": "Solana network requires SolanaSignRequest"
                        },
                    )

                solana_payload: dict[str, Any] = {
                    "hexTransaction": request_obj.request.hex_transaction,
                }
                if request_obj.message is not None:
                    solana_payload["message"] = request_obj.message
                # Manual mode options
                if request_obj.bypass_manual_approval:
                    solana_payload["bypassManualApproval"] = (
                        request_obj.bypass_manual_approval
                    )
                if request_obj.expires_at is not None:
                    solana_payload["expiresAt"] = request_obj.expires_at

                return self._handle_solana_transaction(solana_payload)

            return SignAndSendResponse(
                success=False,
                data=None,
                error=f"Unsupported network: {request_obj.network}",
                error_details={
                    "message": f"Unsupported network: {request_obj.network}"
                },
            )

        except Exception as e:
            self._log("SIGN_AND_SEND_ERROR", {"error": str(e)})
            return SignAndSendResponse(
                success=False,
                data=None,
                error=str(e),
                error_details={"message": str(e), "type": type(e).__name__},
            )

    def sign_message(
        self, request: EvmMessageSignRequest | dict
    ) -> EvmMessageSignResponse:
        """
        Sign a message on an EVM network.

        Args:
            request: EVM message signing input
                - messageType: "eip712" or "eip191"
                - chainId: Ethereum chain ID
                - data: Message data structure

        Returns:
            EvmMessageSignResponse with signature components in .data
            Check .success and use .error_message on failure
        """
        if isinstance(request, dict):
            request_obj = EvmMessageSignRequest(**request)
        else:
            request_obj = request

        self._log("SIGN_MESSAGE", {"request": request_obj.model_dump()})

        try:
            # Call the message signing endpoint
            from .types import EvmMessageSignData

            response = self.client.post(
                "/v1/messages/evm",
                request_obj.model_dump(mode="json", exclude_unset=True),
            )
            if not isinstance(response, dict):
                raise ValueError("Expected dict response from messages/evm endpoint")
            return EvmMessageSignResponse(
                success=True,
                data=EvmMessageSignData(**response["data"]),
                error=None,
                error_details=None,
            )
        except Exception as e:
            self._log("SIGN_MESSAGE_ERROR", {"error": str(e)})
            error_message = str(e)
            return EvmMessageSignResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"message": error_message, "type": type(e).__name__},
            )

    def _update_job_status(
        self, request: UpdateJobStatusRequest | dict
    ) -> UpdateJobStatusResponse:
        """
        Internal method to update job status. Used by the Agent wrapper for automatic tracking.

        This method is not intended for direct use by agent developers - job status tracking
        is handled automatically by the Agent wrapper.
        """
        # Handle both dict and Pydantic model inputs
        if isinstance(request, dict):
            request_obj = UpdateJobStatusRequest(**request)
        else:
            request_obj = request

        self._log("UPDATE_JOB_STATUS", request_obj.model_dump())

        # Call the job status update endpoint
        # Don't include jobId in body since it's in the URL path
        payload: dict[str, str] = {
            "status": request_obj.status,
        }
        if request_obj.errorMessage:
            payload["errorMessage"] = request_obj.errorMessage

        try:
            response = self.client.post(f"/v1/jobs/{request_obj.jobId}/status", payload)
            if not isinstance(response, dict):
                raise ValueError("Expected dict response from jobs status endpoint")
            # Jobs endpoint returns void response (no data field)
            # Return success response with default values
            return UpdateJobStatusResponse(
                status=200, message="Job status updated successfully"
            )
        except Exception as e:
            self._log("UPDATE_JOB_STATUS_ERROR", {"error": str(e)})
            # Return an error response instead of letting the exception bubble up
            return UpdateJobStatusResponse(
                status=400, message=f"Failed to update job status: {str(e)}"
            )

    # =====================
    # Private Implementation Methods (migrated from AgentToolset)
    # =====================

    def _handle_evm_transaction(self, request: dict[str, Any]) -> SignAndSendResponse:
        """Handle EVM transaction signing and broadcasting."""
        try:
            # 1) Sign the transaction (or store as suggestion in manual mode)
            sign_response = self.client.post("/v1/transactions/evm", request)
            if not isinstance(sign_response, dict):
                raise ValueError(
                    "Expected dict response from transactions/evm endpoint"
                )

            # Extract data from standardized response
            sign_data = sign_response["data"]

            # Check if this is a suggested transaction (manual mode)
            if isinstance(sign_data, dict) and sign_data.get("suggested") is True:
                from .types import SuggestedTransactionData

                return SuggestedTransactionResponse(
                    success=True,
                    data=SuggestedTransactionData(**sign_data),
                    error=None,
                    error_details=None,
                )

            # 2) Broadcast the transaction (only if not a suggestion)
            transaction_id = sign_data[
                "id"
            ]  # API returns "id", not "internalTransactionId"
            broadcast_response = self.client.post(
                f"/v1/transactions/evm/{transaction_id}/broadcast"
            )
            if not isinstance(broadcast_response, dict):
                raise ValueError("Expected dict response from broadcast endpoint")

            # Extract data from standardized response
            broadcast_data = broadcast_response["data"]

            return SignAndSendResponse(
                success=True,
                data=SignAndSendData(
                    internal_transaction_id=transaction_id,
                    tx_hash=broadcast_data[
                        "transactionHash"
                    ],  # API returns "transactionHash", not "txHash"
                    transaction_url=None,  # API doesn't return transactionUrl
                    suggestionId=None,
                ),
                error=None,
                error_details=None,
            )
        except Exception as e:
            self._log("EVM_TRANSACTION_ERROR", {"error": str(e)})
            return SignAndSendResponse(
                success=False,
                data=None,
                error=str(e),
                error_details={"message": str(e), "type": type(e).__name__},
            )

    def _handle_solana_transaction(
        self, request: dict[str, Any]
    ) -> SignAndSendResponse:
        """Handle Solana transaction signing and broadcasting."""
        try:
            # 1) Sign the transaction (or store as suggestion in manual mode)
            sign_response = self.client.post("/v1/transactions/solana", request)
            if not isinstance(sign_response, dict):
                raise ValueError(
                    "Expected dict response from transactions/solana endpoint"
                )

            # Extract data from standardized response
            sign_data = sign_response["data"]

            # Check if this is a suggested transaction (manual mode)
            if isinstance(sign_data, dict) and sign_data.get("suggested") is True:
                from .types import SuggestedTransactionData

                return SuggestedTransactionResponse(
                    success=True,
                    data=SuggestedTransactionData(**sign_data),
                    error=None,
                    error_details=None,
                )

            # 2) Broadcast the transaction (only if not a suggestion)
            transaction_id = sign_data[
                "id"
            ]  # API returns "id", not "internalTransactionId"
            broadcast_response = self.client.post(
                f"/v1/transactions/solana/{transaction_id}/broadcast"
            )
            if not isinstance(broadcast_response, dict):
                raise ValueError("Expected dict response from broadcast endpoint")

            # Extract data from standardized response
            broadcast_data = broadcast_response["data"]

            return SignAndSendResponse(
                success=True,
                data=SignAndSendData(
                    internal_transaction_id=transaction_id,
                    tx_hash=broadcast_data[
                        "transactionHash"
                    ],  # API returns "transactionHash", not "txHash"
                    transaction_url=None,  # API doesn't return transactionUrl
                    suggestionId=None,
                ),
                error=None,
                error_details=None,
            )
        except Exception as e:
            self._log("SOLANA_TRANSACTION_ERROR", {"error": str(e)})
            return SignAndSendResponse(
                success=False,
                data=None,
                error=str(e),
                error_details={"message": str(e), "type": type(e).__name__},
            )

    def _send_logs(self, logs: list) -> dict[str, Any]:
        """Send logs to the agent timeline (migrated from AgentToolset)."""
        response = self.client.post("/v1/logs", logs)
        if not isinstance(response, dict):
            raise ValueError("Expected dict response from logs endpoint")
        # Logs endpoint returns void response (no data field)
        # Return empty dict to maintain backward compatibility
        return {}

    def transactions(self) -> TransactionsResponse:
        """
        Get transaction ledger with asset changes.

        Retrieves all confirmed transaction asset changes for the current session.
        Returns both EVM and Solana transactions with their asset transfers.

        **Output**: `TransactionsResponse`
            - `success` (bool): Whether the operation succeeded
            - `data` (list[AssetChange] | None): Array of asset changes on success
                - Each `AssetChange` contains:
                    - `network` (str): Network identifier (e.g., "ethereum:1", "solana")
                    - `transactionHash` (str): Transaction hash
                    - `from_` (str): Sender address
                    - `to` (str): Recipient address
                    - `amount` (str): Amount transferred (as string to preserve precision)
                    - `token` (str | None): Token contract address (None for native tokens)
                    - `tokenId` (str | None): Token ID for NFTs (None for fungible tokens)
                    - `tokenType` (str): Token type (e.g., "native", "ERC20", "ERC721")
                    - `tokenUsdPrice` (str | None): Token price in USD at time of transaction
                    - `timestamp` (str): Transaction timestamp
            - `error` (str | None): Error message on failure
            - `error_details` (dict | None): Detailed error information

        Returns:
            TransactionsResponse: Response with array of asset changes or error details

        Example:
            ```python
            result = sdk.transactions()

            if result.success and result.data:
                print(f"Found {len(result.data)} asset changes")
                for change in result.data:
                    print(f"{change.from_} → {change.to}: {change.amount} ({change.tokenType})")
                    print(f"Token: {change.token or 'native'}, USD Price: {change.tokenUsdPrice or 'N/A'}")
            ```
        """
        try:
            response = self.client.get("/v1/transactions/ledger")
            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from transactions/ledger endpoint"
                )
            # Extract data from standardized response
            response_data = cast(list[dict[str, Any]], response["data"])

            # Parse response as list of AssetChange objects
            asset_changes = [AssetChange(**item) for item in response_data]

            return TransactionsResponse(
                success=True,
                data=asset_changes,
                error=None,
                error_details=None,
            )
        except Exception as e:
            self._log("TRANSACTIONS_ERROR", {"error": str(e)})
            error_message = str(e)
            return TransactionsResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"message": error_message, "type": type(e).__name__},
            )

    def get_current_positions(self) -> GetCurrentPositionsResponse:
        """
        Get current live positions for the session.

        Retrieves all current positions held by the session wallet with live balance data.
        For ERC1155 positions (e.g., Polymarket), automatically enriches the response with
        detailed market metadata including PNL, current prices, and redeemability status.

        **Key Features**:
            - Live balance data from the analytics service
            - Automatic Polymarket metadata enrichment for ERC1155 positions
            - Pending transaction detection to warn of potentially stale balances

        **Output**: `GetCurrentPositionsResponse`
            - `success` (bool): Whether the operation succeeded
            - `data` (GetCurrentPositionsData | None): Current positions data on success
                - `hasPendingTxs` (bool): Whether there are pending transactions
                - `positions` (list[EnrichedPosition]): Array of current positions
                    - `network` (str): Network identifier (e.g., "ethereum:137")
                    - `assetAddress` (str): Token/asset contract address
                    - `tokenId` (str | None): Token ID for NFTs/ERC1155 (None for fungible)
                    - `avgUnitCost` (str): Average unit cost in USD
                    - `currentQty` (str): Current quantity held (raw amount)
                    - `polymarketMetadata` (PolymarketMetadata | None): Detailed Polymarket position data
                        - `question` (str): Market question text
                        - `outcome` (str): Outcome name (e.g., "Yes", "No")
                        - `formattedShares` (str): Human-readable share count
                        - `valueUsd` (str): Current position value in USD
                        - `priceUsd` (str): Current price per share
                        - `averagePriceUsd` (str): Average purchase price
                        - `pnlUsd` (str): Unrealized profit/loss in USD
                        - `pnlPercent` (str): Unrealized profit/loss percentage
                        - `isRedeemable` (bool): Whether position can be redeemed
                        - `endDate` (str): Market end date
                        - Plus additional market details
            - `error` (str | None): Error message on failure
            - `error_details` (dict | None): Detailed error information

        Returns:
            GetCurrentPositionsResponse: Response with enriched positions or error details

        Example:
            ```python
            result = sdk.get_current_positions()

            if result.success and result.data:
                print(f"Found {len(result.data.positions)} positions")

                if result.data.hasPendingTxs:
                    print("⚠️  Warning: Pending transactions may affect balances")

                for position in result.data.positions:
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
                print(f"Failed to get positions: {result.error}")
            ```

        **Success Response Structure**:
            ```json
            {
                "success": true,
                "data": {
                    "positions": [
                        {
                            "network": "ethereum:137",
                            "assetAddress": "0x4d97dcd97eC945f40cF65F87097ACe5EA0476045",
                            "tokenId": "123456",
                            "avgUnitCost": "0.52",
                            "currentQty": "10.5",
                            "polymarketMetadata": {
                                "question": "Will event X happen?",
                                "outcome": "Yes",
                                "formattedShares": "10.5",
                                "valueUsd": "5.46",
                                "priceUsd": "0.52",
                                "averagePriceUsd": "0.50",
                                "pnlUsd": "0.21",
                                "pnlPercent": "4.00",
                                "isRedeemable": false
                            }
                        }
                    ],
                    "hasPendingTxs": false
                }
            }
            ```
        """
        try:
            response = self.client.get("/v1/positions/current")
            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from positions/current endpoint"
                )

            # Extract data from standardized response
            # Parse response as GetCurrentPositionsData
            positions_data = GetCurrentPositionsData(**response["data"])

            return GetCurrentPositionsResponse(
                success=True,
                data=positions_data,
                error=None,
                error_details=None,
            )
        except Exception as e:
            self._log("GET_CURRENT_POSITIONS_ERROR", {"error": str(e)})
            error_message = str(e)
            return GetCurrentPositionsResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"message": error_message, "type": type(e).__name__},
            )

    def clear_suggested_transactions(self) -> ClearSuggestionsResponse:
        """
        Clear all pending suggested transactions for this session.

        This performs a soft delete by setting the `deletedAt` timestamp on all
        unprocessed suggestions. Useful for clearing stale suggestions before
        creating new ones or when the agent's strategy has changed.

        **Output**: `ClearSuggestionsResponse`
            - `success` (bool): Whether the operation succeeded
            - `error` (str | None): Error message on failure
            - `error_details` (dict | None): Detailed error information

        Returns:
            ClearSuggestionsResponse: Response with success status or error details

        Example:
            ```python
            result = sdk.clear_suggested_transactions()
            if result.success:
                print("Cleared all pending suggestions")
            else:
                print(f"Failed: {result.error}")
            ```
        """
        try:
            response = self.client.delete("/v1/sessions/suggestions")
            if not isinstance(response, dict):
                raise ValueError(
                    "Expected dict response from sessions/suggestions endpoint"
                )

            return ClearSuggestionsResponse(
                success=True,
                data=None,
                error=None,
                error_details=None,
            )
        except Exception as e:
            self._log("CLEAR_SUGGESTED_TRANSACTIONS_ERROR", {"error": str(e)})
            error_message = str(e)
            return ClearSuggestionsResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"message": error_message, "type": type(e).__name__},
            )
