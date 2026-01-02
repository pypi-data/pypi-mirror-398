"""
Token Exchange type definitions
"""

from typing import Optional, Any, Dict, Union, Literal
from pydantic import BaseModel, Field


class TokenExchangeRequest(BaseModel):
    """Token Exchange Request"""
    subject_token: str = Field(..., description="The token to exchange")
    subject_token_type: Literal[
        "urn:ietf:params:oauth:token-type:access_token",
        "urn:ietf:params:oauth:token-type:id_token"
    ] = Field(..., description="Type of the subject token")
    audience: str = Field(..., description="Target audience for the new token")
    scope: Optional[str] = Field(None, description="Requested scope for the new token")
    requested_token_type: Optional[Literal["urn:ietf:params:oauth:token-type:access_token"]] = Field(
        "urn:ietf:params:oauth:token-type:access_token",
        description="Requested token type"
    )


class TokenExchangeResponse(BaseModel):
    """Token Exchange Response"""
    access_token: str = Field(..., description="The exchanged access token")
    issued_token_type: str = Field(..., description="Type of the issued token")
    token_type: str = Field(..., description="Token type (usually 'Bearer')")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")


class TokenVerificationOptions(BaseModel):
    """Token Verification Options"""
    issuer: str = Field(..., description="Expected token issuer")
    audience: str = Field(..., description="Expected token audience")
    jwks_uri: Optional[str] = Field(None, description="JWKS URI for key verification")
    clock_tolerance: Optional[int] = Field(0, description="Clock tolerance in seconds")
    expected_scope: Optional[str] = Field(None, description="Expected token scope (optional validation)")


class TokenVerificationResult(BaseModel):
    """Token Verification Result"""
    valid: bool = Field(..., description="Whether the token is valid")
    payload: Optional[Dict[str, Any]] = Field(None, description="Decoded token payload")
    sub: Optional[str] = Field(None, description="Token subject")
    email: Optional[str] = Field(None, description="User email from token")
    aud: Optional[str] = Field(None, description="Token audience")
    iss: Optional[str] = Field(None, description="Token issuer")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")
    iat: Optional[int] = Field(None, description="Token issued at timestamp")
    scope: Optional[str] = Field(None, description="Token scope")
    error: Optional[str] = Field(None, description="Error message if verification failed")

