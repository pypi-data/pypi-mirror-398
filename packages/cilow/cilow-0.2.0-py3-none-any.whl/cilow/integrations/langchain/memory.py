"""
Cilow Memory Implementations for LangChain

Provides memory implementations backed by Cilow's semantic search
for intelligent context retrieval in LangChain chains.

Compatible with langchain-core >= 0.2.0
"""

import asyncio
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

try:
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    from pydantic import BaseModel, Field, PrivateAttr
except ImportError as e:
    raise ImportError(
        "langchain-core is required for LangChain integration. "
        "Install it with: pip install cilow[langchain]"
    ) from e

from ...client import CilowClient
from ...models import SearchResult


class CilowSemanticMemory(BaseModel):
    """
    Cilow semantic memory for intelligent context retrieval.

    Unlike traditional chat history that returns all messages, this memory
    uses Cilow's semantic search to retrieve only the most relevant memories
    based on the current input. This is ideal for:

    - Long-running conversations where context would exceed token limits
    - Multi-session agents that need to recall information across sessions
    - Knowledge-augmented agents that need relevant facts

    Example:
        ```python
        from langchain_openai import ChatOpenAI
        from langchain.chains import ConversationChain
        from cilow.integrations.langchain import CilowSemanticMemory

        memory = CilowSemanticMemory(
            user_id="user-123",
            api_key="cilow_xxx",
            memory_key="relevant_context",
            input_key="input",
            top_k=5,
        )

        chain = ConversationChain(
            llm=ChatOpenAI(),
            memory=memory
        )

        response = chain.invoke({"input": "What did we discuss about Python?"})
        ```

    Args:
        user_id: User ID for memory isolation
        session_id: Optional session ID for additional filtering
        api_key: Optional Cilow API key
        access_token: Optional JWT access token
        base_url: Cilow API server URL
        memory_key: Key in the returned dict for retrieved memories
        input_key: Key in inputs dict containing the query
        top_k: Number of memories to retrieve
        min_relevance: Minimum relevance score (0.0-1.0)
        include_metadata: Whether to include memory metadata in output
    """

    # Pydantic fields
    memory_key: str = Field(default="history")
    input_key: str = Field(default="input")
    return_messages: bool = Field(default=False)
    top_k: int = Field(default=5)
    min_relevance: float = Field(default=0.0)
    include_metadata: bool = Field(default=False)

    # Private attributes
    _user_id: Optional[str] = PrivateAttr(default=None)
    _session_id: Optional[str] = PrivateAttr(default=None)
    _api_key: Optional[str] = PrivateAttr(default=None)
    _access_token: Optional[str] = PrivateAttr(default=None)
    _base_url: str = PrivateAttr(default="http://localhost:8080")

    def __init__(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "http://localhost:8080",
        memory_key: str = "history",
        input_key: str = "input",
        top_k: int = 5,
        min_relevance: float = 0.0,
        include_metadata: bool = False,
        return_messages: bool = False,
        **kwargs: Any,
    ):
        super().__init__(
            memory_key=memory_key,
            input_key=input_key,
            top_k=top_k,
            min_relevance=min_relevance,
            include_metadata=include_metadata,
            return_messages=return_messages,
            **kwargs,
        )
        self._user_id = user_id
        self._session_id = session_id
        self._api_key = api_key
        self._access_token = access_token
        self._base_url = base_url

    def _get_client(self) -> CilowClient:
        """Create a new client instance."""
        return CilowClient(
            base_url=self._base_url,
            api_key=self._api_key,
            access_token=self._access_token,
        )

    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]

    def _format_memories(self, results: List[SearchResult]) -> str:
        """Format search results as a string context."""
        if not results:
            return ""

        formatted = []
        for result in results:
            memory = result.memory
            content = memory.content or ""

            if self.include_metadata:
                meta_str = ""
                if memory.tags:
                    meta_str += f" [tags: {', '.join(memory.tags)}]"
                if memory.created_at:
                    meta_str += f" [created: {memory.created_at}]"
                formatted.append(f"- {content}{meta_str}")
            else:
                formatted.append(f"- {content}")

        return "\n".join(formatted)

    def _format_as_messages(self, results: List[SearchResult]) -> List[BaseMessage]:
        """Format search results as LangChain messages."""
        messages: List[BaseMessage] = []

        for result in results:
            memory = result.memory
            content = memory.content or ""

            # Determine role from tags/metadata
            role = "human"
            if memory.tags:
                for tag in memory.tags:
                    if "role:ai" in tag or "role:assistant" in tag:
                        role = "ai"
                        break

            if memory.metadata and "role" in memory.metadata:
                role_value = memory.metadata["role"]
                if role_value in ("ai", "assistant"):
                    role = "ai"

            if role == "ai":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

        return messages

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search relevant memories based on current input.

        Args:
            inputs: Dictionary containing the input_key with query

        Returns:
            Dictionary with memory_key containing relevant context
        """
        query = inputs.get(self.input_key, "")
        if not query:
            return {self.memory_key: "" if not self.return_messages else []}

        async def _search() -> List[SearchResult]:
            async with self._get_client() as client:
                tags = None
                if self._session_id:
                    tags = [f"session:{self._session_id}"]

                return await client.search_memories(
                    query=query,
                    limit=self.top_k,
                    min_relevance=self.min_relevance,
                    user_id=self._user_id,
                    tags=tags,
                )

        results = asyncio.run(_search())

        if self.return_messages:
            return {self.memory_key: self._format_as_messages(results)}
        return {self.memory_key: self._format_memories(results)}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save interaction to Cilow.

        Args:
            inputs: Input dictionary with user message
            outputs: Output dictionary with assistant response
        """
        user_message = inputs.get(self.input_key, "")
        assistant_message = outputs.get("output", outputs.get("response", ""))

        if not user_message and not assistant_message:
            return

        async def _save():
            async with self._get_client() as client:
                # Save as a conversation turn
                await client.add_conversation(
                    user_message=user_message,
                    assistant_message=assistant_message,
                    session_id=self._session_id,
                    metadata={
                        "source": "langchain",
                        "memory_type": "semantic",
                    },
                )

        asyncio.run(_save())

    def clear(self) -> None:
        """
        Clear memories for this user/session.

        Note: This only clears memories tagged with 'langchain' to avoid
        deleting other application data.
        """

        async def _clear():
            async with self._get_client() as client:
                tags = ["langchain"]
                if self._session_id:
                    tags.append(f"session:{self._session_id}")

                memories = await client.list_memories(
                    tags=tags,
                    user_id=self._user_id,
                    limit=10000,
                )

                for memory in memories:
                    if memory.id:
                        try:
                            await client.delete_memory(memory.id)
                        except Exception:
                            pass

        asyncio.run(_clear())


