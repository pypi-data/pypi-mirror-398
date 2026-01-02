"""
Connected Accounts type definitions

Types for external token exchange and connected account flows
"""

from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ExternalTokenExchangeRequest(BaseModel):
    """Request for exchanging token with external provider (e.g., Auth0)"""
    subject_token: str = Field(..., description="The token to exchange")
    subject_token_type: str = Field(..., description="Type of the subject token (supports custom URNs like 'urn:dell:okta-token')")
    audience: str = Field(..., description="Target audience for the new token")
    scope: Optional[str] = Field(None, description="Requested scope for the new token")
    token_endpoint: str = Field(..., description="External provider's token endpoint URL")
    client_id: str = Field(..., description="OAuth client ID for the external provider")
    client_secret: str = Field(..., description="OAuth client secret for the external provider")
    requested_token_type: Optional[str] = Field(
        "urn:ietf:params:oauth:token-type:access_token",
        description="Requested token type (default: access_token)"
    )
    grant_type: Optional[str] = Field(
        "urn:ietf:params:oauth:grant-type:token-exchange",
        description="OAuth grant type (default: token-exchange)"
    )
    additional_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional parameters to include in the token exchange request"
    )


class ExternalTokenExchangeResponse(BaseModel):
    """Response from external token exchange"""
    access_token: str = Field(..., description="The exchanged access token")
    issued_token_type: Optional[str] = Field(None, description="Type of the issued token")
    token_type: str = Field(..., description="Token type (usually 'Bearer')")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")
    refresh_token: Optional[str] = Field(None, description="Refresh token (if provided)")


class FederatedTokenExchangeRequest(BaseModel):
    """Request for federated connection token exchange (e.g., Google, GitHub via Auth0)"""
    subject_token: str = Field(..., description="The access token to exchange")
    subject_token_type: str = Field(
        "urn:ietf:params:oauth:token-type:access_token",
        description="Type of the subject token"
    )
    connection: str = Field(..., description="Federated connection name (e.g., 'google-oauth2', 'github')")
    scopes: Optional[str] = Field(None, description="Requested scopes for the federated token")
    token_endpoint: str = Field(..., description="Token endpoint URL (e.g., Auth0 token endpoint)")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    requested_token_type: str = Field(
        "http://auth0.com/oauth/token-type/federated-connection-access-token",
        description="Requested token type for federated connection"
    )
    grant_type: Optional[str] = Field(
        "urn:auth0:params:oauth:grant-type:token-exchange:federated-connection-access-token",
        description="Grant type for federated token exchange"
    )


class FederatedTokenExchangeResponse(BaseModel):
    """Response from federated token exchange"""
    access_token: str = Field(..., description="The federated provider access token")
    token_type: str = Field(..., description="Token type (usually 'Bearer')")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")
    issued_token_type: Optional[str] = Field(None, description="Type of the issued token")


class ConnectedAccountInitiateRequest(BaseModel):
    """Request to initiate connected account linking"""
    connection: str = Field(..., description="Connection name (e.g., 'google-oauth2', 'github')")
    redirect_uri: str = Field(..., description="Redirect URI for the authorization callback")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")
    code_challenge: Optional[str] = Field(None, description="PKCE code challenge")
    code_challenge_method: Optional[Literal["S256", "plain"]] = Field(
        None,
        description="PKCE code challenge method"
    )
    authorization_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional authorization parameters to pass to the provider"
    )


class ConnectedAccountInitiateResponse(BaseModel):
    """Response from account linking initiation"""
    auth_session: str = Field(..., description="Authentication session identifier")
    connect_uri: str = Field(..., description="Base connection URI")
    connect_params: Dict[str, Any] = Field(..., description="Connection parameters including ticket")
    authorization_url: str = Field(..., description="Full authorization URL with ticket parameter")


class ConnectedAccountCompleteRequest(BaseModel):
    """Request to complete account linking"""
    auth_session: str = Field(..., description="Authentication session identifier from initiation")
    connect_code: str = Field(..., description="Authorization code from the callback URL")
    redirect_uri: str = Field(..., description="Redirect URI (must match initiation request)")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier (if code_challenge was used)")


class ConnectedAccountCompleteResponse(BaseModel):
    """Response from account linking completion"""
    success: bool = Field(..., description="Whether the linking was successful")
    connection_id: Optional[str] = Field(None, description="Connected account identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Full response data from the provider")


class Auth0Config(BaseModel):
    """Auth0 configuration for connected account flows"""
    token_endpoint: str = Field(..., description="Auth0 token endpoint URL")
    myaccount_connect_endpoint: str = Field(..., description="Auth0 MyAccount connect endpoint URL")
    myaccount_complete_endpoint: str = Field(..., description="Auth0 MyAccount complete endpoint URL")
    vault_audience: str = Field(..., description="Auth0 vault audience")
    myaccount_audience: str = Field(..., description="Auth0 MyAccount audience")
    vault_token_type: str = Field(..., description="Custom token type for Okta token (e.g., 'urn:dell:okta-token')")
    vault_scope: str = Field(..., description="Scope for vault token (e.g., 'read:vault')")
    vault_client_id: str = Field(..., description="Auth0 vault API client ID")
    vault_client_secret: str = Field(..., description="Auth0 vault API client secret")
    myaccount_client_id: str = Field(..., description="Auth0 MyAccount client ID")
    myaccount_client_secret: str = Field(..., description="Auth0 MyAccount client secret")


class GetExternalProviderTokenRequest(BaseModel):
    """Request to get external provider token (tries vault first, initiates linking if needed)"""
    okta_access_token: str = Field(..., description="Okta access token to exchange")
    auth0_config: Auth0Config = Field(..., description="Auth0 configuration")
    connection: str = Field(..., description="Federated connection name (e.g., 'google-oauth2', 'github')")
    redirect_uri: str = Field(..., description="Redirect URI for account linking callback")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")
    authorization_params: Optional[Dict[str, Any]] = Field(None, description="Additional authorization parameters")


class GetExternalProviderTokenResponse(BaseModel):
    """Response from get external provider token"""
    token: Optional[str] = Field(None, description="External provider token (if found in vault)")
    token_type: Optional[str] = Field(None, description="Token type (usually 'Bearer')")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")
    requires_linking: bool = Field(..., description="Whether account linking is required")
    authorization_url: Optional[str] = Field(None, description="Authorization URL for account linking (if requires_linking is True)")
    auth_session: Optional[str] = Field(None, description="Authentication session identifier (if requires_linking is True)")


class CompleteLinkingAndGetTokenRequest(BaseModel):
    """Request to complete account linking and get external provider token"""
    auth_session: str = Field(..., description="Authentication session identifier from initiation")
    connect_code: str = Field(..., description="Authorization code from the callback URL")
    redirect_uri: str = Field(..., description="Redirect URI (must match initiation request)")
    auth0_config: Auth0Config = Field(..., description="Auth0 configuration")
    connection: str = Field(..., description="Federated connection name (e.g., 'google-oauth2', 'github')")
    okta_access_token: str = Field(..., description="Okta access token (needed to get fresh Auth0 vault token)")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier (if code_challenge was used)")


class CompleteLinkingAndGetTokenResponse(BaseModel):
    """Response from complete linking and get token"""
    token: str = Field(..., description="External provider token")
    token_type: str = Field(..., description="Token type (usually 'Bearer')")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")
    connection_id: Optional[str] = Field(None, description="Connected account identifier")
    user_id: Optional[str] = Field(None, description="User identifier")

