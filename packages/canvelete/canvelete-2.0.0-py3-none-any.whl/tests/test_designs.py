"""Tests for Designs resource."""

import pytest
from unittest.mock import Mock
from canvelete.exceptions import ValidationError


def test_list_designs(mock_client, mock_response):
    """Test listing designs."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": [{"id": "design_1", "name": "Design 1"}],
        "pagination": {"page": 1, "limit": 20, "total": 1, "totalPages": 1}
    }
    
    result = mock_client.designs.list(page=1, limit=20)
    
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "design_1"
    
    mock_client.request.assert_called_once_with(
        "GET",
        "/api/automation/designs",
        params={"page": 1, "limit": 20}
    )


def test_create_design(mock_client, mock_response, sample_design):
    """Test creating a design."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {"data": sample_design}
    
    result = mock_client.designs.create(
        name="Test Design",
        canvas_data={"elements": []},
        width=1920,
        height=1080
    )
    
    assert result["id"] == "design_123"
    assert result["name"] == "Test Design"
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "POST"
    assert call_args[0][1] == "/api/automation/designs"


def test_get_design(mock_client, mock_response, sample_design):
    """Test getting a specific design."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {"data": sample_design}
    
    result = mock_client.designs.get("design_123")
    
    assert result["id"] == "design_123"
    
    mock_client.request.assert_called_once_with(
        "GET",
        "/api/automation/designs/design_123"
    )


def test_update_design(mock_client, mock_response, sample_design):
    """Test updating a design."""
    mock_client.request.return_value = mock_response
    updated_design = sample_design.copy()
    updated_design["name"] = "Updated Design"
    mock_response.json.return_value = {"data": updated_design}
    
    result = mock_client.designs.update(
        "design_123",
        name="Updated Design"
    )
    
    assert result["name"] == "Updated Design"
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "PATCH"


def test_delete_design(mock_client, mock_response):
    """Test deleting a design."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {"success": True}
    
    result = mock_client.designs.delete("design_123")
    
    assert result is True
    
    mock_client.request.assert_called_once_with(
        "DELETE",
        "/api/automation/designs/design_123"
    )


def test_iterate_all_designs(mock_client, mock_response):
    """Test iterating through all designs."""
    # Mock pagination
    page1_response = Mock()
    page1_response.json.return_value = {
        "data": [{"id": f"design_{i}", "name": f"Design {i}"} for i in range(1, 21)],
        "pagination": {"page": 1, "limit": 20, "total": 25, "totalPages": 2}
    }
    
    page2_response = Mock()
    page2_response.json.return_value = {
        "data": [{"id": f"design_{i}", "name": f"Design {i}"} for i in range(21, 26)],
        "pagination": {"page": 2, "limit": 20, "total": 25, "totalPages": 2}
    }
    
    mock_client.request.side_effect = [page1_response, page2_response]
    
    designs = list(mock_client.designs.iterate_all(limit=20))
    
    assert len(designs) == 25
    assert designs[0]["id"] == "design_1"
    assert designs[-1]["id"] == "design_25"
    assert mock_client.request.call_count == 2
