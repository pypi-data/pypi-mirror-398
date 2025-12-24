"""
Pytest fixtures for Cilow SDK tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import aiohttp

from cilow.client import CilowClient
from cilow.models import Memory, MemoryStats, SearchResult, HealthStatus


@pytest.fixture
def base_url():
    """Base URL for testing"""
    return "http://localhost:8080"


@pytest.fixture
def api_key():
    """Test API key"""
    return "test-api-key-12345"


@pytest.fixture
def mock_memory_data():
    """Sample memory data"""
    return {
        "id": "mem_abc123",
        "memory_id": "mem_abc123",
        "content": "User prefers Python programming",
        "created_at": "2024-01-15T10:30:00Z",
        "tier": "hot",
        "salience": 0.95,
        "access_count": 5,
        "tags": ["preference", "programming"],
        "metadata": {"source": "conversation"},
    }


@pytest.fixture
def mock_search_results():
    """Sample search results"""
    return [
        {
            "memory_id": "mem_abc123",
            "content": "User prefers Python programming",
            "created_at": "2024-01-15T10:30:00Z",
            "tier": "hot",
            "salience": 0.95,
            "score": 0.92,
            "tags": ["preference"],
        },
        {
            "memory_id": "mem_def456",
            "content": "User also likes Rust for systems programming",
            "created_at": "2024-01-14T09:00:00Z",
            "tier": "warm",
            "salience": 0.85,
            "score": 0.78,
            "tags": ["preference"],
        },
    ]


@pytest.fixture
def mock_stats_data():
    """Sample memory stats"""
    return {
        "total_memories": 150,
        "hot_tier_count": 50,
        "warm_tier_count": 75,
        "cold_tier_count": 25,
        "avg_salience": 0.72,
        "total_tokens": 45000,
        "total_embeddings": 150,
    }


@pytest.fixture
def mock_health_data():
    """Sample health check response"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "uptime_seconds": 86400,
        "memory_usage_mb": 256.5,
    }


@pytest.fixture
def mock_response():
    """Create a mock aiohttp response"""
    def _mock_response(status=200, json_data=None):
        mock = AsyncMock()
        mock.status = status
        mock.json = AsyncMock(return_value=json_data or {})
        mock.text = AsyncMock(return_value="")
        return mock
    return _mock_response


@pytest.fixture
def mock_session(mock_response):
    """Create a mock aiohttp session"""
    def _mock_session(responses):
        """
        Args:
            responses: List of (method, url_contains, response_data) or single response
        """
        session = MagicMock(spec=aiohttp.ClientSession)

        if isinstance(responses, dict):
            # Single response for all requests
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response(200, responses)
            mock_cm.__aexit__.return_value = None
            session.request = MagicMock(return_value=mock_cm)
            session.get = MagicMock(return_value=mock_cm)
            session.post = MagicMock(return_value=mock_cm)
            session.put = MagicMock(return_value=mock_cm)
            session.delete = MagicMock(return_value=mock_cm)
        else:
            # Multiple responses based on URL
            def create_response(method, url, **kwargs):
                for resp_method, url_pattern, data, status in responses:
                    if resp_method == method.upper() and url_pattern in url:
                        mock_cm = AsyncMock()
                        mock_cm.__aenter__.return_value = mock_response(status, data)
                        mock_cm.__aexit__.return_value = None
                        return mock_cm
                # Default response
                mock_cm = AsyncMock()
                mock_cm.__aenter__.return_value = mock_response(404, {"error": "Not found"})
                mock_cm.__aexit__.return_value = None
                return mock_cm

            session.request = MagicMock(side_effect=create_response)

        session.close = AsyncMock()
        return session

    return _mock_session


@pytest.fixture
async def client(base_url, api_key):
    """Create a CilowClient instance (not connected)"""
    return CilowClient(base_url=base_url, api_key=api_key)


class MockContextManager:
    """Helper for mocking async context manager"""
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass
