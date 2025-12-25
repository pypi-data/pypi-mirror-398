"""Weex SDK - A comprehensive Python SDK for Weex exchange API."""

from weex_sdk.client import WeexClient, AsyncWeexClient
from weex_sdk.websocket import WeexWebSocket, AsyncWeexWebSocket
from weex_sdk.exceptions import (
    WeexAPIException,
    WeexAuthenticationError,
    WeexRateLimitError,
    WeexNetworkError,
    WeexWebSocketError,
    WeexValidationError,
)

# API modules
from weex_sdk.api.account import AccountAPI, AsyncAccountAPI
from weex_sdk.api.market import MarketAPI, AsyncMarketAPI
from weex_sdk.api.trade import TradeAPI, AsyncTradeAPI
from weex_sdk.api.ai import AIAPI, AsyncAIAPI

__version__ = "1.0.1"

__all__ = [
    # Clients
    "WeexClient",
    "AsyncWeexClient",
    "WeexWebSocket",
    "AsyncWeexWebSocket",
    # Exceptions
    "WeexAPIException",
    "WeexAuthenticationError",
    "WeexRateLimitError",
    "WeexNetworkError",
    "WeexWebSocketError",
    "WeexValidationError",
    # API modules
    "AccountAPI",
    "AsyncAccountAPI",
    "MarketAPI",
    "AsyncMarketAPI",
    "TradeAPI",
    "AsyncTradeAPI",
    "AIAPI",
    "AsyncAIAPI",
]
