"""
Unit tests for Pydantic models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError as PydanticValidationError

from cilow.models import (
    Memory,
    MemoryTier,
    MemoryStats,
    SearchResult,
    HealthStatus,
    AgentConfig,
    Agent,
    AgentExecutionResult,
    ExtractedFact,
    FactType,
    Entity,
    EntityType,
    Relationship,
)


class TestMemoryModel:
    """Tests for Memory model"""

    def test_memory_creation_minimal(self):
        """Test creating memory with minimal fields"""
        memory = Memory(
            id="mem_123",
            content="Test content",
            created_at=datetime.now(),
        )
        assert memory.id == "mem_123"
        assert memory.content == "Test content"
        assert memory.tier == MemoryTier.HOT  # default
        assert memory.salience == 1.0  # default
        assert memory.access_count == 0  # default
        assert memory.tags == []  # default
        assert memory.metadata == {}  # default

    def test_memory_creation_full(self):
        """Test creating memory with all fields"""
        now = datetime.now()
        memory = Memory(
            id="mem_456",
            content="Full memory content",
            created_at=now,
            updated_at=now,
            tier=MemoryTier.WARM,
            salience=0.85,
            access_count=10,
            tags=["important", "work"],
            metadata={"source": "conversation", "session_id": "sess_123"},
            facts=[],
            embedding=[0.1] * 10,
        )
        assert memory.id == "mem_456"
        assert memory.tier == MemoryTier.WARM
        assert memory.salience == 0.85
        assert memory.access_count == 10
        assert len(memory.tags) == 2
        assert "source" in memory.metadata

    def test_memory_from_iso_datetime(self):
        """Test parsing ISO datetime strings"""
        memory = Memory(
            id="mem_789",
            content="Test",
            created_at="2024-01-15T10:30:00Z",
        )
        assert isinstance(memory.created_at, datetime)
        assert memory.created_at.year == 2024

    def test_memory_from_iso_datetime_with_timezone(self):
        """Test parsing ISO datetime with timezone"""
        memory = Memory(
            id="mem_abc",
            content="Test",
            created_at="2024-01-15T10:30:00+00:00",
        )
        assert isinstance(memory.created_at, datetime)

    def test_memory_invalid_salience(self):
        """Test that invalid salience raises error"""
        with pytest.raises(PydanticValidationError):
            Memory(
                id="mem_bad",
                content="Test",
                created_at=datetime.now(),
                salience=-0.5,  # Invalid: must be >= 0
            )

    def test_memory_invalid_access_count(self):
        """Test that negative access count raises error"""
        with pytest.raises(PydanticValidationError):
            Memory(
                id="mem_bad",
                content="Test",
                created_at=datetime.now(),
                access_count=-1,  # Invalid: must be >= 0
            )


class TestMemoryTier:
    """Tests for MemoryTier enum"""

    def test_tier_values(self):
        """Test tier enum values"""
        assert MemoryTier.HOT.value == "hot"
        assert MemoryTier.WARM.value == "warm"
        assert MemoryTier.COLD.value == "cold"

    def test_tier_from_string(self):
        """Test creating tier from string"""
        memory = Memory(
            id="test",
            content="test",
            created_at=datetime.now(),
            tier="warm",
        )
        assert memory.tier == MemoryTier.WARM


class TestMemoryStats:
    """Tests for MemoryStats model"""

    def test_stats_creation(self):
        """Test creating memory stats"""
        stats = MemoryStats(
            total_memories=100,
            hot_tier_count=30,
            warm_tier_count=50,
            cold_tier_count=20,
            avg_salience=0.75,
            total_tokens=50000,
            total_embeddings=100,
        )
        assert stats.total_memories == 100
        assert stats.hot_tier_count + stats.warm_tier_count + stats.cold_tier_count == 100

    def test_stats_defaults(self):
        """Test stats with defaults"""
        stats = MemoryStats(total_memories=50)
        assert stats.hot_tier_count == 0
        assert stats.avg_salience == 0.0

    def test_stats_invalid_negative(self):
        """Test that negative counts raise error"""
        with pytest.raises(PydanticValidationError):
            MemoryStats(total_memories=-1)


class TestSearchResult:
    """Tests for SearchResult model"""

    def test_search_result_creation(self):
        """Test creating search result"""
        memory = Memory(
            id="mem_123",
            content="Test",
            created_at=datetime.now(),
        )
        result = SearchResult(
            memory=memory,
            score=0.95,
            rank=1,
        )
        assert result.score == 0.95
        assert result.rank == 1
        assert result.memory.id == "mem_123"

    def test_search_result_score_bounds(self):
        """Test score must be between 0 and 1"""
        memory = Memory(
            id="test",
            content="test",
            created_at=datetime.now(),
        )
        with pytest.raises(PydanticValidationError):
            SearchResult(memory=memory, score=1.5, rank=1)

        with pytest.raises(PydanticValidationError):
            SearchResult(memory=memory, score=-0.1, rank=1)

    def test_search_result_rank_positive(self):
        """Test rank must be positive"""
        memory = Memory(
            id="test",
            content="test",
            created_at=datetime.now(),
        )
        with pytest.raises(PydanticValidationError):
            SearchResult(memory=memory, score=0.5, rank=0)


class TestHealthStatus:
    """Tests for HealthStatus model"""

    def test_health_creation(self):
        """Test creating health status"""
        health = HealthStatus(
            status="healthy",
            version="0.1.0",
            uptime_seconds=3600,
            memory_usage_mb=256.5,
        )
        assert health.status == "healthy"
        assert health.version == "0.1.0"
        assert health.uptime_seconds == 3600

    def test_health_defaults(self):
        """Test health with defaults"""
        health = HealthStatus(status="healthy")
        assert health.version == "unknown"
        assert health.uptime_seconds == 0


class TestAgentConfig:
    """Tests for AgentConfig model"""

    def test_agent_config_creation(self):
        """Test creating agent config"""
        config = AgentConfig(
            name="assistant",
            agent_type="react",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2000,
            context_limit=4000,
        )
        assert config.name == "assistant"
        assert config.agent_type == "react"

    def test_agent_config_defaults(self):
        """Test agent config defaults"""
        config = AgentConfig(name="test")
        assert config.agent_type == "react"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7

    def test_agent_config_temperature_bounds(self):
        """Test temperature bounds"""
        with pytest.raises(PydanticValidationError):
            AgentConfig(name="test", temperature=2.5)  # Max is 2.0


class TestAgent:
    """Tests for Agent model"""

    def test_agent_creation(self):
        """Test creating agent"""
        agent = Agent(
            id="agent_123",
            name="assistant",
            agent_type="react",
            created_at=datetime.now(),
        )
        assert agent.id == "agent_123"
        assert agent.name == "assistant"


class TestAgentExecutionResult:
    """Tests for AgentExecutionResult model"""

    def test_execution_result_success(self):
        """Test successful execution result"""
        result = AgentExecutionResult(
            success=True,
            response="Here's the answer based on your memories.",
            reasoning="Found relevant context in memories.",
            memories_used=["mem_123", "mem_456"],
            tokens_used=150,
            execution_time_ms=250,
        )
        assert result.success is True
        assert len(result.memories_used) == 2
        assert result.tokens_used == 150

    def test_execution_result_failure(self):
        """Test failed execution result"""
        result = AgentExecutionResult(
            success=False,
            response="Unable to complete task.",
        )
        assert result.success is False
        assert result.reasoning is None
        assert result.memories_used == []


class TestEntity:
    """Tests for Entity model"""

    def test_entity_creation(self):
        """Test creating entity"""
        entity = Entity(
            name="Python",
            entity_type=EntityType.CONCEPT,
            confidence=0.95,
            attributes={"category": "programming language"},
        )
        assert entity.name == "Python"
        assert entity.entity_type == EntityType.CONCEPT
        assert entity.confidence == 0.95

    def test_entity_defaults(self):
        """Test entity defaults"""
        entity = Entity(
            name="Test",
            entity_type=EntityType.OBJECT,
        )
        assert entity.confidence == 0.8  # default
        assert entity.attributes == {}

    def test_entity_confidence_bounds(self):
        """Test confidence must be 0-1"""
        with pytest.raises(PydanticValidationError):
            Entity(
                name="Test",
                entity_type=EntityType.PERSON,
                confidence=1.5,
            )


class TestRelationship:
    """Tests for Relationship model"""

    def test_relationship_creation(self):
        """Test creating relationship"""
        rel = Relationship(
            source="User",
            relationship_type="LIKES",
            target="Python",
            confidence=0.9,
            context="Based on conversation about programming preferences",
        )
        assert rel.source == "User"
        assert rel.relationship_type == "LIKES"
        assert rel.target == "Python"


class TestExtractedFact:
    """Tests for ExtractedFact model"""

    def test_fact_creation(self):
        """Test creating extracted fact"""
        fact = ExtractedFact(
            id="fact_123",
            statement="User prefers Python for web development",
            confidence=0.92,
            fact_type=FactType.PREFERENCE,
            entities=[
                Entity(name="User", entity_type=EntityType.PERSON),
                Entity(name="Python", entity_type=EntityType.CONCEPT),
            ],
            relationships=[
                Relationship(
                    source="User",
                    relationship_type="PREFERS",
                    target="Python",
                )
            ],
        )
        assert fact.id == "fact_123"
        assert fact.fact_type == FactType.PREFERENCE
        assert len(fact.entities) == 2
        assert len(fact.relationships) == 1

    def test_fact_types(self):
        """Test all fact types exist"""
        assert FactType.PERSONAL.value == "Personal"
        assert FactType.PREFERENCE.value == "Preference"
        assert FactType.SKILL.value == "Skill"
        assert FactType.GOAL.value == "Goal"
        assert FactType.RELATIONSHIP.value == "Relationship"
        assert FactType.CONTEXTUAL.value == "Contextual"
        assert FactType.TEMPORAL.value == "Temporal"
        assert FactType.CAUSAL.value == "Causal"


class TestEntityTypes:
    """Tests for EntityType enum"""

    def test_all_entity_types(self):
        """Test all entity types exist"""
        assert EntityType.PERSON.value == "Person"
        assert EntityType.PLACE.value == "Place"
        assert EntityType.ORGANIZATION.value == "Organization"
        assert EntityType.OBJECT.value == "Object"
        assert EntityType.CONCEPT.value == "Concept"
        assert EntityType.EVENT.value == "Event"
        assert EntityType.TIME.value == "Time"
        assert EntityType.SKILL.value == "Skill"
        assert EntityType.PREFERENCE.value == "Preference"


class TestModelSerialization:
    """Tests for model serialization"""

    def test_memory_to_dict(self):
        """Test memory can be converted to dict"""
        memory = Memory(
            id="mem_123",
            content="Test content",
            created_at=datetime.now(),
            tags=["test"],
        )
        data = memory.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == "mem_123"
        assert data["content"] == "Test content"

    def test_memory_to_json(self):
        """Test memory can be converted to JSON"""
        memory = Memory(
            id="mem_123",
            content="Test content",
            created_at=datetime.now(),
        )
        json_str = memory.model_dump_json()
        assert isinstance(json_str, str)
        assert "mem_123" in json_str

    def test_search_result_nested_serialization(self):
        """Test nested model serialization"""
        memory = Memory(
            id="mem_123",
            content="Test",
            created_at=datetime.now(),
        )
        result = SearchResult(memory=memory, score=0.9, rank=1)
        data = result.model_dump()
        assert isinstance(data["memory"], dict)
        assert data["memory"]["id"] == "mem_123"
