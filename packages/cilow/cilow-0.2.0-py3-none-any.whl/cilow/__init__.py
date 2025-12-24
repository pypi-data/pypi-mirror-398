"""
Cilow Python SDK
High-level async Python client for the Cilow AI Agent Platform
"""

from .client import (
    CilowClient,
    add_memory_sync,
    search_memories_sync,
    get_memory_stats_sync,
    register_sync,
    login_sync,
)

from .models import (
    # Enums
    MemoryTier,
    FactType,
    EntityType,
    # Models
    Entity,
    Relationship,
    ExtractedFact,
    Memory,
    MemoryStats,
    SearchResult,
    AgentConfig,
    Agent,
    AgentExecutionResult,
    HealthStatus,
    # Auth Models
    User,
    AuthResponse,
    ApiKey,
    Session,
)

from .errors import (
    CilowError,
    ConnectionError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)

__version__ = "0.1.0"
__all__ = [
    # Client
    "CilowClient",
    "add_memory_sync",
    "search_memories_sync",
    "get_memory_stats_sync",
    "register_sync",
    "login_sync",
    # Enums
    "MemoryTier",
    "FactType",
    "EntityType",
    # Models
    "Entity",
    "Relationship",
    "ExtractedFact",
    "Memory",
    "MemoryStats",
    "SearchResult",
    "AgentConfig",
    "Agent",
    "AgentExecutionResult",
    "HealthStatus",
    # Auth Models
    "User",
    "AuthResponse",
    "ApiKey",
    "Session",
    # Errors
    "CilowError",
    "ConnectionError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
]
