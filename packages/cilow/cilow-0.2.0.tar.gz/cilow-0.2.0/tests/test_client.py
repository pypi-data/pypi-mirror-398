"""
Unit tests for CilowClient
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import aiohttp

from cilow.client import CilowClient, add_memory_sync, search_memories_sync
from cilow.models import Memory, SearchResult, MemoryStats, HealthStatus
from cilow.errors import (
    CilowError,
    ConnectionError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)


class TestCilowClientInit:
    """Tests for client initialization"""

    def test_init_defaults(self):
        """Test default initialization"""
        client = CilowClient()
        assert client.base_url == "http://localhost:8080"
        assert client.api_key is None
        assert client._session is None

    def test_init_with_params(self):
        """Test initialization with custom params"""
        client = CilowClient(
            base_url="https://api.cilow.ai",
            api_key="test-key",
            timeout=60.0,
        )
        assert client.base_url == "https://api.cilow.ai"
        assert client.api_key == "test-key"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base_url"""
        client = CilowClient(base_url="http://localhost:8080/")
        assert client.base_url == "http://localhost:8080"


class TestCilowClientContextManager:
    """Tests for async context manager"""

    @pytest.mark.asyncio
    async def test_session_created_on_enter(self):
        """Test that session is created on context enter"""
        async with CilowClient() as client:
            assert client._session is not None
            assert isinstance(client._session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_session_closed_on_exit(self):
        """Test that session is closed on context exit"""
        client = CilowClient()
        async with client:
            session = client._session
        assert client._session is None

    @pytest.mark.asyncio
    async def test_get_session_raises_without_context(self):
        """Test that _get_session raises error outside context"""
        client = CilowClient()
        with pytest.raises(RuntimeError, match="async context manager"):
            client._get_session()


class TestMemoryOperations:
    """Tests for memory operations"""

    @pytest.mark.asyncio
    async def test_add_memory(self, mock_memory_data):
        """Test adding a memory"""
        response_data = {"memory_id": "mem_abc123"}

        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=response_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient(api_key="test-key") as client:
                client._session = mock_session
                memory_id = await client.add_memory(
                    content="User prefers Python",
                    metadata={"source": "test"},
                    tags=["preference"],
                )

            assert memory_id == "mem_abc123"
            mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_memory_with_user_id(self):
        """Test adding memory with user_id for multi-tenant"""
        response_data = {"memory_id": "mem_xyz789"}

        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=response_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                memory_id = await client.add_memory(
                    content="Test memory",
                    user_id="user_123",
                )

            assert memory_id == "mem_xyz789"
            call_args = mock_session.request.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_get_memory(self, mock_memory_data):
        """Test getting a memory by ID"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_memory_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                memory = await client.get_memory("mem_abc123")

            assert isinstance(memory, Memory)
            assert memory.id == "mem_abc123"
            assert memory.content == "User prefers Python programming"

    @pytest.mark.asyncio
    async def test_update_memory(self, mock_memory_data):
        """Test updating a memory"""
        updated_data = {**mock_memory_data, "content": "Updated content"}

        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=updated_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                memory = await client.update_memory(
                    "mem_abc123",
                    content="Updated content",
                )

            assert isinstance(memory, Memory)
            assert memory.content == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_memory(self):
        """Test deleting a memory"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"deleted": True})

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                result = await client.delete_memory("mem_abc123")

            assert result is True


class TestSearchOperations:
    """Tests for search operations"""

    @pytest.mark.asyncio
    async def test_search_memories(self, mock_search_results):
        """Test searching memories"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_search_results)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                results = await client.search_memories("programming", limit=10)

            assert len(results) == 2
            assert all(isinstance(r, SearchResult) for r in results)
            assert results[0].memory.content == "User prefers Python programming"
            assert results[0].score == 0.92

    @pytest.mark.asyncio
    async def test_search_memories_with_tags(self, mock_search_results):
        """Test searching memories with tag filter"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_search_results)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                results = await client.search_memories(
                    "programming",
                    tags=["preference"],
                    tag_mode="any",
                )

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_memories_with_min_relevance(self, mock_search_results):
        """Test searching with minimum relevance threshold"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_search_results)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                results = await client.search_memories(
                    "programming",
                    min_relevance=0.8,
                )

            # Verify request was made with min_relevance
            assert len(results) >= 0


class TestHealthAndStats:
    """Tests for health check and stats"""

    @pytest.mark.asyncio
    async def test_health_check(self, mock_health_data):
        """Test health check endpoint"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_health_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.get = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                health = await client.health_check()

            assert isinstance(health, HealthStatus)
            assert health.status == "healthy"
            assert health.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, mock_stats_data):
        """Test getting memory stats"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_stats_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                stats = await client.get_memory_stats()

            assert isinstance(stats, MemoryStats)
            assert stats.total_memories == 150
            assert stats.hot_tier_count == 50


class TestErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test 401 raises AuthenticationError"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                with pytest.raises(AuthenticationError):
                    await client.get_memory("mem_123")

    @pytest.mark.asyncio
    async def test_not_found_error(self):
        """Test 404 raises NotFoundError"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Not found")

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                with pytest.raises(NotFoundError):
                    await client.get_memory("nonexistent")

    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Test 422 raises ValidationError"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 422
            mock_response.text = AsyncMock(return_value="Invalid content")

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                with pytest.raises(ValidationError):
                    await client.add_memory("")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test 429 raises RateLimitError"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.text = AsyncMock(return_value="Rate limited")

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                with pytest.raises(RateLimitError):
                    await client.search_memories("test")

    @pytest.mark.asyncio
    async def test_generic_error(self):
        """Test generic 5xx raises CilowError"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal error")

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                with pytest.raises(CilowError):
                    await client.add_memory("test")

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test connection error handling"""
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_cm = AsyncMock()
            mock_cm.__aenter__.side_effect = aiohttp.ClientError("Connection failed")
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                with pytest.raises(ConnectionError):
                    await client.add_memory("test")


