"""Asset management API resource."""

from typing import Optional, Dict, Any, Iterator, BinaryIO, Union
import os


class AssetsResource:
    """Handler for Asset management endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def list(
        self,
        page: int = 1,
        limit: int = 20,
        asset_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List user's uploaded assets.
        
        Args:
            page: Page number (1-indexed)
            limit: Number of results per page
            asset_type: Filter by type (IMAGE, FONT, VIDEO, AUDIO)
        
        Returns:
            Response with assets data and pagination info
        
        Example:
            assets = client.assets.list(asset_type="IMAGE")
            for asset in assets["data"]:
                print(f"{asset['name']}: {asset['url']}")
        """
        params = {"page": page, "limit": limit}
        
        if asset_type:
            params["type"] = asset_type
        
        response = self.client.request(
            "GET",
            "/api/assets/library",
            params=params,
        )
        
        return response.json()
    
    def upload(
        self,
        file_path: str,
        name: str,
        asset_type: str = "IMAGE",
    ) -> Dict[str, Any]:
        """
        Upload an asset to the library.
        
        Args:
            file_path: Path to file to upload
            name: Asset name
            asset_type: Asset type (IMAGE, FONT, VIDEO, AUDIO)
        
        Returns:
            Uploaded asset data
        
        Example:
            asset = client.assets.upload(
                file_path="logo.png",
                name="Company Logo",
                asset_type="IMAGE"
            )
            print(f"Uploaded: {asset['url']}")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get upload signature
        signature_response = self.client.request(
            "POST",
            "/api/assets/upload-signature",
            json_data={
                "filename": os.path.basename(file_path),
                "type": asset_type,
            },
        )
        
        signature_data = signature_response.json()
        
        # Upload to cloud storage (Cloudinary)
        with open(file_path, 'rb') as f:
            files = {'file': f}
            upload_data = signature_data.get("uploadData", {})
            
            import requests
            upload_response = requests.post(
                signature_data["uploadUrl"],
                data=upload_data,
                files=files,
            )
            
            if upload_response.status_code != 200:
                raise Exception(f"Upload failed: {upload_response.text}")
            
            cloud_result = upload_response.json()
        
        # Complete upload and save to database
        complete_response = self.client.request(
            "POST",
            "/api/assets/upload-complete",
            json_data={
                "name": name,
                "type": asset_type,
                "cloudinaryPublicId": cloud_result.get("public_id"),
                "url": cloud_result.get("secure_url"),
                "format": cloud_result.get("format"),
                "size": cloud_result.get("bytes"),
                "width": cloud_result.get("width"),
                "height": cloud_result.get("height"),
            },
        )
        
        return complete_response.json().get("data", {})
    
    def search_stock_images(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for stock images from Pixabay.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
        
        Returns:
            Search results with image data
        
        Example:
            results = client.assets.search_stock_images(
                query="business meeting",
                per_page=10
            )
            for image in results["data"]:
                print(f"{image['tags']}: {image['previewURL']}")
        """
        params = {
            "query": query,
            "page": page,
            "perPage": per_page,
        }
        
        response = self.client.request(
            "GET",
            "/api/assets/stock-images",
            params=params,
        )
        
        return response.json()
    
    def search_icons(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for icon assets.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
        
        Returns:
            Search results with icon data
        
        Example:
            results = client.assets.search_icons(query="arrow")
            for icon in results["data"]:
                print(f"{icon['name']}: {icon['url']}")
        """
        params = {
            "query": query,
            "page": page,
            "perPage": per_page,
        }
        
        response = self.client.request(
            "GET",
            "/api/assets/icons",
            params=params,
        )
        
        return response.json()
    
    def search_clipart(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for clipart images.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            tag: Optional tag filter
        
        Returns:
            Search results with clipart data
        
        Example:
            results = client.assets.search_clipart(
                query="celebration",
                tag="party"
            )
        """
        params = {
            "query": query,
            "page": page,
            "perPage": per_page,
        }
        
        if tag:
            params["tag"] = tag
        
        response = self.client.request(
            "GET",
            "/api/assets/clipart",
            params=params,
        )
        
        return response.json()
    
    def search_illustrations(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for illustration assets.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            category: Optional category filter
        
        Returns:
            Search results with illustration data
        
        Example:
            results = client.assets.search_illustrations(
                query="technology",
                category="business"
            )
        """
        params = {
            "query": query,
            "page": page,
            "perPage": per_page,
        }
        
        if category:
            params["category"] = category
        
        response = self.client.request(
            "GET",
            "/api/assets/illustrations",
            params=params,
        )
        
        return response.json()
    
    def list_fonts(
        self,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List available fonts.
        
        Args:
            category: Optional category filter (serif, sans-serif, monospace, etc.)
        
        Returns:
            List of available fonts
        
        Example:
            fonts = client.assets.list_fonts(category="sans-serif")
            for font in fonts["data"]:
                print(f"{font['family']}: {font['variants']}")
        """
        params = {}
        if category:
            params["category"] = category
        
        response = self.client.request(
            "GET",
            "/api/assets/fonts",
            params=params,
        )
        
        return response.json()
    
    def get(self, asset_id: str) -> Dict[str, Any]:
        """
        Get a specific asset by ID.
        
        Args:
            asset_id: Asset ID
        
        Returns:
            Asset data
        """
        response = self.client.request(
            "GET",
            f"/api/assets/{asset_id}",
        )
        
        return response.json().get("data", {})
    
    def delete(self, asset_id: str) -> bool:
        """
        Delete an asset.
        
        Args:
            asset_id: Asset ID
        
        Returns:
            True if successful
        """
        response = self.client.request(
            "DELETE",
            f"/api/assets/{asset_id}",
        )
        
        return response.json().get("success", False)
