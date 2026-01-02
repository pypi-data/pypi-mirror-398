"""
Cross-App Access Client

Implements Identity Assertion Authorization Grant (ID-JAG) for secure cross-application access
"""

import json
import base64
import time
import uuid
from typing import Dict, Any, Optional, Literal

import requests
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKError
from cryptography.hazmat.backends import default_backend

from ..types import (
    OktaAIConfig,
    IdJagTokenRequest,
    IdJagTokenResponse,
    IdJagTokenVerificationOptions,
    IdJagTokenVerificationResult,
    AuthServerTokenRequest,
    AuthServerTokenResponse,
    AuthServerTokenVerificationOptions,
    AuthServerTokenVerificationResult,
    SDKError,
)


class CrossAppAccessClient:
    """Cross-App Access Client for Identity Assertion Authorization Grant (ID-JAG)"""

    def __init__(self, config: OktaAIConfig):
        """Initialize the Cross-App Access Client"""
        self.config = config
        self.session = requests.Session()
        self.session.timeout = config.timeout / 1000 if config.timeout else 30  # Convert ms to seconds

    def _generate_jwt_assertion(
        self,
        principal_id: str,
        audience: str,
        private_jwk: Dict[str, Any]
    ) -> str:
        """
        Generate a JWT assertion for client authentication using private JWK
        Based on RFC 7523 (JSON Web Token (JWT) Profile for OAuth 2.0 Client Authentication)
        """
        try:
            # Get current time
            now = int(time.time())
            
            # Prepare header
            header = {
                "kid": private_jwk.get("kid"),
                "alg": "RS256"
            }
            
            # Prepare payload
            payload = {
                "iss": principal_id,
                "aud": audience,
                "sub": principal_id,
                "exp": now + 60,  # Expires in 60 seconds
                "iat": now,
                "jti": str(uuid.uuid4())
            }
            
            # Convert JWK to RSA private key for signing
            from cryptography.hazmat.primitives.asymmetric import rsa
            
            # Helper function to decode base64url to int
            def b64url_to_int(b64url_str: str) -> int:
                """Convert base64url string to integer"""
                # Add padding if needed
                padding = 4 - len(b64url_str) % 4
                if padding != 4:
                    b64url_str += '=' * padding
                # Replace URL-safe characters
                b64_str = b64url_str.replace('-', '+').replace('_', '/')
                decoded = base64.b64decode(b64_str)
                return int.from_bytes(decoded, byteorder='big')
            
            # Extract and decode key components from JWK
            n_int = b64url_to_int(private_jwk["n"])
            e_int = b64url_to_int(private_jwk["e"])
            d_int = b64url_to_int(private_jwk["d"])
            
            # Build RSA private key numbers
            # For RSA private keys, we need p, q, dp, dq, qi if available for efficiency
            # But we can also construct from just n, e, d (though less efficient)
            if "p" in private_jwk and "q" in private_jwk:
                # Use CRT parameters for efficiency
                p_int = b64url_to_int(private_jwk["p"])
                q_int = b64url_to_int(private_jwk["q"])
                dp_int = b64url_to_int(private_jwk.get("dp", "")) if "dp" in private_jwk else None
                dq_int = b64url_to_int(private_jwk.get("dq", "")) if "dq" in private_jwk else None
                qi_int = b64url_to_int(private_jwk.get("qi", "")) if "qi" in private_jwk else None
                
                private_numbers = rsa.RSAPrivateNumbers(
                    p=p_int,
                    q=q_int,
                    d=d_int,
                    dmp1=dp_int,
                    dmq1=dq_int,
                    iqmp=qi_int,
                    public_numbers=rsa.RSAPublicNumbers(e_int, n_int)
                )
            else:
                # Fallback: construct from n, e, d only (less efficient but works)
                # This requires computing p and q from n, which is expensive
                # For now, raise an error if CRT parameters are missing
                raise ValueError(
                    "JWK must include 'p' and 'q' parameters for RSA private key. "
                    "Full private key components are required."
                )
            
            private_key = private_numbers.private_key(backend=default_backend())
            
            # Encode JWT
            assertion = jwt.encode(
                payload,
                private_key,
                algorithm="RS256",
                headers=header
            )
            
            return assertion
            
        except KeyError as e:
            raise self._create_error(
                f"Missing required JWK parameter: {str(e)}",
                'INVALID_JWK_FORMAT'
            )
        except Exception as e:
            raise self._create_error(
                f"Failed to generate JWT assertion: {str(e)}",
                'JWT_ASSERTION_GENERATION_FAILED'
            )

    def _exchange_token_for_id_jag_internal(self, request: IdJagTokenRequest) -> IdJagTokenResponse:
        """
        Internal method: Exchange an Okta ID token or access token for an ID-JAG token
        Based on RFC 8693 (OAuth 2.0 Token Exchange) with ID-JAG extension
        """
        try:
            token_type_label = "ID token" if request.subject_token_type == "urn:ietf:params:oauth:token-type:id_token" else "access token"
            print(f" Exchanging {token_type_label} for ID-JAG token...")
            print(f" Audience: {request.audience}")

            # Prepare the token exchange request - Cross App Access uses org auth server
            token_exchange_url = f"{self.config.okta_domain}/oauth2/v1/token"
            
            form_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
                'requested_token_type': 'urn:ietf:params:oauth:token-type:id-jag',
                'subject_token': request.subject_token,
                'subject_token_type': request.subject_token_type,
                'audience': request.audience,
            }
            
            # Add scope if provided
            if request.scope:
                form_data['scope'] = request.scope
            
            # Determine authentication method
            # Priority: Use JWT bearer assertion if principal_id and private_jwk are provided
            # Otherwise, fall back to client_id/client_secret
            principal_id = request.principal_id or self.config.principal_id
            private_jwk = request.private_jwk or self.config.private_jwk
            
            if principal_id and private_jwk:
                # Use JWT bearer assertion
                print(" Using JWT bearer assertion for client authentication")
                assertion_audience = f"{self.config.okta_domain}/oauth2/v1/token"
                client_assertion = self._generate_jwt_assertion(
                    principal_id=principal_id,
                    audience=assertion_audience,
                    private_jwk=private_jwk
                )
                form_data['client_assertion_type'] = 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
                form_data['client_assertion'] = client_assertion
            elif request.client_id and request.client_secret:
                # Use client_id/client_secret
                print(f" Using client_id/client_secret for authentication")
                form_data['client_id'] = request.client_id
                form_data['client_secret'] = request.client_secret
            elif self.config.client_id and self.config.client_secret:
                # Use config client credentials
                print(f" Using config client_id/client_secret for authentication")
                form_data['client_id'] = self.config.client_id
                form_data['client_secret'] = self.config.client_secret
            else:
                raise self._create_error(
                    'Either (principal_id and private_jwk) or (client_id and client_secret) must be provided',
                    'MISSING_AUTH_CREDENTIALS'
                )

            print(f" Making ID-JAG token exchange request to: {token_exchange_url}")

            response = self.session.post(
                token_exchange_url,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            response.raise_for_status()
            response_data = response.json()

            print(" ID-JAG token exchange successful")
            print(f" Issued token type: {response_data.get('issued_token_type')}")
            print(f" Expires in: {response_data.get('expires_in', 'N/A')} seconds")

            return IdJagTokenResponse(**response_data)

        except requests.exceptions.RequestException as e:
            print(f" ID-JAG token exchange failed: {e}")
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    raise self._create_error(
                        f"ID-JAG token exchange failed: {error_message}",
                        'ID_JAG_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code,
                        error_data
                    )
                except (ValueError, KeyError):
                    raise self._create_error(
                        f"ID-JAG token exchange failed: {e.response.text}",
                        'ID_JAG_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code
                    )
            
            raise self._create_error(
                f"ID-JAG token exchange failed: {str(e)}",
                'ID_JAG_TOKEN_EXCHANGE_ERROR'
            )

    def verify_id_jag_token(
        self, 
        token: str, 
        audience: str
    ) -> IdJagTokenVerificationResult:
        """
        STEP 2: Verify ID-JAG token
        
        Verifies the ID-JAG token using the issuer's public keys
        """
        try:
            issuer = self.config.okta_domain
            
            print(" Verifying ID-JAG token...")
            print(f" Expected Issuer: {issuer}")
            print(f" Expected Audience: {audience}")

            # Determine JWKS URI
            jwks_uri = f"{issuer}/oauth2/v1/keys"
            print(f" JWKS URI: {jwks_uri}")

            # Create JWK client
            jwks_client = PyJWKClient(jwks_uri)

            # Ensure token is bytes (some versions of PyJWT require this)
            token_bytes = token.encode('utf-8') if isinstance(token, str) else token

            # Get the signing key
            signing_key = jwks_client.get_signing_key_from_jwt(token_bytes)

            # Verify the token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=audience,
                issuer=issuer,
                options={"verify_exp": True, "verify_aud": True, "verify_iss": True}
            )

            print(" ID-JAG token verified successfully")
            print(f" Subject: {payload.get('sub')}")
            print(f" Email: {payload.get('email', 'N/A')}")
            print(f" Audience: {payload.get('aud')}")
            print(f" Issuer: {payload.get('iss')}")
            print(f" Expires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload.get('exp', 0)))}")

            return IdJagTokenVerificationResult(
                valid=True,
                payload=payload,
                sub=payload.get('sub'),
                email=payload.get('email'),
                aud=payload.get('aud'),
                iss=payload.get('iss'),
                exp=payload.get('exp')
            )

        except (InvalidTokenError, PyJWKError) as e:
            print(f" ID-JAG token verification failed: {e}")
            return IdJagTokenVerificationResult(
                valid=False,
                error=str(e)
            )
        except Exception as e:
            print(f" ID-JAG token verification failed: {e}")
            return IdJagTokenVerificationResult(
                valid=False,
                error=f"Unknown verification error: {str(e)}"
            )

    def exchange_token(
        self, 
        token: str, 
        audience: str, 
        scope: Optional[str] = None,
        token_type: Literal["id_token", "access_token"] = "id_token"
    ) -> IdJagTokenResponse:
        """
        STEP 1: Exchange ID token or access token for ID-JAG token
        
        Uses SDK configuration for authentication (principal_id/private_jwk or client_id/client_secret)
        
        Args:
            token: The ID token or access token to exchange
            audience: Target audience for the ID-JAG token
            scope: Optional scope for the ID-JAG token
            token_type: Type of token - "id_token" (default) or "access_token"
                        The value is converted to the appropriate URN format internally
        """
        # Convert token_type parameter to subject_token_type URN format
        token_type_urn_map = {
            "id_token": "urn:ietf:params:oauth:token-type:id_token",
            "access_token": "urn:ietf:params:oauth:token-type:access_token"
        }
        subject_token_type = token_type_urn_map.get(token_type, "urn:ietf:params:oauth:token-type:id_token")
        
        # Determine which authentication method to use
        if self.config.principal_id and self.config.private_jwk:
            # Use JWT bearer assertion
            request = IdJagTokenRequest(
                subject_token=token,
                subject_token_type=subject_token_type,
                audience=audience,
                scope=scope,
                principal_id=self.config.principal_id,
                private_jwk=self.config.private_jwk
            )
        elif self.config.client_id and self.config.client_secret:
            # Use client_id/client_secret
            request = IdJagTokenRequest(
                subject_token=token,
                subject_token_type=subject_token_type,
                audience=audience,
                scope=scope,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret
            )
        else:
            raise self._create_error(
                'Either (principal_id and private_jwk) or (client_id and client_secret) must be configured',
                'MISSING_AUTH_CREDENTIALS'
            )

        return self._exchange_token_for_id_jag_internal(request)

    def exchange_id_jag_for_auth_server_token(
        self, 
        request: AuthServerTokenRequest
    ) -> AuthServerTokenResponse:
        """
        STEP 3: Exchange ID-JAG token for authorization server access token
        
        Uses JWT Bearer grant type (RFC 7523) with custom authorization server
        """
        try:
            print(" Exchanging ID-JAG token for authorization server token...")
            print(f" Authorization Server ID: {request.authorization_server_id}")

            # Prepare the authorization server token request
            auth_server_token_url = f"{self.config.okta_domain}/oauth2/{request.authorization_server_id}/v1/token"
            
            form_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': request.id_jag_token,
            }
            
            # Determine authentication method
            # Use JWT bearer assertion for client authentication
            principal_id = request.principal_id or self.config.principal_id
            private_jwk = request.private_jwk or self.config.private_jwk
            
            if principal_id and private_jwk:
                # Use JWT bearer assertion
                print(" Using JWT bearer assertion for client authentication")
                assertion_audience = f"{self.config.okta_domain}/oauth2/{request.authorization_server_id}/v1/token"
                client_assertion = self._generate_jwt_assertion(
                    principal_id=principal_id,
                    audience=assertion_audience,
                    private_jwk=private_jwk
                )
                form_data['client_assertion_type'] = 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
                form_data['client_assertion'] = client_assertion
            else:
                raise self._create_error(
                    'principal_id and private_jwk are required for authorization server token exchange',
                    'MISSING_AUTH_CREDENTIALS'
                )

            print(f" Making authorization server token request to: {auth_server_token_url}")

            response = self.session.post(
                auth_server_token_url,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            response.raise_for_status()
            response_data = response.json()

            print(" Authorization server token exchange successful")
            print(f" Expires in: {response_data.get('expires_in', 'N/A')} seconds")
            if response_data.get('scope'):
                print(f" Scope: {response_data.get('scope')}")

            return AuthServerTokenResponse(**response_data)

        except requests.exceptions.RequestException as e:
            print(f" Authorization server token exchange failed: {e}")
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    raise self._create_error(
                        f"Authorization server token exchange failed: {error_message}",
                        'AUTH_SERVER_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code,
                        error_data
                    )
                except (ValueError, KeyError):
                    raise self._create_error(
                        f"Authorization server token exchange failed: {e.response.text}",
                        'AUTH_SERVER_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code
                    )
            
            raise self._create_error(
                f"Authorization server token exchange failed: {str(e)}",
                'AUTH_SERVER_TOKEN_EXCHANGE_ERROR'
            )

    def verify_auth_server_token(
        self,
        token: str,
        authorization_server_id: str,
        audience: str
    ) -> AuthServerTokenVerificationResult:
        """
        STEP 4: Verify authorization server token
        
        Verifies the authorization server token using the issuer's public keys
        """
        try:
            issuer = f"{self.config.okta_domain}/oauth2/{authorization_server_id}"
            jwks_uri = f"{issuer}/v1/keys"
            
            print(" Verifying authorization server token...")
            print(f" Expected Issuer: {issuer}")
            print(f" Expected Audience: {audience}")
            print(f" JWKS URI: {jwks_uri}")

            # Create JWK client
            jwks_client = PyJWKClient(jwks_uri)

            # Ensure token is bytes (some versions of PyJWT require this)
            token_bytes = token.encode('utf-8') if isinstance(token, str) else token

            # Get the signing key
            signing_key = jwks_client.get_signing_key_from_jwt(token_bytes)

            # Verify the token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=audience,
                issuer=issuer,
                options={"verify_exp": True, "verify_aud": True, "verify_iss": True}
            )

            # Extract scope from token - Okta uses 'scp' claim as array
            token_scp = payload.get('scp', [])
            token_scope = payload.get('scope')  # Fallback to 'scope' if present
            
            # Ensure token_scp is a list
            if not isinstance(token_scp, list):
                token_scp = [str(token_scp)] if token_scp else []
            
            # Use scp if available, otherwise fallback to scope
            scope_value = ' '.join(token_scp) if token_scp else token_scope

            print(" Authorization server token verified successfully")
            print(f" Subject: {payload.get('sub')}")
            print(f" Email: {payload.get('email', 'N/A')}")
            print(f" Audience: {payload.get('aud')}")
            print(f" Issuer: {payload.get('iss')}")
            if scope_value:
                print(f" Scope: {scope_value}")
            print(f" Expires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload.get('exp', 0)))}")

            return AuthServerTokenVerificationResult(
                valid=True,
                payload=payload,
                sub=payload.get('sub'),
                email=payload.get('email'),
                aud=payload.get('aud'),
                iss=payload.get('iss'),
                exp=payload.get('exp'),
                scope=scope_value
            )

        except (InvalidTokenError, PyJWKError) as e:
            print(f" Authorization server token verification failed: {e}")
            return AuthServerTokenVerificationResult(
                valid=False,
                error=str(e)
            )
        except Exception as e:
            print(f" Authorization server token verification failed: {e}")
            return AuthServerTokenVerificationResult(
                valid=False,
                error=f"Unknown verification error: {str(e)}"
            )

    def _create_error(
        self, 
        message: str, 
        code: str, 
        status_code: Optional[int] = None, 
        details: Optional[Dict[str, Any]] = None
    ) -> SDKError:
        """Create a custom error"""
        return SDKError(message, code, status_code, details)

