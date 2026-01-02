"""
Transaction signing type definitions for agent operations.

This module provides types for signing and broadcasting transactions across
different networks (Ethereum and Solana), including support for manual mode
suggestions.
"""

from pydantic import ConfigDict, Field, field_validator, model_validator

from .base import BaseData, BaseRequest, BaseResponse


class EthereumSignRequest(BaseRequest):
    """
    Ethereum-specific transaction request.

    This request type supports all standard EVM transaction parameters including
    gas optimization, fee strategies, and transaction control options.

    Attributes:
        to_address: Recipient address in hex format (0x...)
        data: Transaction data in hex format (0x...)
        value: Transaction value in wei as string
        gas: Optional gas limit for the transaction
        max_fee_per_gas: Optional max fee per gas in wei as string
        max_priority_fee_per_gas: Optional max priority fee per gas in wei as string
        nonce: Optional nonce for the transaction
        enforce_transaction_success: Optional flag to enforce transaction success
    """

    to_address: str = Field(
        ...,
        description="Recipient address in hex format",
        pattern=r"^0x[a-fA-F0-9]{40}$",
    )
    data: str = Field(
        ..., description="Transaction data in hex format", pattern=r"^0x[a-fA-F0-9]*$"
    )
    value: str = Field(..., description="Transaction value in wei as string")
    gas: int | None = Field(None, description="Optional gas limit for the transaction")
    max_fee_per_gas: str | None = Field(
        None, description="Optional max fee per gas in wei as string"
    )
    max_priority_fee_per_gas: str | None = Field(
        None, description="Optional max priority fee per gas in wei as string"
    )
    nonce: int | None = Field(None, description="Optional nonce for the transaction")
    enforce_transaction_success: bool | None = Field(
        None,
        description="Optional flag to enforce transaction success, if set to true, failed tx simulations will be ignored",
    )


