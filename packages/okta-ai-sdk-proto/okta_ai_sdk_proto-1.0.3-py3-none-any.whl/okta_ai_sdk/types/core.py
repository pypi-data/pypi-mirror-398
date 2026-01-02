"""
Core type definitions for Okta AI SDK
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class OktaAIConfig(BaseModel):
    """Core SDK Configuration"""
    okta_domain: str = Field(..., description="Okta domain (e.g., 'https://your-domain.okta.com')")
    client_id: str = Field(..., description="Okta client ID")
    client_secret: Optional[str] = Field(None, description="Okta client secret (optional)")
    authorization_server_id: Optional[str] = Field("default", description="Authorization server ID")
    timeout: Optional[int] = Field(30000, description="Request timeout in milliseconds")
    retry_attempts: Optional[int] = Field(3, description="Number of retry attempts")
    principal_id: Optional[str] = Field(None, description="Agent/Workload Principal ID for JWT bearer assertion (e.g., 'wlpJ46tr4ks0JJi081t7')")
    private_jwk: Optional[Dict[str, Any]] = Field(None, description="JWK-formatted private key for JWT bearer assertion")

    class Config:
        """Pydantic configuration"""
        populate_by_name = True
        alias_generator = lambda field_name: {
            'okta_domain': 'oktaDomain',
            'client_id': 'clientId',
            'client_secret': 'clientSecret',
            'authorization_server_id': 'authorizationServerId',
            'timeout': 'timeout',
            'retry_attempts': 'retryAttempts',
            'principal_id': 'principalId',
            'private_jwk': 'privateJWK',
        }.get(field_name, field_name)


class SDKError(Exception):
    """Custom SDK Error with additional context"""
    
    def __init__(
        self, 
        message: str, 
        code: str, 
        status_code: Optional[int] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        return {
            "message": self.message,
            "code": self.code,
            "status_code": self.status_code,
            "details": self.details,
        }

