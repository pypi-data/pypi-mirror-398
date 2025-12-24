"""Canvas manipulation API resource."""

from typing import Optional, Dict, Any


class CanvasResource:
    """Handler for Canvas manipulation endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def add_element(
        self,
        design_id: str,
        element: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add an element to the canvas.
        
        Args:
            design_id: Design ID
            element: Element data dictionary with type, position, and properties
        
        Returns:
            Created element data with ID
        
        Example:
            element = client.canvas.add_element(
                design_id="design_123",
                element={
                    "type": "text",
                    "text": "Hello World",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 50,
                    "fontSize": 24,
                    "fontFamily": "Arial"
                }
            )
        """
        response = self.client.request(
            "POST",
            f"/api/designs/{design_id}/elements",
            json_data={"element": element},
        )
        
        return response.json().get("data", {})
    
    def update_element(
        self,
        design_id: str,
        element_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update an existing element on the canvas.
        
        Args:
            design_id: Design ID
            element_id: Element ID to update
            updates: Properties to update
        
        Returns:
            Updated element data
        
        Example:
            element = client.canvas.update_element(
                design_id="design_123",
                element_id="elem_456",
                updates={"text": "Updated Text", "fontSize": 32}
            )
        """
        response = self.client.request(
            "PATCH",
            f"/api/designs/{design_id}/elements/{element_id}",
            json_data=updates,
        )
        
        return response.json().get("data", {})
    
    def delete_element(
        self,
        design_id: str,
        element_id: str,
    ) -> bool:
        """
        Delete an element from the canvas.
        
        Args:
            design_id: Design ID
            element_id: Element ID to delete
        
        Returns:
            True if successful
        
        Example:
            success = client.canvas.delete_element(
                design_id="design_123",
                element_id="elem_456"
            )
        """
        response = self.client.request(
            "DELETE",
            f"/api/designs/{design_id}/elements/{element_id}",
        )
        
        return response.json().get("success", False)
    
    def get_elements(
        self,
        design_id: str,
    ) -> Dict[str, Any]:
        """
        Get all elements from a canvas.
        
        Args:
            design_id: Design ID
        
        Returns:
            Canvas data with elements array
        
        Example:
            canvas = client.canvas.get_elements(design_id="design_123")
            for element in canvas["elements"]:
                print(f"Element: {element['type']} at ({element['x']}, {element['y']})")
        """
        response = self.client.request(
            "GET",
            f"/api/designs/{design_id}/canvas",
        )
        
        return response.json().get("data", {})
    
    def resize(
        self,
        design_id: str,
        width: int,
        height: int,
    ) -> Dict[str, Any]:
        """
        Resize the canvas dimensions.
        
        Args:
            design_id: Design ID
            width: New width in pixels
            height: New height in pixels
        
        Returns:
            Updated design data
        
        Example:
            design = client.canvas.resize(
                design_id="design_123",
                width=1920,
                height=1080
            )
        """
        response = self.client.request(
            "PATCH",
            f"/api/designs/{design_id}/canvas/resize",
            json_data={"width": width, "height": height},
        )
        
        return response.json().get("data", {})
    
    def clear(
        self,
        design_id: str,
    ) -> bool:
        """
        Remove all elements from the canvas.
        
        Args:
            design_id: Design ID
        
        Returns:
            True if successful
        
        Example:
            success = client.canvas.clear(design_id="design_123")
        """
        response = self.client.request(
            "DELETE",
            f"/api/designs/{design_id}/canvas/elements",
        )
        
        return response.json().get("success", False)
    
    def update_background(
        self,
        design_id: str,
        background: str,
    ) -> Dict[str, Any]:
        """
        Update canvas background color or gradient.
        
        Args:
            design_id: Design ID
            background: Background color (hex) or gradient definition
        
        Returns:
            Updated design data
        
        Example:
            # Solid color
            design = client.canvas.update_background(
                design_id="design_123",
                background="#FFFFFF"
            )
            
            # Gradient
            design = client.canvas.update_background(
                design_id="design_123",
                background="linear-gradient(90deg, #FF0000, #0000FF)"
            )
        """
        response = self.client.request(
            "PATCH",
            f"/api/designs/{design_id}/canvas/background",
            json_data={"background": background},
        )
        
        return response.json().get("data", {})
