"""Tests for Assets resource."""

import pytest
from unittest.mock import Mock, patch, mock_open


def test_list_assets(mock_client, mock_response):
    """Test listing assets."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": [
            {"id": "asset_1", "name": "Logo", "type": "IMAGE"},
            {"id": "asset_2", "name": "Font", "type": "FONT"}
        ],
        "pagination": {"page": 1, "limit": 20, "total": 2, "totalPages": 1}
    }
    
    result = mock_client.assets.list(page=1, limit=20)
    
    assert "data" in result
    assert len(result["data"]) == 2
    assert result["data"][0]["type"] == "IMAGE"
    
    mock_client.request.assert_called_once()


def test_search_stock_images(mock_client, mock_response):
    """Test searching stock images."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": [
            {
                "id": "img_1",
                "tags": "business, meeting",
                "previewURL": "https://example.com/preview.jpg",
                "largeImageURL": "https://example.com/large.jpg"
            }
        ]
    }
    
    result = mock_client.assets.search_stock_images(
        query="business",
        per_page=10
    )
    
    assert "data" in result
    assert len(result["data"]) == 1
    assert "business" in result["data"][0]["tags"]
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[1]["params"]["query"] == "business"


def test_search_icons(mock_client, mock_response):
    """Test searching icons."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": [
            {"id": "icon_1", "name": "arrow-right", "url": "https://example.com/icon.svg"}
        ]
    }
    
    result = mock_client.assets.search_icons(query="arrow")
    
    assert "data" in result
    assert len(result["data"]) == 1
    assert "arrow" in result["data"][0]["name"]
    
    mock_client.request.assert_called_once()


def test_list_fonts(mock_client, mock_response):
    """Test listing fonts."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": [
            {"family": "Arial", "variants": ["regular", "bold"]},
            {"family": "Helvetica", "variants": ["regular", "bold", "italic"]}
        ]
    }
    
    result = mock_client.assets.list_fonts(category="sans-serif")
    
    assert "data" in result
    assert len(result["data"]) == 2
    assert result["data"][0]["family"] == "Arial"
    
    mock_client.request.assert_called_once()


def test_get_asset(mock_client, mock_response):
    """Test getting a specific asset."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": {
            "id": "asset_123",
            "name": "Company Logo",
            "type": "IMAGE",
            "url": "https://example.com/logo.png"
        }
    }
    
    result = mock_client.assets.get("asset_123")
    
    assert result["id"] == "asset_123"
    assert result["name"] == "Company Logo"
    
    mock_client.request.assert_called_once()


def test_delete_asset(mock_client, mock_response):
    """Test deleting an asset."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {"success": True}
    
    result = mock_client.assets.delete("asset_123")
    
    assert result is True
    
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "DELETE"
