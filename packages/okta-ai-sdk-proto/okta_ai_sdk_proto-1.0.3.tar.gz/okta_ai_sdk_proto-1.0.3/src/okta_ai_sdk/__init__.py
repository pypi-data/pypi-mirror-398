"""
Okta AI SDK for Python

A comprehensive Python SDK for Okta AI applications with support for 
Token Exchange, Cross-App Access (ID-JAG), and Connected Accounts.
"""

from .core.sdk import OktaAISDK
from .token_exchange.client import TokenExchangeClient
from .cross_app_access.client import CrossAppAccessClient
from .connected_accounts.client import ConnectedAccountsClient

# Type exports
from .types import (
    # Core types
    OktaAIConfig,
    SDKError,
    
    # Token Exchange types
    TokenExchangeRequest,
    TokenExchangeResponse,
    TokenVerificationOptions,
    TokenVerificationResult,
    
    # Cross-App Access (ID-JAG) types
    IdJagTokenRequest,
    IdJagTokenResponse,
    IdJagTokenVerificationOptions,
    IdJagTokenVerificationResult,
    AuthServerTokenRequest,
    AuthServerTokenResponse,
    AuthServerTokenVerificationOptions,
    AuthServerTokenVerificationResult,
    
    # Connected Accounts types
    Auth0Config,
    GetExternalProviderTokenRequest,
    GetExternalProviderTokenResponse,
    CompleteLinkingAndGetTokenRequest,
    CompleteLinkingAndGetTokenResponse,
)

__version__ = "1.0.3"
__author__ = "Okta Inc."

__all__ = [
    # Main SDK class
    "OktaAISDK",
    
    # Client classes
    "TokenExchangeClient",
    "CrossAppAccessClient",
    "ConnectedAccountsClient",
    
    # Core types
    "OktaAIConfig",
    "SDKError",
    
    # Token Exchange types
    "TokenExchangeRequest",
    "TokenExchangeResponse",
    "TokenVerificationOptions",
    "TokenVerificationResult",
    
    # Cross-App Access types
    "IdJagTokenRequest",
    "IdJagTokenResponse",
    "IdJagTokenVerificationOptions",
    "IdJagTokenVerificationResult",
    "AuthServerTokenRequest",
    "AuthServerTokenResponse",
    "AuthServerTokenVerificationOptions",
    "AuthServerTokenVerificationResult",
    
    # Connected Accounts types
    "Auth0Config",
    "GetExternalProviderTokenRequest",
    "GetExternalProviderTokenResponse",
    "CompleteLinkingAndGetTokenRequest",
    "CompleteLinkingAndGetTokenResponse",
]