class CilowConversationMemory(BaseModel):
    """
    Cilow conversation memory that combines recent history with semantic search.

    This memory provides a sliding window of recent messages plus semantically
    relevant older context. Ideal for conversations that need both immediate
    context and long-term recall.

    Example:
        ```python
        from cilow.integrations.langchain import CilowConversationMemory

        memory = CilowConversationMemory(
            session_id="user-123-session-1",
            api_key="cilow_xxx",
            recent_k=5,      # Last 5 messages
            semantic_k=3,    # Plus 3 relevant older memories
        )
        ```

    Args:
        session_id: Session ID for conversation tracking
        user_id: Optional user ID for isolation
        api_key: Optional Cilow API key
        access_token: Optional JWT access token
        base_url: Cilow API server URL
        memory_key: Key for the returned context
        input_key: Key for the input query
        recent_k: Number of recent messages to include
        semantic_k: Number of semantically relevant memories to include
    """

    memory_key: str = Field(default="history")
    input_key: str = Field(default="input")
    return_messages: bool = Field(default=False)
    recent_k: int = Field(default=5)
    semantic_k: int = Field(default=3)

    _session_id: str = PrivateAttr()
    _user_id: Optional[str] = PrivateAttr(default=None)
    _api_key: Optional[str] = PrivateAttr(default=None)
    _access_token: Optional[str] = PrivateAttr(default=None)
    _base_url: str = PrivateAttr(default="http://localhost:8080")

    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "http://localhost:8080",
        memory_key: str = "history",
        input_key: str = "input",
        recent_k: int = 5,
        semantic_k: int = 3,
        return_messages: bool = False,
        **kwargs: Any,
    ):
        super().__init__(
            memory_key=memory_key,
            input_key=input_key,
            recent_k=recent_k,
            semantic_k=semantic_k,
            return_messages=return_messages,
            **kwargs,
        )
        self._session_id = session_id
        self._user_id = user_id
        self._api_key = api_key
        self._access_token = access_token
        self._base_url = base_url

    def _get_client(self) -> CilowClient:
        """Create a new client instance."""
        return CilowClient(
            base_url=self._base_url,
            api_key=self._api_key,
            access_token=self._access_token,
        )

    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load both recent messages and semantically relevant context.

        Args:
            inputs: Dictionary containing the input_key with query

        Returns:
            Dictionary with memory_key containing combined context
        """
        query = inputs.get(self.input_key, "")

        async def _load():
            async with self._get_client() as client:
                # Get recent messages
                recent_memories = await client.list_memories(
                    tags=[f"session:{self._session_id}"],
                    user_id=self._user_id,
                    limit=self.recent_k,
                )

                # Sort by created_at descending (most recent first)
                recent_sorted = sorted(
                    recent_memories,
                    key=lambda m: m.created_at or "",
                    reverse=True,
                )[: self.recent_k]

                # Get semantically relevant memories (if query provided)
                semantic_results: List[SearchResult] = []
                if query and self.semantic_k > 0:
                    # Exclude recent message IDs to avoid duplication
                    recent_ids = {m.id for m in recent_sorted if m.id}

                    all_results = await client.search_memories(
                        query=query,
                        limit=self.semantic_k + len(recent_ids),
                        user_id=self._user_id,
                    )

                    # Filter out recent messages
                    semantic_results = [
                        r
                        for r in all_results
                        if r.memory.id not in recent_ids
                    ][: self.semantic_k]

                return recent_sorted, semantic_results

        recent, semantic = asyncio.run(_load())

        # Format combined context
        lines = []

        if semantic:
            lines.append("Relevant context from previous conversations:")
            for result in semantic:
                content = result.memory.content or ""
                lines.append(f"  - {content}")
            lines.append("")

        if recent:
            lines.append("Recent conversation:")
            # Reverse to chronological order
            for memory in reversed(recent):
                content = memory.content or ""
                lines.append(f"  {content}")

        return {self.memory_key: "\n".join(lines)}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save interaction to Cilow."""
        user_message = inputs.get(self.input_key, "")
        assistant_message = outputs.get("output", outputs.get("response", ""))

        if not user_message and not assistant_message:
            return

        async def _save():
            async with self._get_client() as client:
                await client.add_conversation(
                    user_message=user_message,
                    assistant_message=assistant_message,
                    session_id=self._session_id,
                    metadata={
                        "source": "langchain",
                        "memory_type": "conversation",
                    },
                )

        asyncio.run(_save())

    def clear(self) -> None:
        """Clear conversation history for this session."""

        async def _clear():
            async with self._get_client() as client:
                memories = await client.list_memories(
                    tags=[f"session:{self._session_id}"],
                    user_id=self._user_id,
                    limit=10000,
                )

                for memory in memories:
                    if memory.id:
                        try:
                            await client.delete_memory(memory.id)
                        except Exception:
                            pass

        asyncio.run(_clear())
