"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
from canvelete import CanveleteClient


@pytest.fixture
def mock_client():
    """Create a mock Canvelete client for testing."""
    client = CanveleteClient(api_key="test_key")
    client.request = Mock()
    return client


@pytest.fixture
def sample_design():
    """Sample design data for testing."""
    return {
        "id": "design_123",
        "name": "Test Design",
        "description": "A test design",
        "width": 1920,
        "height": 1080,
        "status": "DRAFT",
        "visibility": "PRIVATE",
        "isTemplate": False,
        "canvasData": {
            "elements": [
                {
                    "type": "text",
                    "text": "Hello World",
                    "x": 100,
                    "y": 100,
                    "fontSize": 24,
                }
            ]
        },
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_element():
    """Sample canvas element for testing."""
    return {
        "type": "text",
        "text": "Test Element",
        "x": 100,
        "y": 100,
        "width": 200,
        "height": 50,
        "fontSize": 24,
        "fontFamily": "Arial",
    }


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.json = Mock(return_value={"data": [], "pagination": {}})
    response.content = b"mock_image_data"
    return response
