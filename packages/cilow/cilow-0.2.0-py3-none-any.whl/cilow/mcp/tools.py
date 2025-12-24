"""MCP Tool definitions for Cilow memory operations."""

from typing import Optional, List, Dict, Any
from datetime import datetime


async def cilow_remember(
    memory_manager,
    content: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Store a memory in the Cilow system.

    Args:
        memory_manager: The MemoryManager instance
        content: The content to remember
        tags: Optional list of tags for categorization
        metadata: Optional additional metadata

    Returns:
        Dict with status and memory ID
    """
    try:
        result = await memory_manager.add_conversation_turn(
            role="user",
            content=content,
            metadata={
                "tags": tags or [],
                "source": "mcp",
                "timestamp": datetime.now().isoformat(),
                **(metadata or {}),
            }
        )
        return {
            "success": True,
            "message": "Memory stored successfully",
            "memory_id": result.get("id") if result else None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def cilow_recall(
    memory_manager,
    query: str,
    limit: int = 5,
    min_score: float = 0.3,
) -> Dict[str, Any]:
    """
    Recall memories using semantic search.

    Args:
        memory_manager: The MemoryManager instance
        query: The search query
        limit: Maximum number of results
        min_score: Minimum relevance score (0-1)

    Returns:
        Dict with search results
    """
    try:
        results = await memory_manager.search_relevant_context(
            query=query,
            limit=limit,
            min_score=min_score,
        )

        return {
            "success": True,
            "count": len(results) if results else 0,
            "memories": [
                {
                    "content": r.get("content", ""),
                    "score": r.get("score", 0),
                    "metadata": r.get("metadata", {}),
                }
                for r in (results or [])
            ],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "memories": [],
        }


async def cilow_search(
    memory_manager,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Advanced search with filters.

    Args:
        memory_manager: The MemoryManager instance
        query: The search query
        filters: Optional filters (tags, date_range, etc.)
        limit: Maximum number of results

    Returns:
        Dict with search results
    """
    try:
        # Use semantic search as base
        results = await memory_manager.search_relevant_context(
            query=query,
            limit=limit,
            min_score=0.2,
        )

        # Apply filters if provided
        if filters and results:
            filtered = []
            for r in results:
                metadata = r.get("metadata", {})

                # Filter by tags
                if "tags" in filters:
                    result_tags = metadata.get("tags", [])
                    if not any(t in result_tags for t in filters["tags"]):
                        continue

                # Filter by role
                if "role" in filters:
                    if metadata.get("role") != filters["role"]:
                        continue

                filtered.append(r)
            results = filtered

        return {
            "success": True,
            "count": len(results) if results else 0,
            "results": [
                {
                    "content": r.get("content", ""),
                    "score": r.get("score", 0),
                    "metadata": r.get("metadata", {}),
                }
                for r in (results or [])
            ],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
        }


async def cilow_get_context(
    memory_manager,
    query: str,
    max_tokens: int = 2000,
) -> Dict[str, Any]:
    """
    Build LLM-ready context from relevant memories.

    Args:
        memory_manager: The MemoryManager instance
        query: The context query
        max_tokens: Maximum context size in tokens (approximate)

    Returns:
        Dict with formatted context string
    """
    try:
        # Get search results
        search_results = await memory_manager.search_relevant_context(
            query=query,
            limit=10,
            min_score=0.3,
        )

        # Get session context
        session_memories = await memory_manager.get_session_context(limit=5)

        # Build context prompt
        context = memory_manager.build_context_prompt(
            search_results=search_results,
            session_memories=session_memories,
            max_tokens=max_tokens,
        )

        return {
            "success": True,
            "context": context,
            "sources": {
                "search_results": len(search_results) if search_results else 0,
                "session_memories": len(session_memories) if session_memories else 0,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "context": "",
        }


async def cilow_stats(memory_manager) -> Dict[str, Any]:
    """
    Get memory system statistics.

    Args:
        memory_manager: The MemoryManager instance

    Returns:
        Dict with memory statistics
    """
    try:
        # Get session context to count
        session_memories = await memory_manager.get_session_context(limit=100)

        return {
            "success": True,
            "session_id": memory_manager.session_id,
            "base_url": memory_manager.base_url,
            "session_memory_count": len(session_memories) if session_memories else 0,
            "connected": True,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "connected": False,
        }
