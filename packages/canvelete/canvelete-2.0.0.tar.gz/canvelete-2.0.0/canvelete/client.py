"""Main Canvelete API client."""

import time
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import OAuth2Handler, TokenStorage
from .exceptions import (
    CanveleteError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    InsufficientScopeError,
)
from .resources.designs import DesignsResource
from .resources.templates import TemplatesResource
from .resources.render import RenderResource
from .resources.api_keys import APIKeysResource
from .resources.canvas import CanvasResource
from .resources.assets import AssetsResource
from .resources.usage import UsageResource
from .resources.billing import BillingResource


class CanveleteClient:
    """
    Main client for interacting with the Canvelete API.
    
    Supports two authentication methods:
    1. API Key (simpler, for server-to-server)
    2. OAuth2 (for user authorization flows)
    
    Example with API Key:
        client = CanveleteClient(api_key="cvt_your_api_key")
        designs = client.designs.list()
    
    Example with OAuth2:
        client = CanveleteClient(
            client_id="your_client_id",
            client_secret="your_client_secret"
        )
        client.authenticate()  # Opens browser for authorization
        designs = client.designs.list()
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: str = "https://www.canvelete.com",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize the Canvelete client.
        
        Args:
            api_key: API key for authentication (alternative to OAuth2)
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            base_url: Base URL for the Canvelete API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        
        # Initialize OAuth2 handler if credentials provided
        self.oauth2: Optional[OAuth2Handler] = None
        if client_id and client_secret:
            self.oauth2 = OAuth2Handler(
                client_id=client_id,
                client_secret=client_secret,
                base_url=base_url,
            )
            self.token_storage = TokenStorage()
            self._load_stored_tokens()
        
        # Create session with retry logic
        self.session = self._create_session(max_retries)
        
        # Initialize resource handlers
        self.designs = DesignsResource(self)
        self.templates = TemplatesResource(self)
        self.render = RenderResource(self)
        self.api_keys = APIKeysResource(self)
        self.canvas = CanvasResource(self)
        self.assets = AssetsResource(self)
        self.usage = UsageResource(self)
        self.billing = BillingResource(self)
    
    def _create_session(self, max_retries: int) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _load_stored_tokens(self):
        """Load stored OAuth2 tokens if available."""
        if not self.oauth2 or not self.token_storage:
            return
        
        tokens = self.token_storage.load_tokens()
        if tokens:
            self.oauth2.access_token = tokens.get("access_token")
            self.oauth2.refresh_token = tokens.get("refresh_token")
            self.oauth2.token_expires_at = tokens.get("expires_at")
    
    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate using OAuth2 flow.
        Opens a browser for user authorization.
        
        Returns:
            Token data dictionary
        """
        if not self.oauth2:
            raise AuthenticationError(
                "OAuth2 not configured. Provide client_id and client_secret."
            )
        
        token_data = self.oauth2.start_local_server_flow()
        
        # Store tokens
        if self.token_storage:
            self.token_storage.save_tokens({
                "access_token": self.oauth2.access_token,
                "refresh_token": self.oauth2.refresh_token,
                "expires_at": self.oauth2.token_expires_at,
            })
        
        return token_data
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "canvelete-python/1.0.0",
        }
        
        # Try OAuth2 first
        if self.oauth2 and self.oauth2.access_token:
            try:
                token = self.oauth2.get_valid_token()
                headers["Authorization"] = f"Bearer {token}"
                return headers
            except AuthenticationError:
                # Fall through to API key if OAuth2 fails
                pass
        
        # Use API key
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            return headers
        
        raise AuthenticationError(
            "No authentication method available. "
            "Provide api_key or authenticate with OAuth2."
        )
    
    def request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make an authenticated API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/api/automation/designs")
            json_data: JSON body data
            params: Query parameters
            **kwargs: Additional arguments for requests
        
        Returns:
            Response object
        
        Raises:
            Various CanveleteError subclasses
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=self.timeout,
                **kwargs
            )
            
            self._handle_response_errors(response)
            return response
            
        except requests.exceptions.Timeout:
            raise CanveleteError(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise CanveleteError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise CanveleteError(f"Request failed: {str(e)}")
    
    def _handle_response_errors(self, response: requests.Response):
        """Handle HTTP error responses."""
        if response.status_code < 400:
            return
        
        try:
            error_data = response.json()
            message = error_data.get("error", error_data.get("message", "Unknown error"))
        except:
            message = response.text or f"HTTP {response.status_code}"
        
        # Map status codes to exceptions
        if response.status_code == 401:
            raise AuthenticationError(message, status_code=401, response=response)
        elif response.status_code == 403:
            if "scope" in message.lower():
                raise InsufficientScopeError(message, status_code=403, response=response)
            raise AuthenticationError(message, status_code=403, response=response)
        elif response.status_code == 404:
            raise NotFoundError(message, status_code=404, response=response)
        elif response.status_code == 422:
            raise ValidationError(message, status_code=422, response=response)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
                status_code=429,
                response=response,
            )
        elif response.status_code >= 500:
            raise ServerError(message, status_code=response.status_code, response=response)
        else:
            raise CanveleteError(message, status_code=response.status_code, response=response)
