"""Tests for Canvas resource."""

import pytest
from unittest.mock import Mock


def test_add_element(mock_client, mock_response, sample_element):
    """Test adding an element to canvas."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {"data": sample_element}
    
    result = mock_client.canvas.add_element(
        design_id="design_123",
        element=sample_element
    )
    
    assert result["type"] == "text"
    assert result["text"] == "Test Element"
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "POST"
    assert "elements" in call_args[0][1]


def test_update_element(mock_client, mock_response, sample_element):
    """Test updating an element."""
    mock_client.request.return_value = mock_response
    updated_element = sample_element.copy()
    updated_element["text"] = "Updated Text"
    mock_response.json.return_value = {"data": updated_element}
    
    result = mock_client.canvas.update_element(
        design_id="design_123",
        element_id="elem_456",
        updates={"text": "Updated Text"}
    )
    
    assert result["text"] == "Updated Text"
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "PATCH"


def test_delete_element(mock_client, mock_response):
    """Test deleting an element."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {"success": True}
    
    result = mock_client.canvas.delete_element(
        design_id="design_123",
        element_id="elem_456"
    )
    
    assert result is True
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "DELETE"


def test_get_elements(mock_client, mock_response, sample_element):
    """Test getting all canvas elements."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": {
            "elements": [sample_element]
        }
    }
    
    result = mock_client.canvas.get_elements(design_id="design_123")
    
    assert "elements" in result
    assert len(result["elements"]) == 1
    
    mock_client.request.assert_called_once()


def test_resize_canvas(mock_client, mock_response, sample_design):
    """Test resizing canvas."""
    mock_client.request.return_value = mock_response
    resized_design = sample_design.copy()
    resized_design["width"] = 3840
    resized_design["height"] = 2160
    mock_response.json.return_value = {"data": resized_design}
    
    result = mock_client.canvas.resize(
        design_id="design_123",
        width=3840,
        height=2160
    )
    
    assert result["width"] == 3840
    assert result["height"] == 2160
    
    mock_client.request.assert_called_once()


def test_clear_canvas(mock_client, mock_response):
    """Test clearing all elements from canvas."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {"success": True}
    
    result = mock_client.canvas.clear(design_id="design_123")
    
    assert result is True
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "DELETE"


def test_update_background(mock_client, mock_response, sample_design):
    """Test updating canvas background."""
    mock_client.request.return_value = mock_response
    updated_design = sample_design.copy()
    updated_design["canvasData"]["background"] = "#FF0000"
    mock_response.json.return_value = {"data": updated_design}
    
    result = mock_client.canvas.update_background(
        design_id="design_123",
        background="#FF0000"
    )
    
    assert result["canvasData"]["background"] == "#FF0000"
    
    mock_client.request.assert_called_once()