class SolanaSignRequest(BaseRequest):
    """Solana-specific transaction request."""

    hex_transaction: str = Field(
        ...,
        alias="hexTransaction",
        description="Serialized VersionedTransaction as hex string",
    )

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class SignAndSendRequest(BaseRequest):
    """
    Main sign_and_send request type with network-specific conditional shapes.

    The request shape changes based on the network field:
    - For ethereum:chainId networks: requires EthereumSignRequest fields
    - For solana network: requires SolanaSignRequest fields

    Attributes:
        network: Target network ("ethereum:chainId" or "solana")
        message: Optional short message attached to the transaction
        request: Network-specific transaction details
        bypass_manual_approval: When True, forces immediate execution even in manual mode
        expires_at: ISO 8601 timestamp for when the suggestion expires (manual mode only)

    Example:
        ```python
        # Ethereum transaction with basic parameters
        sdk.sign_and_send({
            "network": "ethereum:1",
            "message": "Token transfer",
            "request": {
                "to_address": "0x742d35cc6634C0532925a3b8D65e95f32B6b5582",
                "data": "0xa9059cbb...",  # encoded transfer()
                "value": "0"
            }
        })

        # Ethereum transaction with advanced parameters
        sdk.sign_and_send({
            "network": "ethereum:42161",  # Arbitrum
            "message": "Optimized swap",
            "request": {
                "to_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                "data": "0x38ed1739...",  # swapExactTokensForTokens
                "value": "0",
                "gas": 300000,
                "max_fee_per_gas": "20000000000",  # 20 gwei
                "max_priority_fee_per_gas": "2000000000",  # 2 gwei
                "nonce": 42,
                "enforce_transaction_success": True
            }
        })

        # Solana transaction
        sdk.sign_and_send({
            "network": "solana",
            "message": "SOL transfer",
            "request": {
                "hex_transaction": "010001030a0b..."
            }
        })

        # Bypass manual approval in manual mode
        sdk.sign_and_send({
            "network": "ethereum:1",
            "request": {...},
            "bypass_manual_approval": True  # Forces execution even in manual mode
        })
        ```
    """

    network: str = Field(..., description="Target network (ethereum:chainId or solana)")
    message: str | None = Field(
        None,
        description="Optional short message attached to the transaction",
        max_length=250,
    )
    request: EthereumSignRequest | SolanaSignRequest = Field(
        ..., description="Network-specific transaction details"
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

    @field_validator("network")
    @classmethod
    def validate_network(cls, v: str) -> str:
        """Validate network format."""
        if v == "solana":
            return v
        if v.startswith("ethereum:"):
            try:
                chain_id = int(v.split(":")[1])
                if chain_id <= 0:
                    raise ValueError("Chain ID must be positive")
                return v
            except (IndexError, ValueError):
                raise ValueError(
                    "Invalid ethereum network format. Use ethereum:chainId"
                ) from None
        raise ValueError("Network must be 'solana' or 'ethereum:chainId'")

    @model_validator(mode="after")
    def validate_request_matches_network(self) -> "SignAndSendRequest":
        """Ensure request type matches network."""
        if self.network == "solana":
            if not isinstance(self.request, SolanaSignRequest):
                raise ValueError("Solana network requires SolanaSignRequest")
        elif self.network.startswith("ethereum:"):
            if not isinstance(self.request, EthereumSignRequest):
                raise ValueError("Ethereum network requires EthereumSignRequest")

        return self

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class SignAndSendData(BaseData):
    """
    Success data from sign_and_send operations.

    This data is returned in the `data` field when a transaction is successfully
    signed and broadcast.

    Attributes:
        internal_transaction_id: Internal transaction ID for tracking
        tx_hash: Transaction hash once broadcast to the network
        transaction_url: Optional transaction URL (explorer link)
        suggestionId: Suggestion ID (only present when in manual mode)
    """

    internal_transaction_id: int = Field(
        ..., description="Internal transaction ID for tracking"
    )
    tx_hash: str = Field(..., description="Transaction hash once broadcast")
    transaction_url: str | None = Field(
        None, description="Optional transaction URL (explorer link)"
    )
    suggestionId: int | None = Field(
        None, description="Suggestion ID (only present when in manual mode)"
    )


class SuggestedTransactionData(BaseData):
    """
    Data structure for suggested transaction responses.

    When a session is in manual mode and bypassManualApproval is False,
    transaction operations return this data instead of executing immediately.

    Attributes:
        suggested: Always True, indicates this is a suggestion
        suggestionId: Unique identifier for the suggestion record
        details: Transaction details for display to the user
    """

    suggested: bool = Field(
        True, description="Indicates this is a suggested transaction"
    )
    suggestionId: int = Field(
        ..., description="Unique identifier for the suggestion record"
    )
    details: dict = Field(
        ..., description="Transaction details for display to the user"
    )


class SignAndSendResponse(BaseResponse[SignAndSendData | SuggestedTransactionData]):
    """
    Response from sign_and_send operations.

    In auto mode, returns SignAndSendData with transaction hash.
    In manual mode (without bypass), returns SuggestedTransactionData.

    Attributes:
        success: Whether the operation was successful
        data: Transaction or suggestion data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = sdk.sign_and_send({
            "network": "ethereum:1",
            "request": {"to_address": "0x...", "data": "0x", "value": "0"}
        })
        if response.success and response.data:
            if hasattr(response.data, 'suggested') and response.data.suggested:
                # Manual mode - transaction was suggested
                print(f"Suggestion #{response.data.suggestionId}")
            else:
                # Auto mode - transaction was executed
                print(f"Transaction hash: {response.data.tx_hash}")
        else:
            print(f"Failed: {response.error}")
        ```
    """

    data: SignAndSendData | SuggestedTransactionData | None = Field(
        None, description="Transaction or suggestion data (only present on success)"
    )


# Backwards compatibility alias
SuggestedTransactionResponse = SignAndSendResponse
