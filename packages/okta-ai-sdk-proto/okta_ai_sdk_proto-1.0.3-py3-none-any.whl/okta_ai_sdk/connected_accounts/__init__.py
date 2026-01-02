"""
Connected Accounts module

Provides functionality for external token exchange and connected account flows
"""

from .client import ConnectedAccountsClient
from .types import (
    Auth0Config,
    GetExternalProviderTokenRequest,
    GetExternalProviderTokenResponse,
    CompleteLinkingAndGetTokenRequest,
    CompleteLinkingAndGetTokenResponse,
)

__all__ = [
    "ConnectedAccountsClient",
    "Auth0Config",
    "GetExternalProviderTokenRequest",
    "GetExternalProviderTokenResponse",
    "CompleteLinkingAndGetTokenRequest",
    "CompleteLinkingAndGetTokenResponse",
]

