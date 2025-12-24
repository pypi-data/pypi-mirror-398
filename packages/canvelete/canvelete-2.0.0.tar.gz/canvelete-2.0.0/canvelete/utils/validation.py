"""Element validation utilities."""

from typing import Dict, Any, List


class ValidationError(Exception):
    """Element validation error."""
    
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {', '.join(errors)}")


def validate_element(element: Dict[str, Any]) -> List[str]:
    """
    Validate a canvas element.
    
    Args:
        element: Element dictionary to validate
    
    Returns:
        List of validation errors (empty if valid)
    
    Example:
        errors = validate_element({
            "type": "text",
            "text": "Hello",
            "x": 100,
            "y": 100
        })
        
        if errors:
            print(f"Validation errors: {errors}")
    """
    errors = []
    
    # Required fields
    if "type" not in element:
        errors.append("Missing required field: type")
    
    if "x" not in element:
        errors.append("Missing required field: x")
    
    if "y" not in element:
        errors.append("Missing required field: y")
    
    # Type-specific validation
    element_type = element.get("type")
    
    if element_type == "text":
        if "text" not in element:
            errors.append("Text element missing 'text' field")
        if "fontSize" not in element:
            errors.append("Text element missing 'fontSize' field")
    
    elif element_type == "image":
        if "src" not in element:
            errors.append("Image element missing 'src' field")
    
    elif element_type in ["rect", "rectangle", "circle"]:
        if "width" not in element:
            errors.append(f"{element_type} element missing 'width' field")
        if "height" not in element:
            errors.append(f"{element_type} element missing 'height' field")
    
    elif element_type == "qr":
        if "qrValue" not in element:
            errors.append("QR element missing 'qrValue' field")
    
    elif element_type == "barcode":
        if "barcodeValue" not in element:
            errors.append("Barcode element missing 'barcodeValue' field")
        if "barcodeFormat" not in element:
            errors.append("Barcode element missing 'barcodeFormat' field")
    
    # Validate numeric ranges
    if "opacity" in element:
        opacity = element["opacity"]
        if not (0 <= opacity <= 1):
            errors.append(f"Opacity must be between 0 and 1, got {opacity}")
    
    if "rotation" in element:
        rotation = element["rotation"]
        if not (0 <= rotation <= 360):
            errors.append(f"Rotation must be between 0 and 360, got {rotation}")
    
    if "fontSize" in element:
        font_size = element["fontSize"]
        if font_size <= 0:
            errors.append(f"Font size must be positive, got {font_size}")
    
    return errors


def validate_canvas_data(canvas_data: Dict[str, Any]) -> List[str]:
    """
    Validate complete canvas data.
    
    Args:
        canvas_data: Canvas data dictionary
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if "elements" not in canvas_data:
        errors.append("Canvas data missing 'elements' array")
        return errors
    
    elements = canvas_data["elements"]
    if not isinstance(elements, list):
        errors.append("'elements' must be an array")
        return errors
    
    # Validate each element
    for i, element in enumerate(elements):
        element_errors = validate_element(element)
        for error in element_errors:
            errors.append(f"Element {i}: {error}")
    
    return errors
