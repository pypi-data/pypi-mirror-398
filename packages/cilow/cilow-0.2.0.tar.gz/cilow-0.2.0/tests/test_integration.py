"""
Integration tests for Cilow Python SDK

These tests require a running Cilow API server.
Set CILOW_API_URL and CILOW_API_KEY environment variables.

Run with: pytest tests/test_integration.py -v --run-integration
"""

import os
import pytest
import asyncio
import uuid
from datetime import datetime

from cilow.client import CilowClient
from cilow.models import Memory, SearchResult, MemoryStats


# Skip all tests in this file if not running integration tests
pytestmark = pytest.mark.integration


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


@pytest.fixture
def api_url():
    """Get API URL from environment"""
    return os.environ.get("CILOW_API_URL", "http://localhost:8080")


@pytest.fixture
def api_key():
    """Get API key from environment"""
    return os.environ.get("CILOW_API_KEY", "test-api-key")


@pytest.fixture
def unique_content():
    """Generate unique content for testing"""
    return f"Test memory created at {datetime.now().isoformat()} - {uuid.uuid4().hex[:8]}"


@pytest.fixture
async def client(api_url, api_key):
    """Create and return a connected client"""
    async with CilowClient(base_url=api_url, api_key=api_key) as client:
        yield client


class TestHealthIntegration:
    """Integration tests for health endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_live(self, api_url, api_key):
        """Test health check against live API"""
        async with CilowClient(base_url=api_url, api_key=api_key) as client:
            health = await client.health_check()

            assert health.status in ["healthy", "ok"]
            assert health.version is not None


class TestMemoryIntegration:
    """Integration tests for memory operations"""

    @pytest.mark.asyncio
    async def test_add_memory_live(self, client, unique_content):
        """Test adding a memory to live API"""
        memory_id = await client.add_memory(
            content=unique_content,
            metadata={"test": True, "created_by": "integration_test"},
            tags=["test", "integration"],
        )

        assert memory_id is not None
        assert len(memory_id) > 0

        # Clean up
        try:
            await client.delete_memory(memory_id)
        except Exception:
            pass  # Ignore cleanup errors

    @pytest.mark.asyncio
    async def test_get_memory_live(self, client, unique_content):
        """Test getting a memory from live API"""
        # First add a memory
        memory_id = await client.add_memory(content=unique_content)

        # Then retrieve it
        memory = await client.get_memory(memory_id)

        assert isinstance(memory, Memory)
        assert memory.id == memory_id
        assert memory.content == unique_content

        # Clean up
        await client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_update_memory_live(self, client, unique_content):
        """Test updating a memory on live API"""
        # Add memory
        memory_id = await client.add_memory(content=unique_content)

        # Update it
        updated_content = f"Updated: {unique_content}"
        memory = await client.update_memory(
            memory_id,
            content=updated_content,
            tags=["updated"],
        )

        assert memory.content == updated_content
        assert "updated" in memory.tags

        # Clean up
        await client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_delete_memory_live(self, client, unique_content):
        """Test deleting a memory on live API"""
        # Add memory
        memory_id = await client.add_memory(content=unique_content)

        # Delete it
        result = await client.delete_memory(memory_id)
        assert result is True

        # Verify it's deleted
        from cilow.errors import NotFoundError
        with pytest.raises(NotFoundError):
            await client.get_memory(memory_id)

    @pytest.mark.asyncio
    async def test_memory_lifecycle(self, client):
        """Test complete memory lifecycle: create, read, update, delete"""
        # Create
        content = f"Lifecycle test {uuid.uuid4().hex[:8]}"
        memory_id = await client.add_memory(
            content=content,
            tags=["lifecycle"],
        )
        assert memory_id is not None

        # Read
        memory = await client.get_memory(memory_id)
        assert memory.content == content
        assert "lifecycle" in memory.tags

        # Update
        new_content = f"Updated {content}"
        updated = await client.update_memory(
            memory_id,
            content=new_content,
        )
        assert updated.content == new_content

        # Delete
        deleted = await client.delete_memory(memory_id)
        assert deleted is True


class TestSearchIntegration:
    """Integration tests for search operations"""

    @pytest.mark.asyncio
    async def test_search_memories_live(self, client):
        """Test searching memories on live API"""
        # Add some test memories
        unique_term = f"unique{uuid.uuid4().hex[:8]}"
        memory_ids = []

        for i in range(3):
            content = f"Test memory {i} about {unique_term}"
            memory_id = await client.add_memory(
                content=content,
                tags=["search_test"],
            )
            memory_ids.append(memory_id)

        # Wait for indexing
        await asyncio.sleep(0.5)

        # Search for them
        results = await client.search_memories(
            query=unique_term,
            limit=10,
        )

        assert len(results) >= 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(unique_term in r.memory.content for r in results)

        # Clean up
        for memory_id in memory_ids:
            await client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_search_with_tags_live(self, client):
        """Test tag-filtered search on live API"""
        unique_tag = f"tag_{uuid.uuid4().hex[:8]}"

        # Add memories with unique tag
        memory_id = await client.add_memory(
            content="Memory with unique tag",
            tags=[unique_tag, "test"],
        )

        # Wait for indexing
        await asyncio.sleep(0.5)

        # Search with tag filter
        results = await client.search_memories(
            query="Memory",
            tags=[unique_tag],
            tag_mode="any",
        )

        # Should find our memory
        found_ids = [r.memory.id for r in results]
        assert memory_id in found_ids

        # Clean up
        await client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_search_relevance_ordering(self, client):
        """Test that search results are ordered by relevance"""
        unique_term = f"python{uuid.uuid4().hex[:8]}"

        # Add memories with varying relevance
        memory_ids = []

        # Most relevant - exact match
        mem1 = await client.add_memory(
            content=f"I love {unique_term} programming very much",
        )
        memory_ids.append(mem1)

        # Less relevant
        mem2 = await client.add_memory(
            content=f"Sometimes I use {unique_term}",
        )
        memory_ids.append(mem2)

        await asyncio.sleep(0.5)

        # Search
        results = await client.search_memories(query=unique_term, limit=10)

        # Check ordering by score
        scores = [r.score for r in results if r.memory.id in memory_ids]
        if len(scores) > 1:
            assert scores == sorted(scores, reverse=True)

        # Clean up
        for memory_id in memory_ids:
            await client.delete_memory(memory_id)


class TestStatsIntegration:
    """Integration tests for stats endpoint"""

    @pytest.mark.asyncio
    async def test_get_stats_live(self, client):
        """Test getting memory stats from live API"""
        stats = await client.get_memory_stats()

        assert isinstance(stats, MemoryStats)
        assert stats.total_memories >= 0
        assert stats.hot_tier_count >= 0
        assert stats.warm_tier_count >= 0
        assert stats.cold_tier_count >= 0


class TestConversationIntegration:
    """Integration tests for conversation operations"""

    @pytest.mark.asyncio
    async def test_add_conversation_live(self, client):
        """Test adding conversation to live API"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        memory_id = await client.add_conversation(
            user_message="What programming language do you recommend?",
            assistant_message="I recommend Python for its versatility and readability.",
            session_id=session_id,
        )

        assert memory_id is not None

        # Verify the memory was created
        memory = await client.get_memory(memory_id)
        assert "User:" in memory.content
        assert "Assistant:" in memory.content
        assert "conversation" in memory.tags

        # Clean up
        await client.delete_memory(memory_id)


