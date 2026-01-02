"""
Centralized type exports for the Python Agent SDK

This module provides all the type definitions used throughout the SDK,
including network types, request/response models, and utility types.
"""

# Base types
from .base import BaseData, BaseRequest, BaseResponse

# Common types (Network utilities, CurrentPosition)
from .common import (
    CurrentPosition,
    Network,
    get_chain_id_from_network,
    is_ethereum_network,
    is_solana_network,
)

# Configuration types
from .config import SDKConfig

# Hyperliquid types
from .hyperliquid import (
    HyperliquidBalances,
    HyperliquidBalancesResponse,
    HyperliquidDeleteOrderResponse,
    HyperliquidFill,
    HyperliquidHistoricalOrder,
    HyperliquidHistoricalOrdersResponse,
    HyperliquidLiquidatedPosition,
    HyperliquidLiquidation,
    HyperliquidLiquidationsResponse,
    HyperliquidOpenOrdersResponse,
    HyperliquidOrderFillsResponse,
    HyperliquidOrderInfo,
    HyperliquidOrderResponse,
    HyperliquidPerpBalance,
    HyperliquidPlaceOrderRequest,
    HyperliquidPlaceOrderResponse,
    HyperliquidPosition,
    HyperliquidPositionsResponse,
    HyperliquidSpotBalance,
    HyperliquidTransferRequest,
    HyperliquidTransferResponse,
)

# Job status types
from .jobs import UpdateJobStatusRequest, UpdateJobStatusResponse

# Transaction ledger types
from .ledger import AssetChange, TransactionsResponse

# Logging types
from .logging import AddLogRequest, LogResponse

# Memory types
from .memory import (
    MemoryDeleteData,
    MemoryDeleteRequest,
    MemoryDeleteResponse,
    MemoryGetData,
    MemoryGetRequest,
    MemoryGetResponse,
    MemoryListData,
    MemoryListRequest,
    MemoryListResponse,
    MemorySetData,
    MemorySetRequest,
    MemorySetResponse,
)

# Messaging types
from .messaging import (
    EvmMessageSignData,
    EvmMessageSignRequest,
    EvmMessageSignResponse,
)

# Polymarket types
from .polymarket import (
    PolymarketEip712Domain,
    PolymarketEip712Message,
    PolymarketEip712Type,
    PolymarketMarketOrderData,
    PolymarketMarketOrderRequest,
    PolymarketMarketOrderResponse,
    PolymarketOrder,
    PolymarketOrderData,
    PolymarketOrderInfo,
    PolymarketPosition,
    PolymarketPositionsData,
    PolymarketPositionsResponse,
    PolymarketRedeemPositionResult,
    PolymarketRedeemPositionsData,
    PolymarketRedeemPositionsRequest,
    PolymarketRedeemPositionsResponse,
    PolymarketSubmitOrderResult,
)

# Position types
from .positions import (
    EnrichedPosition,
    GetCurrentPositionsData,
    GetCurrentPositionsResponse,
    PolymarketMetadata,
)

# Suggestion management types
from .suggestions import ClearSuggestionsResponse

# Swidge types
from .swidge import (
    QUOTE_RESULT,
    SwidgeData,
    SwidgeEvmTransactionDetails,
    SwidgeExecuteRequest,
    SwidgeExecuteResponse,
    SwidgeExecuteResponseData,
    SwidgeFee,
    SwidgePriceImpact,
    SwidgeQuoteAsset,
    SwidgeQuoteRequest,
    SwidgeQuoteResponse,
    SwidgeStatusInfo,
    SwidgeTransactionStep,
    SwidgeUnsignedStep,
    SwidgeWallet,
)

# Transaction types
from .transactions import (
    EthereumSignRequest,
    SignAndSendData,
    SignAndSendRequest,
    SignAndSendResponse,
    SolanaSignRequest,
    SuggestedTransactionData,
    SuggestedTransactionResponse,
)

__all__ = [
    # Base types
    "BaseRequest",
    "BaseResponse",
    "BaseData",
    # Network types
    "Network",
    "is_ethereum_network",
    "is_solana_network",
    "get_chain_id_from_network",
    # Common types
    "CurrentPosition",
    # Memory types
    "MemorySetRequest",
    "MemoryGetRequest",
    "MemoryDeleteRequest",
    "MemoryListRequest",
    "MemorySetData",
    "MemoryGetData",
    "MemoryDeleteData",
    "MemoryListData",
    "MemorySetResponse",
    "MemoryGetResponse",
    "MemoryDeleteResponse",
    "MemoryListResponse",
    # Polymarket types
    "PolymarketPosition",
    "PolymarketPositionsData",
    "PolymarketMarketOrderRequest",
    "PolymarketOrder",
    "PolymarketEip712Type",
    "PolymarketEip712Domain",
    "PolymarketEip712Message",
    "PolymarketOrderInfo",
    "PolymarketSubmitOrderResult",
    "PolymarketOrderData",
    "PolymarketMarketOrderData",
    "PolymarketRedeemPositionsRequest",
    "PolymarketRedeemPositionResult",
    "PolymarketRedeemPositionsData",
    "PolymarketPositionsResponse",
    "PolymarketMarketOrderResponse",
    "PolymarketRedeemPositionsResponse",
    # Hyperliquid types
    "HyperliquidPlaceOrderRequest",
    "HyperliquidTransferRequest",
    "HyperliquidOrderInfo",
    "HyperliquidPerpBalance",
    "HyperliquidSpotBalance",
    "HyperliquidBalances",
    "HyperliquidPosition",
    "HyperliquidFill",
    "HyperliquidHistoricalOrder",
    "HyperliquidLiquidatedPosition",
    "HyperliquidLiquidation",
    "HyperliquidPlaceOrderResponse",
    "HyperliquidOrderResponse",
    "HyperliquidDeleteOrderResponse",
    "HyperliquidBalancesResponse",
    "HyperliquidPositionsResponse",
    "HyperliquidOpenOrdersResponse",
    "HyperliquidOrderFillsResponse",
    "HyperliquidHistoricalOrdersResponse",
    "HyperliquidTransferResponse",
    "HyperliquidLiquidationsResponse",
    # Swidge types
    "SwidgeWallet",
    "SwidgeData",
    "SwidgeExecuteRequest",
    "SwidgeExecuteResponseData",
    "SwidgeUnsignedStep",
    "SwidgeEvmTransactionDetails",
    "SwidgeFee",
    "SwidgePriceImpact",
    "SwidgeQuoteAsset",
    "SwidgeStatusInfo",
    "SwidgeTransactionStep",
    "SwidgeQuoteRequest",
    "SwidgeQuoteResponse",
    "SwidgeExecuteResponse",
    "QUOTE_RESULT",
    # Core request types
    "SignAndSendRequest",
    "AddLogRequest",
    "EvmMessageSignRequest",
    "EthereumSignRequest",
    "SolanaSignRequest",
    "UpdateJobStatusRequest",
    # Core response types
    "SignAndSendData",
    "SignAndSendResponse",
    "EvmMessageSignData",
    "EvmMessageSignResponse",
    "LogResponse",
    "UpdateJobStatusResponse",
    # Core data types
    "AssetChange",
    "TransactionsResponse",
    "EnrichedPosition",
    "PolymarketMetadata",
    "GetCurrentPositionsData",
    "GetCurrentPositionsResponse",
    "ClearSuggestionsResponse",
    "SuggestedTransactionData",
    "SuggestedTransactionResponse",
    # Configuration types
    "SDKConfig",
]