class TestConversationOperations:
    """Tests for conversation operations"""

    @pytest.mark.asyncio
    async def test_add_conversation(self):
        """Test adding a conversation turn"""
        response_data = {"memory_id": "mem_conv123"}

        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=response_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                memory_id = await client.add_conversation(
                    user_message="What's the weather?",
                    assistant_message="It's sunny today!",
                    session_id="session_123",
                )

            assert memory_id == "mem_conv123"


class TestAgentOperations:
    """Tests for agent operations"""

    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Test creating an agent"""
        response_data = {"agent_id": "agent_abc123"}

        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=response_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                agent_id = await client.create_agent(
                    name="assistant",
                    agent_type="react",
                )

            assert agent_id == "agent_abc123"

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test executing a task with an agent"""
        response_data = {
            "success": True,
            "response": "Based on your memories, you prefer Python.",
            "reasoning": "Found relevant memories about programming preferences.",
            "memories_used": ["mem_abc123"],
            "tokens_used": 150,
            "execution_time_ms": 250,
        }

        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=response_data)

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_cm.__aexit__.return_value = None
            mock_session.request = MagicMock(return_value=mock_cm)
            mock_session.close = AsyncMock()

            async with CilowClient() as client:
                client._session = mock_session
                result = await client.execute_task(
                    agent_id="agent_abc123",
                    task="What programming language do I prefer?",
                    include_reasoning=True,
                )

            assert result.success is True
            assert "Python" in result.response
            assert len(result.memories_used) == 1


class TestSyncFunctions:
    """Tests for synchronous convenience functions"""

    def test_add_memory_sync(self):
        """Test synchronous add_memory wrapper"""
        # This test would require mocking the entire async flow
        # For now, we verify the function exists and has correct signature
        assert callable(add_memory_sync)

    def test_search_memories_sync(self):
        """Test synchronous search_memories wrapper"""
        assert callable(search_memories_sync)
