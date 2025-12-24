"""OAuth2 authentication helpers for Canvelete SDK."""

import json
import os
import time
import webbrowser
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse
import http.server
import socketserver
import threading

from .exceptions import AuthenticationError


class OAuth2Handler:
    """Handles OAuth2 authentication flow for Canvelete."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback",
        base_url: str = "https://www.canvelete.com",
        scopes: Optional[list] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url.rstrip("/")
        self.scopes = scopes or [
            "openid",
            "profile",
            "email",
            "designs:read",
            "designs:write",
            "templates:read",
            "render:write",
            "apikeys:read",
            "apikeys:write",
        ]
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate the OAuth2 authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
        }
        
        if state:
            params["state"] = state
        
        return f"{self.base_url}/api/auth/oauth2/authorize?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        import requests
        
        token_url = f"{self.base_url}/api/auth/oauth2/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError(
                f"Token exchange failed: {response.text}",
                status_code=response.status_code,
            )
        
        token_data = response.json()
        
        # Store tokens
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")
        
        # Calculate expiration time
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in
        
        return token_data
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        import requests
        
        if not self.refresh_token:
            raise AuthenticationError("No refresh token available")
        
        token_url = f"{self.base_url}/api/auth/oauth2/token"
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError(
                f"Token refresh failed: {response.text}",
                status_code=response.status_code,
            )
        
        token_data = response.json()
        
        # Update tokens
        self.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            self.refresh_token = token_data["refresh_token"]
        
        # Calculate expiration time
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in
        
        return token_data
    
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self.token_expires_at:
            return True
        
        # Consider token expired 60 seconds before actual expiration
        return time.time() >= (self.token_expires_at - 60)
    
    def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if not self.access_token:
            raise AuthenticationError("No access token available. Please authenticate first.")
        
        if self.is_token_expired():
            self.refresh_access_token()
        
        return self.access_token
    
    def start_local_server_flow(self) -> Dict[str, Any]:
        """
        Start a local HTTP server to handle OAuth callback.
        Opens browser for user authorization.
        """
        
        # Generate state for CSRF protection
        import secrets
        state = secrets.token_urlsafe(32)
        
        # Storage for the authorization code
        auth_code = {"code": None, "error": None}
        
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse query parameters
                parsed_url = urlparse(self.path)
                params = parse_qs(parsed_url.query)
                
                if "code" in params:
                    auth_code["code"] = params["code"][0]
                    # Send success response
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html>
                        <body>
                            <h1>Authorization Successful!</h1>
                            <p>You can close this window and return to your application.</p>
                        </body>
                        </html>
                    """)
                elif "error" in params:
                    auth_code["error"] = params["error"][0]
                    # Send error response
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"""
                        <html>
                        <body>
                            <h1>Authorization Failed</h1>
                            <p>Error: {params["error"][0]}</p>
                        </body>
                        </html>
                    """.encode())
                
            def log_message(self, format, *args):
                # Suppress logging
                pass
        
        # Start local server
        port = int(urlparse(self.redirect_uri).port or 8080)
        with socketserver.TCPServer(("", port), CallbackHandler) as httpd:
            # Open browser
            auth_url = self.get_authorization_url(state)
            print(f"Opening browser for authentication...")
            print(f"If the browser doesn't open, visit: {auth_url}")
            webbrowser.open(auth_url)
            
            # Wait for callback
            print("Waiting for authorization...")
            while auth_code["code"] is None and auth_code["error"] is None:
                httpd.handle_request()
        
        if auth_code["error"]:
            raise AuthenticationError(f"Authorization failed: {auth_code['error']}")
        
        if not auth_code["code"]:
            raise AuthenticationError("No authorization code received")
        
        # Exchange code for token
        return self.exchange_code_for_token(auth_code["code"])


class TokenStorage:
    """Manages persistent storage of OAuth tokens."""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            home = os.path.expanduser("~")
            storage_path = os.path.join(home, ".canvelete", "credentials.json")
        
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    
    def save_tokens(self, tokens: Dict[str, Any]):
        """Save tokens to storage."""
        with open(self.storage_path, "w") as f:
            json.dump(tokens, f, indent=2)
    
    def load_tokens(self) -> Optional[Dict[str, Any]]:
        """Load tokens from storage."""
        if not os.path.exists(self.storage_path):
            return None
        
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def clear_tokens(self):
        """Clear stored tokens."""
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
