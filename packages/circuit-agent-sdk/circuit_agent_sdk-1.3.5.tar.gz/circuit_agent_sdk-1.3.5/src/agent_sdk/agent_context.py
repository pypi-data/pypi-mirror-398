"""
Unified agent interface combining request data and SDK methods.

This module provides the AgentContext class that serves as the single interface
agent developers interact with. It combines request metadata with all SDK functionality
into one clean object.
"""

import json
from typing import Literal

from pydantic import BaseModel

from .agent_sdk import AgentSdk
from .memory import MemoryApi
from .platforms import PlatformsApi
from .swidge import SwidgeApi
from .types import (
    ClearSuggestionsResponse,
    EvmMessageSignRequest,
    EvmMessageSignResponse,
    GetCurrentPositionsResponse,
    LogResponse,
    SDKConfig,
    SignAndSendRequest,
    SignAndSendResponse,
    TransactionsResponse,
)
from .types.common import CurrentPosition
from .utils import setup_logging

# Type alias for execution mode
ExecutionMode = Literal["auto", "manual", "hybrid"]


class AgentContext:
    """
    Unified interface for agent developers combining request data and SDK methods.

    This class provides everything an agent needs in a single object:
    - Request metadata (sessionId, walletAddress, etc.)
    - Direct access to SDK methods (memory, platforms, swidge)
    - Unified logging with agent.log()

    The agent developer's execution and unwind functions receive this object:

    ```python
    def run_function(agent: AgentContext) -> None:
        agent.log(f"Starting execution for session {agent.sessionId}")
        agent.memory.set("last_run", str(time.time()))
        positions = agent.platforms.polymarket.positions()
        if positions.success:
            agent.log(f"Found {len(positions.data.positions)} positions")
    ```

    Attributes:
        sessionId: Unique session identifier
        sessionWalletAddress: Wallet address for this session
        currentPositions: Current positions allocated to this agent
        executionMode: Execution mode for this session (auto, manual, hybrid)
        memory: Session-scoped key-value storage
        platforms: Platform-specific integrations (polymarket, etc.)
        swidge: Cross-chain swap operations
    """

    def __init__(
        self,
        sessionId: int,
        sessionWalletAddress: str,
        currentPositions: list[CurrentPosition] | None = None,
        executionMode: ExecutionMode = "auto",
        base_url: str | None = None,
        authorization_header: str | None = None,
    ) -> None:
        """
        Create a new AgentContext instance.

        This is typically created automatically by the Agent wrapper, but can be
        instantiated manually for testing in Jupyter notebooks or scripts.

        Args:
            sessionId: Unique session identifier
            sessionWalletAddress: Wallet address for this session
            currentPositions: Current positions allocated to this agent
            base_url: Override API base URL (detected automatically otherwise)
            authorization_header: Optional Authorization header from incoming request

        Example:
            ```python
            # Manual instantiation for testing
            agent = AgentContext(
                sessionId=123,
                sessionWalletAddress="0x742d35cc6634C0532925a3b8D65e95f32B6b5582",
                currentPositions=[]
            )
            agent.log("Testing agent functionality")
            ```
        """
        # Store request data
        self.sessionId = sessionId
        self.sessionWalletAddress = sessionWalletAddress
        self.currentPositions = currentPositions or []
        self.executionMode: ExecutionMode = executionMode

        # Initialize SDK with session ID
        self._sdk = AgentSdk(
            SDKConfig(
                session_id=sessionId,
                base_url=base_url,
                authorization_header=authorization_header,
            )
        )

        # Set up logger
        self._logger = setup_logging()

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
    #     self._sdk.set_base_url(base_url)

    @property
    def memory(self) -> MemoryApi:
        """
        Access session-scoped key-value storage.

        Returns:
            MemoryApi instance for get/set/delete/list operations
        """
        return self._sdk.memory

    @property
    def platforms(self) -> PlatformsApi:
        """
        Access platform-specific integrations.

        Returns:
            PlatformsApi instance with polymarket and other platform integrations
        """
        return self._sdk.platforms

    @property
    def swidge(self) -> SwidgeApi:
        """
        Access cross-chain swap and bridge operations.

        Returns:
            SwidgeApi instance for quote/execute operations
        """
        return self._sdk.swidge

    def log(
        self,
        message: str | dict | list | BaseModel,
        error: bool = False,
        debug: bool = False,
    ) -> LogResponse:
        """
        Unified logging method that handles console output and backend messaging.

        This method always logs to the console using Python's logger, and conditionally
        sends logs to the backend based on the flags provided. Accepts strings, dicts,
        lists, or Pydantic models - structured data is pretty-printed to console and serialized
        for the backend (truncated to 250 characters).

        **Behavior:**
        - `agent.log("message")` → `logger.info()` + backend POST with type="observe"
        - `agent.log("message", error=True)` → `logger.error()` + backend POST with type="error"
        - `agent.log("message", debug=True)` → `logger.info()` + NO backend call
        - `agent.log(pydantic_model)` → Pretty-printed to console + serialized to backend (truncated)
        - `agent.log({"key": "value"})` → Pretty-printed to console + serialized to backend (truncated)
        - `agent.log([1, 2, 3])` → Pretty-printed to console + serialized to backend (truncated)

        **Input**: `message: str | dict | list | BaseModel, error: bool = False, debug: bool = False`
            - `message` (str | dict | list | BaseModel): The message to log
            - `error` (bool): If True, log as error level and send type="error" to backend
            - `debug` (bool): If True, only log to console (no backend call)

        **Output**: `LogResponse`
            - `success` (bool): Whether the operation succeeded
            - `error` (str | None): Error message on failure
            - `error_details` (dict | None): Detailed error info on failure

        **Examples:**
            ```python
            # Standard info log (console + backend)
            agent.log("Processing transaction")

            # Log a Pydantic model (pretty-printed)
            response = agent.memory.get("key")
            agent.log(response)  # Pretty JSON in console, truncated for backend

            # Log a dict (pretty-printed)
            agent.log({"wallet": agent.sessionWalletAddress, "status": "active"})

            # Log a list/array (pretty-printed)
            agent.log([{"position": 1}, {"position": 2}])

            # Error log (console + backend)
            result = agent.memory.get("key")
            if not result.success:
                agent.log(result.error_message, error=True)

            # Debug log (console only, no backend)
            agent.log("Internal state: processing...", debug=True)

            # Check for errors in logging
            log_result = agent.log("Important message")
            if not log_result.success:
                print(f"Failed to send log: {log_result.error_message}")
            ```

        Args:
            message: The message to log (string, dict, list, or Pydantic model)
            error: If True, log as error and send to backend as error type
            debug: If True, only log to console (skips backend call)

        Returns:
            LogResponse: Response object with success status and error details
        """
        # Prepare console and backend messages
        console_message: str
        backend_message: str

        # Convert message to appropriate format
        if isinstance(message, BaseModel):
            # Pydantic model: serialize to dict then to pretty JSON for console
            message_dict = message.model_dump()
            console_message = json.dumps(message_dict, indent=2, default=str)
            backend_message = json.dumps(message_dict, default=str)
        elif isinstance(message, dict) or isinstance(message, list):
            # Dict or list: pretty print for console
            console_message = json.dumps(message, indent=2, default=str)
            backend_message = json.dumps(message, default=str)
        else:
            # String or other: use as-is
            console_message = str(message)
            backend_message = str(message)

        # Always log to console (unlimited length, pretty-printed for dicts/models)
        if error:
            self._logger.error(console_message)
        else:
            # Use info level for all non-error logs (including debug=True)
            # so developers can see them in the console
            self._logger.info(console_message)

        # If debug=True, skip backend call and return success
        if debug:
            return LogResponse(success=True, data=None, error=None, error_details=None)

        # Send to backend with appropriate type (truncated to 250 chars)
        log_type = "error" if error else "observe"

        try:
            # Use the SDK's internal _send_logs method
            logs_request = [{"type": log_type, "message": backend_message}]
            self._sdk._send_logs(logs_request)
            return LogResponse(success=True, data=None, error=None, error_details=None)
        except Exception as e:
            # Log the error but don't let it crash the agent
            error_message = str(e)
            self._logger.error(f"Failed to send log to backend: {error_message}")
            return LogResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"message": error_message, "type": type(e).__name__},
            )

    def sign_and_send(self, request: SignAndSendRequest | dict) -> SignAndSendResponse:
        """
        Sign and broadcast a transaction on the specified network.

        Delegates to the underlying SDK's sign_and_send method.

        **Input**: `request: SignAndSendRequest | dict`
            - `network` (str): "solana" or "ethereum:chainId"
            - `message` (str | None): Optional context message
            - `request` (dict): Transaction payload (EthereumSignRequest or SolanaSignRequest)

        **Output**: `SignAndSendResponse`
            - `success` (bool): Whether the operation succeeded
            - `tx_hash` (str | None): Transaction hash on success
            - `transaction_url` (str | None): Explorer link on success
            - `error` (str | None): Error message on failure

        **Example:**
            ```python
            response = agent.sign_and_send({
                "network": "ethereum:42161",
                "request": {
                    "to_address": "0x742d35cc6634C0532925a3b8D65e95f32B6b5582",
                    "data": "0x",
                    "value": "1000000000000000000"  # 1 ETH
                },
                "message": "Sending 1 ETH"
            })

            if response.success:
                agent.log(f"Transaction sent: {response.tx_hash}")
            else:
                agent.log(response.error_message, error=True)
            ```

        Args:
            request: Transaction request with network and transaction details

        Returns:
            SignAndSendResponse: Response with transaction hash or error details
        """
        return self._sdk.sign_and_send(request)

    def sign_message(
        self, request: EvmMessageSignRequest | dict
    ) -> EvmMessageSignResponse:
        """
        Sign a message on an EVM network.

        Delegates to the underlying SDK's sign_message method.

        **Input**: `request: EvmMessageSignRequest | dict`
            - `messageType` (str): "eip712" or "eip191"
            - `chainId` (int): Ethereum chain ID
            - `data` (dict): Message data structure

        **Output**: `EvmMessageSignResponse`
            - `status` (int): HTTP status code
            - `v` (int): Signature v component
            - `r` (str): Signature r component
            - `s` (str): Signature s component
            - `formattedSignature` (str): Complete signature string
            - `type` (str): Always "evm"

        **Example:**
            ```python
            response = agent.sign_message({
                "messageType": "eip712",
                "chainId": 1,
                "data": {
                    # EIP712 typed data structure
                }
            })

            if response.status == 200:
                agent.log(f"Message signed: {response.formattedSignature}")
            ```

        Args:
            request: Message signing request with type and data

        Returns:
            EvmMessageSignResponse: Response with signature components
        """
        return self._sdk.sign_message(request)

    def transactions(self) -> TransactionsResponse:
        """
        Get transaction ledger with asset changes.

        Fetches all confirmed transaction asset changes for this session, including
        both EVM and Solana transactions.

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

        Returns:
            TransactionsResponse: Response with asset changes or error details

        Example:
            ```python
            result = agent.transactions()

            if result.success and result.data:
                agent.log(f"Found {len(result.data)} transactions")

                # Filter for outgoing transfers
                outgoing = [c for c in result.data if c.from_ == agent.sessionWalletAddress]

                # Calculate total USD value
                total_usd = sum(
                    float(c.amount) * float(c.tokenUsdPrice)
                    for c in result.data
                    if c.tokenUsdPrice
                )

                agent.log(f"Total USD value: ${total_usd:.2f}")
            else:
                agent.log(result.error or 'Failed to fetch transactions', error=True)
            ```
        """
        return self._sdk.transactions()

    def get_current_positions(self) -> GetCurrentPositionsResponse:
        """
        Get current live positions for the session.

        Retrieves all current positions held by the session wallet with live balance data.
        For ERC1155 positions (e.g., Polymarket), automatically enriches the response with
        detailed market metadata including PNL, current prices, and redeemability status.

        **Output**: `CurrentPositionsResponse`
            - `success` (bool): Whether the operation succeeded
            - `data` (CurrentPositionsData | None): Current positions data on success
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

        Returns:
            CurrentPositionsResponse: Response with enriched positions or error details

        Example:
            ```python
            result = agent.get_current_positions()

            if result.success and result.data:
                agent.log(f"Managing {len(result.data.positions)} positions")

                if result.data.hasPendingTxs:
                    agent.log("⚠️  Warning: Pending transactions may affect balances")

                # Iterate through positions
                for position in result.data.positions:
                    agent.log(f"Position: {position.assetAddress}")
                    agent.log(f"  Quantity: {position.currentQty}")
                    agent.log(f"  Avg Cost: ${position.avgUnitCost}")

                    # Check for Polymarket enrichment
                    if position.polymarketMetadata:
                        pm = position.polymarketMetadata
                        agent.log(f"  Market: {pm.question}")
                        agent.log(f"  Outcome: {pm.outcome}")
                        agent.log(f"  Value: ${pm.valueUsd}")
                        agent.log(f"  PNL: ${pm.pnlUsd} ({pm.pnlPercent}%)")

                        if pm.isRedeemable:
                            agent.log("  ✅ This position is redeemable!")
            else:
                agent.log(result.error or 'Failed to fetch positions', error=True)
            ```
        """
        return self._sdk.get_current_positions()

    def clear_suggested_transactions(self) -> ClearSuggestionsResponse:
        """
        Clear all pending suggested transactions for this session.

        This performs a soft delete by setting the `deletedAt` timestamp on all
        unprocessed suggestions. Useful for clearing stale suggestions before
        creating new ones or when the agent's strategy has changed.

        **Output**: `ClearSuggestionsResponse`
            - `success` (bool): Whether the operation succeeded
            - `error` (str | None): Error message on failure

        Returns:
            ClearSuggestionsResponse: Response with success status or error details

        Example:
            ```python
            # Clear all pending suggestions before creating new ones
            result = agent.clear_suggested_transactions()
            if result.success:
                agent.log("Cleared pending suggestions")
            else:
                agent.log(result.error or "Failed to clear suggestions", error=True)
            ```
        """
        return self._sdk.clear_suggested_transactions()
