"""
Cilow SDK Pydantic Models
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class MemoryTier(str, Enum):
    """Memory storage tier"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class FactType(str, Enum):
    """Type of extracted fact"""
    PERSONAL = "Personal"
    PREFERENCE = "Preference"
    SKILL = "Skill"
    GOAL = "Goal"
    RELATIONSHIP = "Relationship"
    CONTEXTUAL = "Contextual"
    TEMPORAL = "Temporal"
    CAUSAL = "Causal"


class EntityType(str, Enum):
    """Type of entity"""
    PERSON = "Person"
    PLACE = "Place"
    ORGANIZATION = "Organization"
    OBJECT = "Object"
    CONCEPT = "Concept"
    EVENT = "Event"
    TIME = "Time"
    SKILL = "Skill"
    PREFERENCE = "Preference"


class Entity(BaseModel):
    """Entity extracted from memory content"""
    name: str = Field(..., description="Entity name or identifier")
    entity_type: EntityType = Field(..., description="Type of entity")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score")
    attributes: Dict[str, str] = Field(default_factory=dict, description="Additional attributes")

    class Config:
        use_enum_values = True


class Relationship(BaseModel):
    """Relationship between entities"""
    source: str = Field(..., description="Source entity name")
    relationship_type: str = Field(..., description="Type of relationship")
    target: str = Field(..., description="Target entity name")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score")
    context: Optional[str] = Field(None, description="Additional context")


class ExtractedFact(BaseModel):
    """Fact extracted from conversation content"""
    id: str = Field(..., description="Unique fact identifier")
    statement: str = Field(..., description="The factual statement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    fact_type: FactType = Field(..., description="Type of fact")
    entities: List[Entity] = Field(default_factory=list, description="Entities in this fact")
    relationships: List[Relationship] = Field(default_factory=list, description="Relationships")
    extracted_at: Optional[datetime] = Field(None, description="Extraction timestamp")

    class Config:
        use_enum_values = True


class Memory(BaseModel):
    """Represents a memory in the Cilow system"""
    id: Optional[str] = Field(None, description="Unique memory identifier")
    content: Optional[str] = Field(None, description="Memory content")
    compressed_content: Optional[str] = Field(None, description="Compressed content from API")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    tier: MemoryTier = Field(default=MemoryTier.HOT, description="Storage tier")
    salience: float = Field(default=1.0, ge=0.0, description="Memory salience/importance")
    access_count: int = Field(default=0, ge=0, description="Number of times accessed")
    tags: List[str] = Field(default_factory=list, description="Memory tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    facts: List[ExtractedFact] = Field(default_factory=list, description="Extracted facts")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    user_id: Optional[str] = Field(None, description="User ID for multi-tenant")

    @validator("tier", pre=True)
    def normalize_tier(cls, v):
        """Handle case-insensitive tier values from API"""
        if isinstance(v, str):
            return v.lower()
        return v

    @property
    def text(self) -> str:
        """Return content or compressed_content"""
        return self.content or self.compressed_content or ""

    class Config:
        use_enum_values = True

    @validator('created_at', pre=True)
    def parse_created_at(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

    @validator('updated_at', pre=True)
    def parse_updated_at(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class MemoryStats(BaseModel):
    """Memory system statistics"""
    total_memories: int = Field(..., ge=0, description="Total memory count")
    hot_tier_count: int = Field(default=0, ge=0, description="Hot tier count")
    warm_tier_count: int = Field(default=0, ge=0, description="Warm tier count")
    cold_tier_count: int = Field(default=0, ge=0, description="Cold tier count")
    avg_salience: float = Field(default=0.0, ge=0.0, description="Average salience")
    total_tokens: int = Field(default=0, ge=0, description="Total tokens stored")
    total_embeddings: int = Field(default=0, ge=0, description="Total embeddings stored")


class SearchResult(BaseModel):
    """Memory search result with relevance score"""
    memory: Memory = Field(..., description="The matched memory")
    score: float = Field(..., ge=0.0, description="Relevance score (can be > 1 for boosted results)")
    rank: int = Field(default=1, ge=1, description="Result rank")


class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(default="react", description="Agent type (react, chain_of_note)")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=2000, ge=1, description="Max response tokens")
    context_limit: int = Field(default=4000, ge=1, description="Context window limit")


class Agent(BaseModel):
    """AI Agent instance"""
    id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    created_at: datetime = Field(..., description="Creation timestamp")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")


class AgentExecutionResult(BaseModel):
    """Result from agent task execution"""
    success: bool = Field(..., description="Whether execution succeeded")
    response: str = Field(..., description="Agent response")
    reasoning: Optional[str] = Field(None, description="Agent reasoning trace")
    memories_used: List[str] = Field(default_factory=list, description="Memory IDs used")
    tokens_used: int = Field(default=0, ge=0, description="Tokens consumed")
    execution_time_ms: int = Field(default=0, ge=0, description="Execution time in ms")


class HealthStatus(BaseModel):
    """API health status"""
    status: str = Field(..., description="Health status")
    version: str = Field(default="unknown", description="API version")
    uptime_seconds: int = Field(default=0, ge=0, description="Server uptime")
    memory_usage_mb: float = Field(default=0.0, ge=0.0, description="Memory usage in MB")


# ==============================================================================
# Authentication Models
# ==============================================================================


class User(BaseModel):
    """Authenticated user information"""
    id: str = Field(..., description="User identifier")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    email_verified: bool = Field(default=False, description="Email verified status")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")

    @validator('created_at', pre=True)
    def parse_created_at(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class AuthResponse(BaseModel):
    """Authentication response with tokens"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    user: User = Field(..., description="Authenticated user")


class ApiKey(BaseModel):
    """API key information"""
    key_id: str = Field(..., alias="id", description="API key identifier")
    name: str = Field(..., description="API key name")
    key: Optional[str] = Field(None, description="API key value (only shown once)")
    permissions: List[str] = Field(default_factory=list, description="Key permissions")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    ip_whitelist: List[str] = Field(default_factory=list, description="IP whitelist")
    is_active: bool = Field(default=True, description="Whether the key is active")

    class Config:
        populate_by_name = True

    @validator('created_at', 'expires_at', 'last_used_at', pre=True)
    def parse_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class Session(BaseModel):
    """User session information"""
    session_id: str = Field(..., description="Session identifier")
    device_info: Optional[str] = Field(None, description="Device information")
    ip_address: Optional[str] = Field(None, description="IP address")
    created_at: Optional[datetime] = Field(None, description="Session creation time")
    last_active_at: Optional[datetime] = Field(None, description="Last activity time")

    @validator('created_at', 'last_active_at', pre=True)
    def parse_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
