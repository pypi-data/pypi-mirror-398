"""Designs API resource."""

from typing import Optional, Dict, Any, Iterator


class DesignsResource:
    """Handler for Designs API endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def list(
        self,
        page: int = 1,
        limit: int = 20,
        is_template: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List user's designs.
        
        Args:
            page: Page number (1-indexed)
            limit: Number of results per page
            is_template: Filter by template status
            status: Filter by status (DRAFT, PUBLISHED, ARCHIVED)
        
        Returns:
            Response with designs data and pagination info
        """
        params = {"page": page, "limit": limit}
        
        if is_template is not None:
            params["isTemplate"] = "true" if is_template else "false"
        
        if status:
            params["status"] = status
        
        response = self.client.request(
            "GET",
            "/api/automation/designs",
            params=params,
        )
        
        return response.json()
    
    def iterate_all(
        self,
        limit: int = 50,
        is_template: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate through all designs with automatic pagination.
        
        Args:
            limit: Number of results per page
            is_template: Filter by template status
            status: Filter by status
        
        Yields:
            Individual design dictionaries
        """
        page = 1
        while True:
            response = self.list(
                page=page,
                limit=limit,
                is_template=is_template,
                status=status,
            )
            
            designs = response.get("data", [])
            if not designs:
                break
            
            for design in designs:
                yield design
            
            # Check if there are more pages
            pagination = response.get("pagination", {})
            if page >= pagination.get("totalPages", 1):
                break
            
            page += 1
    
    def create(
        self,
        name: str,
        canvas_data: Dict[str, Any],
        description: Optional[str] = None,
        width: int = 1920,
        height: int = 1080,
        is_template: bool = False,
        visibility: str = "PRIVATE",
    ) -> Dict[str, Any]:
        """
        Create a new design.
        
        Args:
            name: Design name
            canvas_data: Canvas data dictionary
            description: Optional description
            width: Canvas width in pixels
            height: Canvas height in pixels
            is_template: Whether this is a template
            visibility: Visibility (PRIVATE, PUBLIC, TEAM)
        
        Returns:
            Created design data
        """
        payload = {
            "name": name,
            "canvasData": canvas_data,
            "width": width,
            "height": height,
            "isTemplate": is_template,
            "visibility": visibility,
        }
        
        if description:
            payload["description"] = description
        
        response = self.client.request(
            "POST",
            "/api/automation/designs",
            json_data=payload,
        )
        
        return response.json().get("data", {})
    
    def get(self, design_id: str) -> Dict[str, Any]:
        """
        Get a specific design by ID.
        
        Args:
            design_id: Design ID
        
        Returns:
            Design data
        """
        response = self.client.request(
            "GET",
            f"/api/automation/designs/{design_id}",
        )
        
        return response.json().get("data", {})
    
    def update(
        self,
        design_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        canvas_data: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a design.
        
        Args:
            design_id: Design ID
            name: New name
            description: New description
            canvas_data: New canvas data
            status: New status
            visibility: New visibility
        
        Returns:
            Updated design data
        """
        payload = {}
        
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if canvas_data is not None:
            payload["canvasData"] = canvas_data
        if status is not None:
            payload["status"] = status
        if visibility is not None:
            payload["visibility"] = visibility
        
        response = self.client.request(
            "PATCH",
            f"/api/automation/designs/{design_id}",
            json_data=payload,
        )
        
        return response.json().get("data", {})
    
    def delete(self, design_id: str) -> bool:
        """
        Delete (archive) a design.
        
        Args:
            design_id: Design ID
        
        Returns:
            True if successful
        """
        response = self.client.request(
            "DELETE",
            f"/api/automation/designs/{design_id}",
        )
        
        return response.json().get("success", False)
