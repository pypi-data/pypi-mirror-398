"""
Token Exchange Client

Implements OAuth 2.0 Token Exchange (RFC 8693) for Okta
"""

import json
import base64
import time
from typing import Dict, Any, Optional
from urllib.parse import urlencode

import requests
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKError

from ..types import (
    OktaAIConfig,
    TokenExchangeRequest,
    TokenExchangeResponse,
    TokenVerificationOptions,
    TokenVerificationResult,
    SDKError,
)


class TokenExchangeClient:
    """Token Exchange Client for OAuth 2.0 Token Exchange (RFC 8693)"""

    def __init__(self, config: OktaAIConfig):
        """Initialize the Token Exchange Client"""
        self.config = config
        self.session = requests.Session()
        self.session.timeout = config.timeout / 1000 if config.timeout else 30  # Convert ms to seconds

    def exchange_token(self, request: TokenExchangeRequest) -> TokenExchangeResponse:
        """
        Exchange a token for a new token with different audience/scope
        Based on Okta's Token Exchange implementation
        """
        try:
            print(" Exchanging token...")
            print(f" Audience: {request.audience}")
            print(f" Token Type: {request.subject_token_type}")

            token_url = f"{self.config.okta_domain}/oauth2/{self.config.authorization_server_id}/v1/token"
            
            # Prepare form data
            form_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
                'subject_token': request.subject_token,
                'subject_token_type': request.subject_token_type,
                'audience': request.audience,
                'client_id': self.config.client_id,
            }
            
            if self.config.client_secret:
                form_data['client_secret'] = self.config.client_secret
            
            if request.scope:
                form_data['scope'] = request.scope
            
            if request.requested_token_type:
                form_data['requested_token_type'] = request.requested_token_type

            print(f" Making token exchange request to: {token_url}")

            response = self.session.post(
                token_url,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            response.raise_for_status()
            response_data = response.json()

            print(" Token exchange successful")
            print(f" Issued token type: {response_data.get('issued_token_type')}")
            print(f" Expires in: {response_data.get('expires_in', 'N/A')} seconds")

            return TokenExchangeResponse(**response_data)

        except requests.exceptions.RequestException as e:
            print(f" Token exchange failed: {e}")
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    raise self._create_error(
                        f"Token exchange failed: {error_message}",
                        'TOKEN_EXCHANGE_FAILED',
                        e.response.status_code,
                        error_data
                    )
                except (ValueError, KeyError):
                    raise self._create_error(
                        f"Token exchange failed: {e.response.text}",
                        'TOKEN_EXCHANGE_FAILED',
                        e.response.status_code
                    )
            
            raise self._create_error(
                f"Token exchange failed: {str(e)}",
                'TOKEN_EXCHANGE_ERROR'
            )

    def verify_token(self, token: str, options: TokenVerificationOptions) -> TokenVerificationResult:
        """
        Verify a token using Okta's JWKS
        Similar to okta-jwt-verifier-js functionality
        """
        try:
            print(" Verifying token...")
            print(f" Expected Issuer: {options.issuer}")
            print(f" Expected Audience: {options.audience}")

            # Determine JWKS URI - use custom auth server if specified
            if options.jwks_uri:
                jwks_uri = options.jwks_uri
            else:
                # Extract authorization server ID from issuer if present
                if '/oauth2/' in options.issuer:
                    # Issuer already contains auth server ID (e.g., https://domain.okta.com/oauth2/custom-as)
                    jwks_uri = f"{options.issuer}/v1/keys"
                else:
                    # Use default auth server
                    jwks_uri = f"{options.issuer}/oauth2/default/v1/keys"
            print(f" JWKS URI: {jwks_uri}")

            # Create JWK client
            jwks_client = PyJWKClient(jwks_uri)

            # Get the signing key
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Verify the token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=options.audience,
                issuer=options.issuer,
                options={"verify_exp": True, "verify_aud": True, "verify_iss": True},
                leeway=options.clock_tolerance or 0
            )

            # Extract scope from token - Okta uses 'scp' claim as array
            token_scp = payload.get('scp', [])
            token_scope = payload.get('scope')  # Fallback to 'scope' if present
            
            # Ensure token_scp is a list
            if not isinstance(token_scp, list):
                token_scp = [str(token_scp)] if token_scp else []
            
            # Use scp if available, otherwise fallback to scope
            final_scope = ' '.join(token_scp) if token_scp else token_scope
            
            # Validate scope if expected scope is provided
            if options.expected_scope:
                # Parse expected scope string into array
                expected_scopes = [scope.strip() for scope in options.expected_scope.split()]
                expected_scopes = [scope for scope in expected_scopes if scope]  # Remove empty strings
                
                # Check if all expected scopes are present in token scopes
                missing_scopes = [scope for scope in expected_scopes if scope not in token_scp]
                
                if missing_scopes:
                    print(f" Scope validation failed: missing scopes {missing_scopes}")
                    print(f"   Expected: {expected_scopes}")
                    print(f"   Token has: {token_scp}")
                    return TokenVerificationResult(
                        valid=False,
                        error=f"Missing required scopes: {missing_scopes}"
                    )

            print(" Token verified successfully")
            print(f" Subject: {payload.get('sub')}")
            print(f" Email: {payload.get('email', 'N/A')}")
            print(f" Audience: {payload.get('aud')}")
            print(f" Issuer: {payload.get('iss')}")
            print(f" Scopes: {token_scp if token_scp else 'N/A'}")
            print(f" Expires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload.get('exp', 0)))}")

            return TokenVerificationResult(
                valid=True,
                payload=payload,
                sub=payload.get('sub'),
                email=payload.get('email'),
                aud=payload.get('aud'),
                iss=payload.get('iss'),
                exp=payload.get('exp'),
                iat=payload.get('iat'),
                scope=final_scope
            )

        except (InvalidTokenError, PyJWKError) as e:
            print(f" Token verification failed: {e}")
            return TokenVerificationResult(
                valid=False,
                error=str(e)
            )
        except Exception as e:
            print(f" Token verification failed: {e}")
            return TokenVerificationResult(
                valid=False,
                error=f"Unknown verification error: {str(e)}"
            )

    def validate_token_format(self, token: str) -> bool:
        """
        Validate token format (basic JWT structure check)
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False

            # Try to decode header and payload
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '==').decode('utf-8'))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==').decode('utf-8'))

            # Check for required claims
            return bool(header.get('alg') and payload.get('sub') and payload.get('aud') and payload.get('exp'))
        except Exception:
            return False

    def _create_error(
        self, 
        message: str, 
        code: str, 
        status_code: Optional[int] = None, 
        details: Optional[Dict[str, Any]] = None
    ) -> SDKError:
        """Create a custom error"""
        return SDKError(message, code, status_code, details)

