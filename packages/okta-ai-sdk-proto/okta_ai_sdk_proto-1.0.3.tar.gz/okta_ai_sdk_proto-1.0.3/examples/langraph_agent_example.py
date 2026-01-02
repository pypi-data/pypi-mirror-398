#!/usr/bin/env python3
"""
LangGraph Agent Example with Okta AI SDK

This example demonstrates how to use the Okta AI SDK with LangGraph agents
for secure cross-application access and token management.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add the src directory to the path so we can import the SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from okta_ai_sdk import (
    OktaAISDK,
    OktaAIConfig,
    TokenExchangeRequest,
    SDKError,
)


@dataclass
class AgentState:
    """State for the LangGraph agent"""
    user_id: str
    access_token: str
    id_token: str
    messages: List[Dict[str, Any]]
    current_app: Optional[str] = None
    exchanged_tokens: Dict[str, str] = None
    
    def __post_init__(self):
        if self.exchanged_tokens is None:
            self.exchanged_tokens = {}


class OktaSecureAgent:
    """LangGraph agent with Okta security integration"""
    
    def __init__(self, config: OktaAIConfig):
        """Initialize the secure agent"""
        self.sdk = OktaAISDK(config)
        self.config = config
        
    def authenticate_user(self, state: AgentState) -> AgentState:
        """Authenticate user and validate tokens"""
        print(f" Authenticating user: {state.user_id}")
        
        try:
            # Validate token format
            if not self.sdk.token_exchange.validate_token_format(state.access_token):
                raise SDKError("Invalid access token format", "INVALID_TOKEN_FORMAT")
            
            # Verify the access token
            verification_result = self.sdk.token_exchange.verify_token(
                token=state.access_token,
                options={
                    "issuer": self.config.okta_domain,
                    "audience": "api://default"  # Adjust based on your setup
                }
            )
            
            if not verification_result.valid:
                raise SDKError("Token verification failed", "TOKEN_VERIFICATION_FAILED")
            
            print(f" User authenticated: {verification_result.sub}")
            state.messages.append({
                "role": "system",
                "content": f"User {verification_result.sub} authenticated successfully"
            })
            
        except Exception as e:
            print(f" Authentication failed: {e}")
            state.messages.append({
                "role": "system",
                "content": f"Authentication failed: {str(e)}"
            })
        
        return state
    
    def exchange_token_for_app(self, state: AgentState, app_audience: str) -> AgentState:
        """Exchange token for specific application access"""
        print(f" Exchanging token for app: {app_audience}")
        
        try:
            # Check if we already have a token for this app
            if app_audience in state.exchanged_tokens:
                print(f" Using cached token for {app_audience}")
                return state
            
            # Create token exchange request
            token_request = TokenExchangeRequest(
                subject_token=state.access_token,
                subject_token_type="urn:ietf:params:oauth:token-type:access_token",
                audience=app_audience,
                scope="read write"
            )
            
            # Exchange the token
            result = self.sdk.token_exchange.exchange_token(token_request)
            
            # Cache the exchanged token
            state.exchanged_tokens[app_audience] = result.access_token
            state.current_app = app_audience
            
            print(f" Token exchanged for {app_audience}")
            state.messages.append({
                "role": "system",
                "content": f"Token exchanged for application: {app_audience}"
            })
            
        except Exception as e:
            print(f" Token exchange failed: {e}")
            state.messages.append({
                "role": "system",
                "content": f"Token exchange failed: {str(e)}"
            })
        
        return state
    
    def get_cross_app_token(self, state: AgentState, target_app: str) -> AgentState:
        """Get ID-JAG token for cross-application access"""
        print(f" Getting cross-app token for: {target_app}")
        
        try:
            # Exchange ID token for ID-JAG token
            id_jag_result = self.sdk.cross_app_access.exchange_token(
                token=state.id_token,
                audience=target_app
            )
            
            # Cache the ID-JAG token
            state.exchanged_tokens[f"id-jag:{target_app}"] = id_jag_result.access_token
            
            print(f" ID-JAG token obtained for {target_app}")
            state.messages.append({
                "role": "system",
                "content": f"Cross-app access token obtained for: {target_app}"
            })
            
        except Exception as e:
            print(f" Cross-app token exchange failed: {e}")
            state.messages.append({
                "role": "system",
                "content": f"Cross-app token exchange failed: {str(e)}"
            })
        
        return state
    
    def process_user_message(self, state: AgentState, message: str) -> AgentState:
        """Process user message and determine required app access"""
        print(f"💬 Processing message: {message}")
        
        # Add user message to state
        state.messages.append({
            "role": "user",
            "content": message
        })
        
        # Simple logic to determine which app to access based on message content
        if "document" in message.lower():
            # Need access to document service
            state = self.exchange_token_for_app(state, "https://document-service.example.com")
        elif "user" in message.lower() or "profile" in message.lower():
            # Need access to user service
            state = self.exchange_token_for_app(state, "https://user-service.example.com")
        elif "cross-app" in message.lower():
            # Need cross-app access
            state = self.get_cross_app_token(state, "http://localhost:5001")
        
        # Generate response (in a real implementation, this would call your LLM)
        response = f"I understand you want to: {message}. I have the necessary tokens to access the required services."
        
        state.messages.append({
            "role": "assistant",
            "content": response
        })
        
        return state
    
    def get_available_tokens(self, state: AgentState) -> Dict[str, str]:
        """Get all available tokens for the current session"""
        return {
            "access_token": state.access_token,
            "id_token": state.id_token,
            "exchanged_tokens": state.exchanged_tokens,
            "current_app": state.current_app
        }


def main():
    """Main example function"""
    
    # Configuration - replace with your actual values
    config = OktaAIConfig(
        okta_domain="https://your-domain.okta.com",
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        authorization_server_id="default"
    )
    
    # Initialize the secure agent
    agent = OktaSecureAgent(config)
    
    print("🤖 Okta Secure LangGraph Agent initialized!")
    print()
    
    # Create initial state
    state = AgentState(
        user_id="user123",
        access_token="YOUR_ACCESS_TOKEN",
        id_token="YOUR_ID_TOKEN",
        messages=[]
    )
    
    # Simulate agent workflow
    print("=== Agent Workflow Simulation ===")
    
    # Step 1: Authenticate user
    state = agent.authenticate_user(state)
    print()
    
    # Step 2: Process user messages
    test_messages = [
        "I need to access my documents",
        "Can you show me my user profile?",
        "I want to use cross-app functionality",
        "What tokens do I have available?"
    ]
    
    for message in test_messages:
        print(f"User: {message}")
        state = agent.process_user_message(state, message)
        print(f"Agent: {state.messages[-1]['content']}")
        print()
    
    # Step 3: Show available tokens
    tokens = agent.get_available_tokens(state)
    print("=== Available Tokens ===")
    for key, value in tokens.items():
        if key in ["access_token", "id_token"]:
            print(f"{key}: {value[:50]}...")
        else:
            print(f"{key}: {value}")
    
    print()
    print("🎉 Agent workflow completed successfully!")


if __name__ == "__main__":
    main()

