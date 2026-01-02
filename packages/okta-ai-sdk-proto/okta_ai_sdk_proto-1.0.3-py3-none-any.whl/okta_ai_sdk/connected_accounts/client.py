"""
Connected Accounts Client

Implements external token exchange and connected account flows
for multi-provider authentication scenarios.
"""

from typing import Optional, Dict, Any
from urllib.parse import urlencode, urlparse, parse_qs

import requests

from ..types import SDKError
from .types import (
    ExternalTokenExchangeRequest,
    ExternalTokenExchangeResponse,
    FederatedTokenExchangeRequest,
    FederatedTokenExchangeResponse,
    ConnectedAccountInitiateRequest,
    ConnectedAccountInitiateResponse,
    ConnectedAccountCompleteRequest,
    ConnectedAccountCompleteResponse,
    GetExternalProviderTokenRequest,
    GetExternalProviderTokenResponse,
    CompleteLinkingAndGetTokenRequest,
    CompleteLinkingAndGetTokenResponse,
)


class ConnectedAccountsClient:
    """Client for connected account flows and external token exchanges"""

    def __init__(self, timeout: Optional[int] = 30):
        """
        Initialize the Connected Accounts Client
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.session = requests.Session()
        self.session.timeout = timeout

    def get_external_provider_token_from_vault(
        self,
        request: GetExternalProviderTokenRequest
    ) -> GetExternalProviderTokenResponse:
        """
        Get external provider token (happy path: tries vault first, initiates linking if needed)
        
        This method implements the complete flow:
        1. Exchanges Okta access token for Auth0 vault token
        2. Tries to get federated provider token from vault (happy path)
        3. If token not in vault, initiates account linking and returns authorization URL
        
        Args:
            request: Request with Okta token and Auth0 configuration
            
        Returns:
            GetExternalProviderTokenResponse with either:
            - token (if found in vault) and requires_linking=False
            - authorization_url and auth_session (if linking needed) and requires_linking=True
        """
        try:
            print(" Getting external provider token...")
            print(f" Connection: {request.connection}")
            
            # Step 5: Exchange Okta token for Auth0 vault token
            print(" Step 1: Exchanging Okta token for Auth0 vault token...")
            vault_token_request = ExternalTokenExchangeRequest(
                subject_token=request.okta_access_token,
                subject_token_type=request.auth0_config.vault_token_type,
                audience=request.auth0_config.vault_audience,
                scope=request.auth0_config.vault_scope,
                token_endpoint=request.auth0_config.token_endpoint,
                client_id=request.auth0_config.vault_client_id,
                client_secret=request.auth0_config.vault_client_secret,
                requested_token_type=None  # Don't specify requested_token_type for custom token types
            )
            
            vault_token_response = self._exchange_with_external_provider(vault_token_request)
            auth0_vault_token = vault_token_response.access_token
            
            # Step 6: Try to get federated token from vault (happy path)
            print(" Step 2: Attempting to get federated token from vault...")
            try:
                federated_request = FederatedTokenExchangeRequest(
                    subject_token=auth0_vault_token,
                    connection=request.connection,
                    scopes=request.auth0_config.vault_scope,
                    token_endpoint=request.auth0_config.token_endpoint,
                    client_id=request.auth0_config.vault_client_id,
                    client_secret=request.auth0_config.vault_client_secret
                )
                
                federated_response = self._exchange_for_federated_token(federated_request)
                
                # Happy path: token found in vault
                print(" Token found in vault (happy path)")
                return GetExternalProviderTokenResponse(
                    token=federated_response.access_token,
                    token_type=federated_response.token_type,
                    expires_in=federated_response.expires_in,
                    scope=federated_response.scope,
                    requires_linking=False,
                    authorization_url=None,
                    auth_session=None
                )
                
            except SDKError as e:
                # Token not in vault - need to initiate account linking
                # Any failure in federated token exchange likely means account not linked
                print(f" Federated token exchange failed: {e.message}")
                print(" Token not found in vault - initiating account linking...")
                
                # Step 7: Get MyAccount token
                print(" Step 3: Getting MyAccount token...")
                myaccount_token_request = ExternalTokenExchangeRequest(
                    subject_token=request.okta_access_token,
                    subject_token_type=request.auth0_config.vault_token_type,
                    audience=request.auth0_config.myaccount_audience,
                    scope="create:me:connected_accounts",
                    token_endpoint=request.auth0_config.token_endpoint,
                    client_id=request.auth0_config.myaccount_client_id,
                    client_secret=request.auth0_config.myaccount_client_secret,
                    requested_token_type=None  # Don't specify requested_token_type for custom token types
                )
                
                myaccount_token_response = self._exchange_with_external_provider(myaccount_token_request)
                myaccount_token = myaccount_token_response.access_token
                
                # Step 8: Initiate account linking
                print(" Step 4: Initiating account linking...")
                link_request = ConnectedAccountInitiateRequest(
                    connection=request.connection,
                    redirect_uri=request.redirect_uri,
                    state=request.state,
                    authorization_params=request.authorization_params
                )
                
                link_response = self._initiate_account_linking(
                    myaccount_token=myaccount_token,
                    request=link_request,
                    myaccount_endpoint=request.auth0_config.myaccount_connect_endpoint
                )
                
                return GetExternalProviderTokenResponse(
                    token=None,
                    token_type=None,
                    expires_in=None,
                    scope=None,
                    requires_linking=True,
                    authorization_url=link_response.authorization_url,
                    auth_session=link_response.auth_session
                )
        
        except Exception as e:
            print(f" Get external provider token failed: {e}")
            raise self._create_error(
                f"Get external provider token failed: {str(e)}",
                'GET_EXTERNAL_PROVIDER_TOKEN_FAILED'
            )

    def complete_linking_and_get_token_from_vault(
        self,
        request: CompleteLinkingAndGetTokenRequest
    ) -> CompleteLinkingAndGetTokenResponse:
        """
        Complete account linking and get external provider token
        
        This method:
        1. Completes account linking with authorization code
        2. Exchanges Okta token for fresh Auth0 vault token
        3. Gets federated provider token (should work now)
        
        Args:
            request: Request with auth session, connect code, and configuration
            
        Returns:
            CompleteLinkingAndGetTokenResponse with the external provider token
        """
        try:
            print(" Completing account linking and getting token...")
            print(f" Connection: {request.connection}")
            
            # Step 9: Complete account linking
            print(" Step 1: Completing account linking...")
            
            # First, get MyAccount token
            myaccount_token_request = ExternalTokenExchangeRequest(
                subject_token=request.okta_access_token,
                subject_token_type=request.auth0_config.vault_token_type,
                audience=request.auth0_config.myaccount_audience,
                scope="create:me:connected_accounts",
                token_endpoint=request.auth0_config.token_endpoint,
                client_id=request.auth0_config.myaccount_client_id,
                client_secret=request.auth0_config.myaccount_client_secret,
                requested_token_type=None  # Don't specify requested_token_type for custom token types
            )
            
            myaccount_token_response = self._exchange_with_external_provider(myaccount_token_request)
            myaccount_token = myaccount_token_response.access_token
            
            # Complete the linking
            complete_request = ConnectedAccountCompleteRequest(
                auth_session=request.auth_session,
                connect_code=request.connect_code,
                redirect_uri=request.redirect_uri,
                code_verifier=request.code_verifier
            )
            
            complete_response = self._complete_account_linking(
                myaccount_token=myaccount_token,
                request=complete_request,
                myaccount_endpoint=request.auth0_config.myaccount_complete_endpoint
            )
            
            if not complete_response.success:
                raise self._create_error(
                    "Account linking completion failed",
                    'ACCOUNT_LINKING_COMPLETION_FAILED'
                )
            
            print(" Account linking completed successfully")
            
            # Step 5 (fresh): Exchange Okta token for Auth0 vault token
            print(" Step 2: Exchanging Okta token for fresh Auth0 vault token...")
            vault_token_request = ExternalTokenExchangeRequest(
                subject_token=request.okta_access_token,
                subject_token_type=request.auth0_config.vault_token_type,
                audience=request.auth0_config.vault_audience,
                scope=request.auth0_config.vault_scope,
                token_endpoint=request.auth0_config.token_endpoint,
                client_id=request.auth0_config.vault_client_id,
                client_secret=request.auth0_config.vault_client_secret,
                requested_token_type=None  # Don't specify requested_token_type for custom token types
            )
            
            vault_token_response = self._exchange_with_external_provider(vault_token_request)
            auth0_vault_token = vault_token_response.access_token
            
            # Step 10: Get federated token (should work now)
            print(" Step 3: Getting federated provider token...")
            federated_request = FederatedTokenExchangeRequest(
                subject_token=auth0_vault_token,
                connection=request.connection,
                scopes=request.auth0_config.vault_scope,
                token_endpoint=request.auth0_config.token_endpoint,
                client_id=request.auth0_config.vault_client_id,
                client_secret=request.auth0_config.vault_client_secret
            )
            
            federated_response = self._exchange_for_federated_token(federated_request)
            
            return CompleteLinkingAndGetTokenResponse(
                token=federated_response.access_token,
                token_type=federated_response.token_type,
                expires_in=federated_response.expires_in,
                scope=federated_response.scope,
                connection_id=complete_response.connection_id,
                user_id=complete_response.user_id
            )
        
        except Exception as e:
            print(f" Complete linking and get token failed: {e}")
            raise self._create_error(
                f"Complete linking and get token failed: {str(e)}",
                'COMPLETE_LINKING_AND_GET_TOKEN_FAILED'
            )

    def _exchange_with_external_provider(
        self,
        request: ExternalTokenExchangeRequest
    ) -> ExternalTokenExchangeResponse:
        """
        Internal method: Exchange token with external provider (e.g., Auth0)
        
        Supports custom token types and external endpoints. This is useful for
        exchanging Okta tokens for tokens from other OAuth providers.
        
        Args:
            request: External token exchange request with provider details
            
        Returns:
            ExternalTokenExchangeResponse with the exchanged token
        """
        try:
            print(" Exchanging token with external provider...")
            print(f" Token Endpoint: {request.token_endpoint}")
            print(f" Audience: {request.audience}")
            print(f" Subject Token Type: {request.subject_token_type}")

            # Prepare form data
            form_data = {
                'grant_type': request.grant_type,
                'subject_token': request.subject_token,
                'subject_token_type': request.subject_token_type,
                'audience': request.audience,
                'client_id': request.client_id,
                'client_secret': request.client_secret,
            }

            if request.scope:
                form_data['scope'] = request.scope

            if request.requested_token_type:
                form_data['requested_token_type'] = request.requested_token_type

            # Add any additional parameters
            if request.additional_params:
                form_data.update(request.additional_params)

            print(f" Making token exchange request to: {request.token_endpoint}")

            response = self.session.post(
                request.token_endpoint,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            response.raise_for_status()
            response_data = response.json()

            print(" External token exchange successful")
            print(f" Issued token type: {response_data.get('issued_token_type', 'N/A')}")
            print(f" Expires in: {response_data.get('expires_in', 'N/A')} seconds")

            return ExternalTokenExchangeResponse(**response_data)

        except requests.exceptions.RequestException as e:
            print(f" External token exchange failed: {e}")

            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    raise self._create_error(
                        f"External token exchange failed: {error_message}",
                        'EXTERNAL_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code,
                        error_data
                    )
                except (ValueError, KeyError):
                    raise self._create_error(
                        f"External token exchange failed: {e.response.text}",
                        'EXTERNAL_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code
                    )
            else:
                raise self._create_error(
                    f"External token exchange failed: {str(e)}",
                    'EXTERNAL_TOKEN_EXCHANGE_FAILED'
                )

    def _exchange_for_federated_token(
        self,
        request: FederatedTokenExchangeRequest
    ) -> FederatedTokenExchangeResponse:
        """
        Internal method: Exchange token for federated provider token (Google, GitHub, etc.)
        
        Uses Auth0's federated connection token exchange grant type to obtain
        tokens from external identity providers that have been linked to the user's account.
        
        Args:
            request: Federated token exchange request with connection details
            
        Returns:
            FederatedTokenExchangeResponse with the federated provider token
        """
        try:
            print(" Exchanging for federated connection token...")
            print(f" Connection: {request.connection}")
            print(f" Token Endpoint: {request.token_endpoint}")

            # Prepare form data
            form_data = {
                'grant_type': request.grant_type,
                'subject_token': request.subject_token,
                'subject_token_type': request.subject_token_type,
                'connection': request.connection,
                'client_id': request.client_id,
                'client_secret': request.client_secret,
                'requested_token_type': request.requested_token_type,
            }

            if request.scopes:
                form_data['scopes'] = request.scopes

            print(f" Making federated token exchange request to: {request.token_endpoint}")

            response = self.session.post(
                request.token_endpoint,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            response.raise_for_status()
            response_data = response.json()

            print(" Federated token exchange successful")
            print(f" Token type: {response_data.get('token_type', 'N/A')}")
            print(f" Expires in: {response_data.get('expires_in', 'N/A')} seconds")

            return FederatedTokenExchangeResponse(**response_data)

        except requests.exceptions.RequestException as e:
            print(f" Federated token exchange failed: {e}")

            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    raise self._create_error(
                        f"Federated token exchange failed: {error_message}",
                        'FEDERATED_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code,
                        error_data
                    )
                except (ValueError, KeyError):
                    raise self._create_error(
                        f"Federated token exchange failed: {e.response.text}",
                        'FEDERATED_TOKEN_EXCHANGE_FAILED',
                        e.response.status_code
                    )
            else:
                raise self._create_error(
                    f"Federated token exchange failed: {str(e)}",
                    'FEDERATED_TOKEN_EXCHANGE_FAILED'
                )

    def _initiate_account_linking(
        self,
        myaccount_token: str,
        request: ConnectedAccountInitiateRequest,
        myaccount_endpoint: str
    ) -> ConnectedAccountInitiateResponse:
        """
        Internal method: Initiate connected account linking
        
        Starts the process of linking a user's account with an external identity provider
        (e.g., Google, GitHub). Returns an authorization URL that the user must visit
        to grant consent.
        
        Args:
            myaccount_token: Access token for the MyAccount API (with create:me:connected_accounts scope)
            request: Account linking initiation request
            myaccount_endpoint: MyAccount API endpoint URL (e.g., Auth0 MyAccount /connect endpoint)
            
        Returns:
            ConnectedAccountInitiateResponse with authorization URL and session info
        """
        try:
            print(" Initiating account linking...")
            print(f" Connection: {request.connection}")
            print(f" MyAccount Endpoint: {myaccount_endpoint}")

            # Prepare request body
            request_body = {
                'connection': request.connection,
                'redirect_uri': request.redirect_uri,
                'authorization_params': request.authorization_params or {}  # Always include, even if empty
            }

            if request.state:
                request_body['state'] = request.state

            if request.code_challenge:
                request_body['code_challenge'] = request.code_challenge

            if request.code_challenge_method:
                request_body['code_challenge_method'] = request.code_challenge_method

            print(f" Making account linking initiation request to: {myaccount_endpoint}")

            response = self.session.post(
                myaccount_endpoint,
                json=request_body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {myaccount_token}'
                }
            )

            # Auth0 MyAccount API returns 201 for successful account linking initiation
            if response.status_code not in [200, 201]:
                response.raise_for_status()
            
            response_data = response.json()

            print(" Account linking initiation successful")

            # Extract response fields
            auth_session = response_data.get('auth_session')
            connect_uri = response_data.get('connect_uri')
            connect_params = response_data.get('connect_params', {})

            # Build full authorization URL
            ticket = connect_params.get('ticket', '')
            if ticket:
                authorization_url = f"{connect_uri}?ticket={ticket}"
            else:
                # Fallback: build URL from connect_uri and connect_params
                parsed_uri = urlparse(connect_uri)
                query_params = parse_qs(parsed_uri.query)
                query_params.update(connect_params)
                query_string = urlencode(query_params, doseq=True)
                authorization_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}{parsed_uri.path}?{query_string}"

            return ConnectedAccountInitiateResponse(
                auth_session=auth_session,
                connect_uri=connect_uri,
                connect_params=connect_params,
                authorization_url=authorization_url
            )

        except requests.exceptions.RequestException as e:
            print(f" Account linking initiation failed: {e}")

            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    # Try multiple possible error message fields
                    error_message = (
                        error_data.get('detail') or  # Auth0 API errors use 'detail'
                        error_data.get('error_description') or
                        error_data.get('error') or
                        error_data.get('message') or
                        error_data.get('title') or
                        str(error_data)
                    )
                    print(f" Error response: {error_data}")
                    raise self._create_error(
                        f"Account linking initiation failed: {error_message}",
                        'ACCOUNT_LINKING_INITIATION_FAILED',
                        e.response.status_code,
                        error_data
                    )
                except (ValueError, KeyError, AttributeError):
                    error_text = e.response.text if hasattr(e.response, 'text') else str(e.response)
                    print(f" Error response text: {error_text}")
                    raise self._create_error(
                        f"Account linking initiation failed: {error_text}",
                        'ACCOUNT_LINKING_INITIATION_FAILED',
                        e.response.status_code
                    )
            else:
                raise self._create_error(
                    f"Account linking initiation failed: {str(e)}",
                    'ACCOUNT_LINKING_INITIATION_FAILED'
                )

    def _complete_account_linking(
        self,
        myaccount_token: str,
        request: ConnectedAccountCompleteRequest,
        myaccount_endpoint: str
    ) -> ConnectedAccountCompleteResponse:
        """
        Internal method: Complete account linking with authorization code
        
        Finishes the account linking process using the authorization code received
        from the provider's callback after user consent.
        
        Args:
            myaccount_token: Access token for the MyAccount API (with create:me:connected_accounts scope)
            request: Account linking completion request with auth session and code
            myaccount_endpoint: MyAccount API endpoint URL (e.g., Auth0 MyAccount /complete endpoint)
            
        Returns:
            ConnectedAccountCompleteResponse with linking result
        """
        try:
            print(" Completing account linking...")
            print(f" MyAccount Endpoint: {myaccount_endpoint}")

            # Prepare request body
            request_body = {
                'auth_session': request.auth_session,
                'connect_code': request.connect_code,
                'redirect_uri': request.redirect_uri,
            }

            if request.code_verifier:
                request_body['code_verifier'] = request.code_verifier

            print(f" Making account linking completion request to: {myaccount_endpoint}")

            response = self.session.post(
                myaccount_endpoint,
                json=request_body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {myaccount_token}'
                }
            )

            response.raise_for_status()
            response_data = response.json()

            print(" Account linking completion successful")

            # Extract response fields (structure may vary by provider)
            return ConnectedAccountCompleteResponse(
                success=True,
                connection_id=response_data.get('connection_id') or response_data.get('id'),
                user_id=response_data.get('user_id') or response_data.get('sub'),
                response_data=response_data
            )

        except requests.exceptions.RequestException as e:
            print(f" Account linking completion failed: {e}")

            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    raise self._create_error(
                        f"Account linking completion failed: {error_message}",
                        'ACCOUNT_LINKING_COMPLETION_FAILED',
                        e.response.status_code,
                        error_data
                    )
                except (ValueError, KeyError):
                    raise self._create_error(
                        f"Account linking completion failed: {e.response.text}",
                        'ACCOUNT_LINKING_COMPLETION_FAILED',
                        e.response.status_code
                    )
            else:
                raise self._create_error(
                    f"Account linking completion failed: {str(e)}",
                    'ACCOUNT_LINKING_COMPLETION_FAILED'
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
