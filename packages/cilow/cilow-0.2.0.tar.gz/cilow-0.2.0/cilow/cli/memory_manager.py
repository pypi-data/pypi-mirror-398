"""
Memory Manager for Cilow Chatbot

Wraps CilowClient operations with chatbot-specific functionality.
Cilow handles all extraction, tagging, and graph building automatically.
"""

from typing import List, Optional, Callable, Any
from datetime import datetime

from ..client import CilowClient
from ..models import Memory, SearchResult, MemoryStats


class MemoryManager:
    """
    Manages memory operations for the chatbot.

    Cilow's backend automatically handles:
    - Entity extraction (Person, Place, Organization, etc.)
    - Relationship extraction (LIKES, WORKS_AT, PLANS, etc.)
    - Auto-tagging (preference, trip, coding, etc.)
    - Knowledge graph construction
    - MemoryRank scoring
    - Multi-tier storage (Hot/Warm/Cold)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        session_id: Optional[str] = None,
        on_memory_add: Optional[Callable[[str], None]] = None,
        on_search: Optional[Callable[[str, int], None]] = None,
        on_extraction: Optional[Callable[[int, int], None]] = None,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.access_token = access_token
        self.session_id = session_id or datetime.now().strftime("%Y%m%d-%H%M%S")

        # Callbacks for UI updates
        self.on_memory_add = on_memory_add
        self.on_search = on_search
        self.on_extraction = on_extraction

        self._client: Optional[CilowClient] = None

    def _get_client(self) -> CilowClient:
        """Get or create client instance."""
        if self._client is None:
            self._client = CilowClient(
                base_url=self.base_url,
                api_key=self.api_key,
                access_token=self.access_token,
            )
        return self._client

    async def __aenter__(self):
        """Async context manager entry."""
        client = self._get_client()
        await client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    async def add_conversation_turn(
        self,
        role: str,
        content: str,
        extra_tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store a conversation turn as a memory.

        Cilow automatically:
        - Extracts entities (Person, Place, Organization, etc.)
        - Identifies relationships
        - Auto-tags based on content analysis
        - Updates the knowledge graph
        - Calculates MemoryRank scores

        Args:
            role: "user" or "assistant"
            content: Message content
            extra_tags: Additional tags to add

        Returns:
            Memory ID
        """
        client = self._get_client()

        # Build tags - Cilow adds more automatically via KV extraction
        tags = [
            f"session:{self.session_id}",
            f"role:{role}",
            "source:chatbot",
            "type:conversation",
        ]
        if extra_tags:
            tags.extend(extra_tags)

        # Add memory - Cilow handles extraction automatically
        memory_id = await client.add_memory(
            content=content,
            tags=tags,
            metadata={
                "role": role,
                "session_id": self.session_id,
                "source": "chatbot",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Notify callback
        if self.on_memory_add:
            self.on_memory_add(memory_id)

        return memory_id

    async def search_relevant_context(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.3,
    ) -> List[SearchResult]:
        """
        Search for relevant memories using Cilow's hybrid retrieval.

        Cilow uses:
        - HNSW vector search (dense embeddings)
        - BM25 keyword search (sparse)
        - Graph traversal (entity relationships)
        - Reciprocal Rank Fusion (RRF) for score merging
        - MemoryRank for salience-based ranking

        Args:
            query: Search query
            limit: Maximum results
            min_score: Minimum relevance score

        Returns:
            List of SearchResult objects
        """
        client = self._get_client()

        results = await client.search_memories(
            query=query,
            limit=limit,
        )

        # Filter by minimum score
        filtered = [r for r in results if r.score >= min_score]

        # Notify callback
        if self.on_search:
            self.on_search(query, len(filtered))

        return filtered

    async def get_session_context(
        self,
        limit: int = 10,
    ) -> List[Memory]:
        """
        Get recent memories from current session for context.

        Returns:
            List of Memory objects from current session
        """
        client = self._get_client()

        memories = await client.list_memories(
            tags=[f"session:{self.session_id}"],
            limit=limit,
        )

        # Sort by creation time (newest first)
        sorted_memories = sorted(
            memories,
            key=lambda m: m.created_at or datetime.min,
            reverse=True,
        )

        return sorted_memories

    async def get_recent_memories(
        self,
        limit: int = 20,
    ) -> List[Memory]:
        """
        Get recent memories across all sessions.

        Returns:
            List of Memory objects
        """
        client = self._get_client()
        return await client.list_memories(limit=limit)

    async def get_memory_stats(self) -> MemoryStats:
        """
        Get memory system statistics.

        Returns:
            MemoryStats object
        """
        client = self._get_client()
        return await client.get_memory_stats()

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.

        Args:
            memory_id: Memory ID to delete

        Returns:
            True if deleted
        """
        client = self._get_client()
        return await client.delete_memory(memory_id)

    async def clear_session(self) -> int:
        """
        Clear all memories from current session.

        Returns:
            Number of memories deleted
        """
        client = self._get_client()

        memories = await client.list_memories(
            tags=[f"session:{self.session_id}"],
            limit=10000,
        )

        deleted = 0
        for memory in memories:
            if memory.id:
                try:
                    await client.delete_memory(memory.id)
                    deleted += 1
                except Exception:
                    pass

        return deleted

    def build_context_prompt(
        self,
        search_results: List[SearchResult],
        session_memories: List[Memory],
        max_tokens: int = 2000,
    ) -> str:
        """
        Build context prompt from retrieved memories.

        Uses FRR (Frequency-Recency-Relevance) paging to stay within
        token budget while maximizing relevant context.

        Args:
            search_results: Results from semantic search
            session_memories: Recent session memories
            max_tokens: Maximum tokens for context

        Returns:
            Formatted context string
        """
        context_parts = []
        estimated_tokens = 0

        # Add relevant memories from search
        if search_results:
            context_parts.append("## Relevant Context")
            for result in search_results:
                memory_text = result.memory.text
                # Rough token estimate: ~4 chars per token
                tokens = len(memory_text) // 4

                if estimated_tokens + tokens > max_tokens * 0.7:
                    break

                score_str = f"(relevance: {result.score:.2f})"
                context_parts.append(f"- {memory_text} {score_str}")
                estimated_tokens += tokens

        # Add recent conversation context
        if session_memories and estimated_tokens < max_tokens:
            context_parts.append("\n## Recent Conversation")
            for memory in session_memories[:5]:
                memory_text = memory.text
                tokens = len(memory_text) // 4

                if estimated_tokens + tokens > max_tokens:
                    break

                role = "User" if "role:user" in (memory.tags or []) else "Assistant"
                context_parts.append(f"- {role}: {memory_text[:200]}")
                estimated_tokens += tokens

        return "\n".join(context_parts) if context_parts else ""

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate (~4 chars per token)."""
        return len(text) // 4
