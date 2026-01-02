"""
Platform integrations namespace.

This module provides the PlatformsApi class which groups platform-specific
integrations like Polymarket under a single namespace.
"""

from typing import TYPE_CHECKING

from .hyperliquid import HyperliquidApi
from .polymarket import PolymarketApi

if TYPE_CHECKING:
    from .agent_sdk import AgentSdk


class PlatformsApi:
    """
    Access to platform-specific integrations.

    Currently supported platforms:
    - polymarket: Prediction market trading operations
    - hyperliquid: Perpetuals trading operations

    All operations are policy-checked and signed automatically.
    """

    # Type annotations for platform properties
    polymarket: "PolymarketApi"
    hyperliquid: "HyperliquidApi"

    def __init__(self, sdk: "AgentSdk"):
        """
        Initialize the PlatformsApi.

        Args:
            sdk: The parent AgentSdk instance
        """
        self._sdk = sdk
        # Initialize platform properties
        self.polymarket = PolymarketApi(sdk)
        self.hyperliquid = HyperliquidApi(sdk)
