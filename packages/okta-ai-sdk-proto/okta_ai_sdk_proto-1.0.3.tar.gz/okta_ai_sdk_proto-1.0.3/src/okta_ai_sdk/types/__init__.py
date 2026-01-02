"""
Type definitions for Okta AI SDK
"""

from .core import (
    OktaAIConfig,
    SDKError,
)

from .token_exchange import (
    TokenExchangeRequest,
    TokenExchangeResponse,
    TokenVerificationOptions,
    TokenVerificationResult,
)

from .cross_app_access import (
    IdJagTokenRequest,
    IdJagTokenResponse,
    IdJagTokenVerificationOptions,
    IdJagTokenVerificationResult,
    AuthServerTokenRequest,
    AuthServerTokenResponse,
    AuthServerTokenVerificationOptions,
    AuthServerTokenVerificationResult,
)

# Import connected_accounts types from the module
from ..connected_accounts.types import (
    Auth0Config,
    GetExternalProviderTokenRequest,
    GetExternalProviderTokenResponse,
    CompleteLinkingAndGetTokenRequest,
    CompleteLinkingAndGetTokenResponse,
)

__all__ = [
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

