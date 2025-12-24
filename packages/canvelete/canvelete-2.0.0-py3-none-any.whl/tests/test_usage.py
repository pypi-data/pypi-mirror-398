"""Tests for Usage resource."""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta


def test_get_stats(mock_client, mock_response):
    """Test getting usage stats."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": {
            "creditsUsed": 1500,
            "creditLimit": 5000,
            "creditsRemaining": 3500,
            "apiCalls": 250,
            "apiCallLimit": 50000
        }
    }
    
    result = mock_client.usage.get_stats()
    
    assert result["creditsUsed"] == 1500
    assert result["creditLimit"] == 5000
    assert result["creditsRemaining"] == 3500
    
    mock_client.request.assert_called_once()


def test_get_history(mock_client, mock_response):
    """Test getting usage history."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": [
            {
                "type": "RENDER",
                "creditsUsed": 10,
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "type": "EXPORT",
                "creditsUsed": 5,
                "timestamp": "2024-01-01T01:00:00Z"
            }
        ],
        "pagination": {"page": 1, "limit": 20, "total": 2, "totalPages": 1}
    }
    
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    result = mock_client.usage.get_history(
        start_date=start_date,
        end_date=end_date
    )
    
    assert "data" in result
    assert len(result["data"]) == 2
    assert result["data"][0]["type"] == "RENDER"
    
    mock_client.request.assert_called_once()


def test_get_api_stats(mock_client, mock_response):
    """Test getting API usage stats."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": {
            "endpoints": {
                "/api/automation/designs": 150,
                "/api/automation/render": 100,
                "/api/automation/templates": 50
            }
        }
    }
    
    result = mock_client.usage.get_api_stats()
    
    assert "endpoints" in result
    assert result["endpoints"]["/api/automation/designs"] == 150
    
    mock_client.request.assert_called_once()


def test_get_activities(mock_client, mock_response):
    """Test getting recent activities."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": [
            {
                "action": "design_created",
                "timestamp": "2024-01-01T00:00:00Z",
                "details": {"designId": "design_123"}
            }
        ],
        "pagination": {"page": 1, "limit": 10, "total": 1, "totalPages": 1}
    }
    
    result = mock_client.usage.get_activities(limit=10)
    
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["action"] == "design_created"
    
    mock_client.request.assert_called_once()


def test_get_analytics(mock_client, mock_response):
    """Test getting usage analytics."""
    mock_client.request.return_value = mock_response
    mock_response.json.return_value = {
        "data": {
            "totalRenders": 500,
            "averagePerDay": 16.67,
            "peakDay": "2024-01-15",
            "trend": "increasing"
        }
    }
    
    result = mock_client.usage.get_analytics(period="month")
    
    assert result["totalRenders"] == 500
    assert result["trend"] == "increasing"
    
    mock_client.request.assert_called_once()
