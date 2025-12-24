"""API Keys resource."""

from typing import Optional, Dict, Any


class APIKeysResource:
    """Handler for API Keys API endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def list(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        List API keys.
        
        Note: This requires OAuth2 authentication.
        API key authentication cannot be used to manage API keys.
        
        Args:
            page: Page number (1-indexed)
            limit: Number of results per page
        
        Returns:
            Response with API keys data and pagination info
        """
        params = {"page": page, "limit": limit}
        
        response = self.client.request(
            "GET",
            "/api/automation/api-keys",
            params=params,
        )
        
        return response.json()
    
    def create(
        self,
        name: str,
        expires_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new API key.
        
        Note: This requires OAuth2 authentication.
        API key authentication cannot be used to manage API keys.
        
        ⚠️ IMPORTANT: The raw API key is only returned once!
        Store it securely. You won't be able to retrieve it again.
        
        Args:
            name: Descriptive name for the API key
            expires_at: Optional expiration date (ISO 8601 format)
        
        Returns:
            API key data with the raw key (shown only once!)
        """
        payload = {"name": name}
        
        if expires_at:
            payload["expiresAt"] = expires_at
        
        response = self.client.request(
            "POST",
            "/api/automation/api-keys",
            json_data=payload,
        )
        
        return response.json().get("data", {})
