"""
Cross-App Access (ID-JAG) type definitions
"""

from typing import Optional, Any, Dict, Literal
from pydantic import BaseModel, Field


class IdJagTokenRequest(BaseModel):
    """ID-JAG Token Request"""
    subject_token: str = Field(..., description="The Okta ID token or access token to exchange")
    subject_token_type: Literal[
        "urn:ietf:params:oauth:token-type:id_token",
        "urn:ietf:params:oauth:token-type:access_token"
    ] = Field("urn:ietf:params:oauth:token-type:id_token", description="Type of the subject token")
    audience: str = Field(..., description="Target audience (e.g., 'http://localhost:5001')")
    client_id: Optional[str] = Field(None, description="Okta client ID (required if using client_secret)")
    client_secret: Optional[str] = Field(None, description="Okta client secret (required if using client_id)")
    scope: Optional[str] = Field(None, description="Requested scope (space-delimited)")
    # JWT Bearer assertion fields (alternative to client_id/client_secret)
    principal_id: Optional[str] = Field(None, description="Agent/Workload Principal ID for JWT bearer assertion")
    private_jwk: Optional[Dict[str, Any]] = Field(None, description="JWK-formatted private key for JWT bearer assertion")


class IdJagTokenResponse(BaseModel):
    """ID-JAG Token Response"""
    access_token: str = Field(..., description="The ID-JAG token")
    issued_token_type: str = Field(..., description="Should be 'urn:ietf:params:oauth:token-type:id-jag'")
    token_type: str = Field(..., description="Should be 'Bearer'")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")


class IdJagTokenVerificationOptions(BaseModel):
    """ID-JAG Token Verification Options"""
    issuer: str = Field(..., description="Expected issuer (e.g., 'https://your-domain.okta.com')")
    audience: str = Field(..., description="Expected audience (e.g., 'http://localhost:5001')")
    jwks_uri: Optional[str] = Field(None, description="Optional JWKS URI, defaults to issuer + /oauth2/v1/keys")


class IdJagTokenVerificationResult(BaseModel):
    """ID-JAG Token Verification Result"""
    valid: bool = Field(..., description="Whether the token is valid")
    payload: Optional[Dict[str, Any]] = Field(None, description="Decoded token payload")
    sub: Optional[str] = Field(None, description="Token subject")
    email: Optional[str] = Field(None, description="User email from token")
    aud: Optional[str] = Field(None, description="Token audience")
    iss: Optional[str] = Field(None, description="Token issuer")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")
    error: Optional[str] = Field(None, description="Error message if verification failed")


class AuthServerTokenRequest(BaseModel):
    """Authorization Server Token Request"""
    id_jag_token: str = Field(..., description="The ID-JAG token to exchange")
    authorization_server_id: str = Field(..., description="Authorization server ID")
    principal_id: Optional[str] = Field(None, description="Agent/Workload Principal ID for JWT bearer assertion")
    private_jwk: Optional[Dict[str, Any]] = Field(None, description="JWK-formatted private key for JWT bearer assertion")


class AuthServerTokenResponse(BaseModel):
    """Authorization Server Token Response"""
    access_token: str = Field(..., description="The access token from authorization server")
    token_type: str = Field(..., description="Should be 'Bearer'")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")
    refresh_token: Optional[str] = Field(None, description="Refresh token if provided")


class AuthServerTokenVerificationOptions(BaseModel):
    """Authorization Server Token Verification Options"""
    issuer: str = Field(..., description="Expected issuer (e.g., 'https://your-domain.okta.com/oauth2/custom-as')")
    audience: str = Field(..., description="Expected audience")
    authorization_server_id: str = Field(..., description="Authorization server ID")
    jwks_uri: Optional[str] = Field(None, description="Optional JWKS URI, defaults to issuer + /v1/keys")


class AuthServerTokenVerificationResult(BaseModel):
    """Authorization Server Token Verification Result"""
    valid: bool = Field(..., description="Whether the token is valid")
    payload: Optional[Dict[str, Any]] = Field(None, description="Decoded token payload")
    sub: Optional[str] = Field(None, description="Token subject")
    email: Optional[str] = Field(None, description="User email from token")
    aud: Optional[str] = Field(None, description="Token audience")
    iss: Optional[str] = Field(None, description="Token issuer")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")
    scope: Optional[str] = Field(None, description="Token scope")
    error: Optional[str] = Field(None, description="Error message if verification failed")