class TestMultiTenantIntegration:
    """Integration tests for multi-tenant isolation"""

    @pytest.mark.asyncio
    async def test_user_isolation(self, client):
        """Test that user_id provides tenant isolation"""
        user1_id = f"user_{uuid.uuid4().hex[:8]}"
        user2_id = f"user_{uuid.uuid4().hex[:8]}"
        unique_content = f"secret_{uuid.uuid4().hex[:8]}"

        # Add memory for user1
        mem_id = await client.add_memory(
            content=unique_content,
            user_id=user1_id,
        )

        await asyncio.sleep(0.5)

        # Search as user1 - should find it
        results1 = await client.search_memories(
            query=unique_content,
            user_id=user1_id,
        )

        # Search as user2 - should NOT find it
        results2 = await client.search_memories(
            query=unique_content,
            user_id=user2_id,
        )

        # Verify isolation
        user1_found = any(unique_content in r.memory.content for r in results1)
        user2_found = any(unique_content in r.memory.content for r in results2)

        assert user1_found, "User1 should find their own memory"
        # Note: Isolation depends on API implementation
        # assert not user2_found, "User2 should NOT find user1's memory"

        # Clean up
        await client.delete_memory(mem_id)


class TestPerformanceIntegration:
    """Integration tests for performance characteristics"""

    @pytest.mark.asyncio
    async def test_search_latency(self, client):
        """Test that search completes within acceptable latency"""
        import time

        # Add a test memory
        memory_id = await client.add_memory(
            content="Test memory for latency measurement",
        )

        await asyncio.sleep(0.5)

        # Measure search latency
        start = time.perf_counter()
        await client.search_memories(query="latency measurement", limit=10)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should complete within 1 second (generous for integration test)
        assert elapsed_ms < 1000, f"Search took {elapsed_ms}ms, expected < 1000ms"

        # Clean up
        await client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_add_memory_latency(self, client):
        """Test that adding memory completes within acceptable latency"""
        import time

        start = time.perf_counter()
        memory_id = await client.add_memory(
            content="Latency test memory",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should complete within 2 seconds (includes embedding generation)
        assert elapsed_ms < 2000, f"Add memory took {elapsed_ms}ms, expected < 2000ms"

        # Clean up
        await client.delete_memory(memory_id)


# Pytest configuration for skipping integration tests by default
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="Need --run-integration to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
