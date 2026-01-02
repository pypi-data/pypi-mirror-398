"""
Swidge (cross-chain swap) type definitions for agent operations.

These schemas exactly match the execution-layer-sdk for zero friction.
"""

from typing import Annotated, Any, Literal

from pydantic import (
    AliasChoices,
    ConfigDict,
    Discriminator,
    Field,
    field_validator,
)

from .base import BaseData, BaseRequest, BaseResponse
from .transactions import SuggestedTransactionData

# =====================
# Network and Wallet Types (exact copy from execution-layer-sdk)
# =====================


class SwidgeWallet(BaseData):
    """Swidge wallet specification with network and address."""

    address: str = Field(..., description="Wallet address")
    network: str = Field(
        ..., description="Network identifier (e.g., 'solana' or 'ethereum:1')"
    )


# =====================
# Quote Request Types (exact copy from execution-layer-sdk)
# =====================


class SwidgeQuoteRequest(BaseRequest):
    """
    Request parameters for getting a cross-chain swap or bridge quote.

    Used to get pricing and routing information for swapping tokens between networks
    or within the same network. Perfect for bridging assets across chains or swapping
    tokens on the same chain.

    Attributes:
        from_: Source wallet specification
        to: Destination wallet specification
        fromToken: Source token contract address (optional, omit for native tokens like ETH/SOL)
        toToken: Destination token contract address (optional, omit for native tokens like ETH/SOL)
        amount: Amount in token's smallest unit (wei for ETH, lamports for SOL)
        slippage: Slippage tolerance % as string (e.g., "2.0" = 2%, default: "0.5")

    Examples:
        ```python
        # Bridge USDC: Polygon → Arbitrum
        quote_request = SwidgeQuoteRequest(
            from_=SwidgeWallet(network="ethereum:137", address=user_address),
            to=SwidgeWallet(network="ethereum:42161", address=user_address),
            amount="50000000",  # $50 USDC (6 decimals)
            fromToken="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC on Polygon
            toToken="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",   # USDC on Arbitrum
            slippage="2.0",  # 2% slippage for cross-chain
        )

        # Swap USDC → ETH on same chain (using defaults)
        quote_request = SwidgeQuoteRequest(
            from_=SwidgeWallet(network="ethereum:42161", address=user_address),
            to=SwidgeWallet(network="ethereum:42161", address=user_address),
            amount="100000000",  # $100 USDC (6 decimals)
            fromToken="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # USDC
            # toToken omitted = native ETH (default behavior)
            # slippage defaults to "0.5"
        )
        ```
    """

    from_: SwidgeWallet = Field(
        ..., alias="from", description="Source wallet specification"
    )
    to: SwidgeWallet = Field(..., description="Destination wallet specification")
    fromToken: str | None = Field(
        None,
        description="Source token contract address (optional, omit for native tokens)",
    )
    toToken: str | None = Field(
        None,
        description="Destination token contract address (optional, omit for native tokens)",
    )
    amount: str = Field(
        ...,
        description="Amount in token's smallest unit (wei for ETH, lamports for SOL)",
    )
    priceImpact: str = Field(
        default="100.0",
        description="Max price impact % as string (hardcoded to '100.0' to not filter quotes)",
    )
    slippage: str | None = Field(
        None, description="Slippage tolerance % as string (default: '0.5')"
    )

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# =====================
# Quote Response Types (exact copy from execution-layer-sdk)
# =====================


class SwidgeQuoteAsset(BaseData):
    """Asset information in quote response."""

    network: str = Field(..., description="Network identifier")
    address: str = Field(..., description="Wallet address")
    token: str | None = Field(
        None, description="Token contract address (null for native tokens)"
    )
    name: str | None = Field(None, description="Token name")
    symbol: str | None = Field(None, description="Token symbol")
    decimals: int | None = Field(None, description="Token decimals")
    amount: str | None = Field(None, description="Raw amount in smallest unit")
    minimumAmount: str | None = Field(None, description="Minimum amount after slippage")
    amountFormatted: str | None = Field(
        None, description="Human-readable formatted amount"
    )
    amountUsd: str | None = Field(None, description="USD value")


