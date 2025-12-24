"""Templates API resource."""

from typing import Optional, Dict, Any, Iterator


class TemplatesResource:
    """Handler for Templates API endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def list(
        self,
        page: int = 1,
        limit: int = 20,
        my_only: bool = False,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List available templates.
        
        Args:
            page: Page number (1-indexed)
            limit: Number of results per page
            my_only: Only show templates created by current user
            search: Search query
        
        Returns:
            Response with templates data and pagination info
        """
        params = {"page": page, "limit": limit}
        
        if my_only:
            params["myOnly"] = "true"
        
        if search:
            params["search"] = search
        
        response = self.client.request(
            "GET",
            "/api/automation/templates",
            params=params,
        )
        
        return response.json()
    
    def iterate_all(
        self,
        limit: int = 50,
        my_only: bool = False,
        search: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate through all templates with automatic pagination.
        
        Args:
            limit: Number of results per page
            my_only: Only show templates created by current user
            search: Search query
        
        Yields:
            Individual template dictionaries
        """
        page = 1
        while True:
            response = self.list(
                page=page,
                limit=limit,
                my_only=my_only,
                search=search,
            )
            
            templates = response.get("data", [])
            if not templates:
                break
            
            for template in templates:
                yield template
            
            # Check if there are more pages
            pagination = response.get("pagination", {})
            if page >= pagination.get("totalPages", 1):
                break
            
            page += 1
    
    def get(self, template_id: str) -> Dict[str, Any]:
        """
        Get a specific template by ID.
        
        Note: This uses the designs endpoint since templates are designs
        with isTemplate=true.
        
        Args:
            template_id: Template ID
        
        Returns:
            Template data
        """
        response = self.client.request(
            "GET",
            f"/api/automation/designs/{template_id}",
        )
        
        return response.json().get("data", {})

    def apply(
        self,
        template_id: str,
        name: str,
        dynamic_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Apply a template to create a new design with dynamic data.
        
        Args:
            template_id: Template ID to apply
            name: Name for the new design
            dynamic_data: Dynamic field values to apply
        
        Returns:
            Created design data
        
        Example:
            design = client.templates.apply(
                template_id="tmpl_123",
                name="John's Certificate",
                dynamic_data={
                    "name": "John Doe",
                    "date": "2024-01-01",
                    "company": "Acme Corp"
                }
            )
        """
        payload = {
            "templateId": template_id,
            "name": name,
        }
        
        if dynamic_data:
            payload["dynamicData"] = dynamic_data
        
        response = self.client.request(
            "POST",
            "/api/templates/apply",
            json_data=payload,
        )
        
        return response.json().get("data", {})
    
    def create(
        self,
        design_id: str,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a template from an existing design.
        
        Args:
            design_id: Design ID to convert to template
            name: Template name
            description: Template description
            category: Template category
        
        Returns:
            Created template data
        
        Example:
            template = client.templates.create(
                design_id="design_123",
                name="Certificate Template",
                description="Professional certificate template",
                category="certificates"
            )
        """
        payload = {
            "designId": design_id,
            "name": name,
        }
        
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category
        
        response = self.client.request(
            "POST",
            "/api/templates",
            json_data=payload,
        )
        
        return response.json().get("data", {})