class SwidgePriceImpact(BaseData):
    """Price impact information."""

    usd: str | None = Field(None, description="Price impact in USD")
    percentage: str | None = Field(None, description="Price impact percentage")


class SwidgeFee(BaseData):
    """Fee information for the swap."""

    name: str = Field(..., description="Fee name (e.g., 'gas', 'bridge', 'protocol')")
    amount: str | None = Field(None, description="Raw fee amount")
    amountFormatted: str | None = Field(
        None, description="Human-readable formatted fee amount"
    )
    amountUsd: str | None = Field(None, description="Fee amount in USD")


# Solana instruction for transaction details
class SwidgeSolanaInstruction(BaseData):
    """Solana instruction for transaction details."""

    programId: str = Field(..., description="Program ID")
    keys: list[dict[str, Any]] = Field(..., description="Instruction keys")
    data: str | bytes = Field(..., description="Instruction data")


# EVM transaction details
class SwidgeEvmTransactionDetails(BaseData):
    """EVM transaction details."""

    type: Literal["evm"] = Field(..., description="Transaction type")
    from_: str = Field(
        ..., alias="from", description="Sender address", pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    to: str = Field(
        ..., description="Recipient address", pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    chainId: int = Field(..., description="Chain ID")
    value: int | str | float = Field(
        ...,
        description="Transaction value in wei (can be int, string, or float for large numbers)",
    )
    data: str = Field(..., description="Transaction data", pattern=r"^0x[a-fA-F0-9]*$")
    gas: int | str | float | None = Field(
        None, description="Gas limit (optional, can be int, string, or float)"
    )
    maxFeePerGas: int | str | float | None = Field(
        None, description="Max fee per gas (optional, can be int, string, or float)"
    )
    maxPriorityFeePerGas: int | str | float | None = Field(
        None,
        description="Max priority fee per gas (optional, can be int, string, or float)",
    )

    @field_validator(
        "value", "gas", "maxFeePerGas", "maxPriorityFeePerGas", mode="before"
    )
    @classmethod
    def convert_numeric_to_acceptable_type(cls, v: Any) -> int | str | float | None:
        """Convert any numeric value to an acceptable type, handling large numbers gracefully."""
        if v is None:
            return v
        # If it's already int or str, return as-is
        if isinstance(v, int) or isinstance(v, str):
            return v
        # If it's a float (including scientific notation), convert to int if it's a whole number
        if isinstance(v, float):
            # Check if it's a whole number
            if v.is_integer():
                # Convert to int - Python handles arbitrarily large integers without precision loss
                return int(v)
            else:
                # Non-integer float, keep as float
                return v
        # Fallback: convert to int if possible, otherwise string
        try:
            return int(v)
        except (ValueError, TypeError):
            return str(v)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# Solana transaction details
class SwidgeSolanaTransactionDetails(BaseData):
    """Solana transaction details."""

    type: Literal["solana"] = Field(..., description="Transaction type")
    instructions: list[SwidgeSolanaInstruction] = Field(
        ..., description="Transaction instructions"
    )
    addressLookupTableAddresses: list[str] = Field(
        ..., description="Address lookup table addresses"
    )


# Transaction step schemas (adapted from execution-layer-sdk)
class SwidgeTransactionStep(BaseData):
    """Transaction step in unsigned steps."""

    type: Literal["transaction"] = Field(..., description="Step type")
    description: str = Field(..., description="Human-readable description")
    transactionDetails: Annotated[
        SwidgeEvmTransactionDetails | SwidgeSolanaTransactionDetails,
        Discriminator("type"),
    ] = Field(..., description="Transaction details")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class SwidgeSignatureStep(BaseData):
    """Signature step in unsigned steps."""

    type: Literal["signature"] = Field(..., description="Step type")
    description: str = Field(..., description="Human-readable description")
    signatureData: str = Field(..., description="Signature data")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


SwidgeUnsignedStep = Annotated[
    SwidgeTransactionStep | SwidgeSignatureStep, Discriminator("type")
]


# Swidge data schema (includes quote and execution parameters like slippage)
class SwidgeData(BaseData):
    """Complete Swidge data from quote endpoint (includes routing and slippage settings)."""

    engine: str = Field(..., description="Swap engine (e.g., 'relay', 'lifi')")
    assetSend: SwidgeQuoteAsset = Field(..., description="Asset being sent")
    assetReceive: SwidgeQuoteAsset = Field(
        validation_alias=AliasChoices("assetReceive", "assetReceive"),
        description="Asset being received",
    )
    priceImpact: SwidgePriceImpact = Field(..., description="Price impact information")
    fees: list[SwidgeFee] = Field(..., description="List of fees")
    steps: list[SwidgeUnsignedStep] = Field(
        ..., description="Unsigned transaction steps"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# =====================
# Execute Request Types
# =====================


# Execute request schema - extends SwidgeData with manual mode options
class SwidgeExecuteRequest(SwidgeData):
    """Execute request schema - takes the complete quote response from quote() method with optional manual mode options."""

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

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# =====================
# Execute Response Types
# =====================


class SwidgeStatusInfo(BaseData):
    """Status information for execute response."""

    network: str = Field(..., description="Network identifier")
    txs: list[str] = Field(..., description="Transaction hashes")


class SwidgeExecuteResponseData(BaseData):
    """
    Execute response data - only final statuses returned by API.

    The API waits for completion and never returns "waiting" or "pending" statuses.

    Note: `in_` and `out` are optional because failed transactions (e.g., insufficient funds,
    timeout, quote not found) will have these fields as undefined.
    """

    status: str = Field(
        ...,
        description="Final execution status. Expected values: 'success', 'failure', 'refund', 'delayed'",
    )
    in_: SwidgeStatusInfo | None = Field(
        None,
        alias="in",
        description="Input transaction status (undefined for failed transactions)",
    )
    out: SwidgeStatusInfo | None = Field(
        None,
        alias="out",
        description="Output transaction status (undefined for failed transactions)",
    )
    lastUpdated: int = Field(..., description="Last update timestamp")
    error: str | None = Field(None, description="Error message for failed transactions")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# =====================
# Result Types
# =====================

QUOTE_RESULT = {
    "FOUND": "QUOTE_FOUND",  # Not an error - success case
    "NO_QUOTE_PROVIDED": "No quote provided",  # Generic API error
    "WALLET_NOT_FOUND": "Wallet not found",  # Exact API error string
    "WALLET_MISMATCH": "From wallet does not match session wallet",  # Exact API error string
}

SwidgeQuoteResult = Literal[
    "QUOTE_FOUND",
    "No quote provided",
    "Wallet not found",
    "From wallet does not match session wallet",
]


# =====================
# SDK Response Wrappers
# =====================


class SwidgeQuoteResponse(BaseResponse[SwidgeData]):
    """Swidge quote response wrapper."""

    data: SwidgeData | None = Field(None, description="Quote data")

    def has_data(self) -> bool:
        """
        Check if the response has data (type-safe data check).

        Returns:
            True if success and data is not None.

        Note:
            Use this helper in combination with explicit None checks for proper type narrowing:
            ```python
            quote = agent.swidge.quote({...})
            if quote.has_data() and quote.data is not None:
                # Type checker now knows quote.data is SwidgeData
                execute = agent.swidge.execute(quote.data)
            ```
        """
        return self.success and self.data is not None


class SwidgeExecuteResponse(
    BaseResponse[SwidgeExecuteResponseData | SuggestedTransactionData]
):
    """
    Swidge execute response wrapper.

    In auto mode, returns SwidgeExecuteResponseData with execution details.
    In manual mode (without bypass), returns SuggestedTransactionData.
    """

    data: SwidgeExecuteResponseData | SuggestedTransactionData | None = Field(
        None, description="Execute or suggestion data"
    )

    def has_data(self) -> bool:
        """
        Check if the response has data (type-safe data check).

        Returns:
            True if success and data is not None.

        Note:
            Use this helper in combination with explicit None checks for proper type narrowing:
            ```python
            execute = agent.swidge.execute(quote.data)
            if execute.has_data() and execute.data is not None:
                # Type checker now knows execute.data is SwidgeExecuteResponseData
                print(f"Status: {execute.data.status}")
            ```
        """
        return self.success and self.data is not None
