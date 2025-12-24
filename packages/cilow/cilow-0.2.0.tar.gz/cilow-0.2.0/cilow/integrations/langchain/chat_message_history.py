"""
Cilow Chat Message History for LangChain

Implements LangChain's BaseChatMessageHistory interface backed by Cilow's
memory system with semantic search and entity extraction.
"""

import asyncio
from typing import List, Optional, Sequence

try:
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
except ImportError as e:
    raise ImportError(
        "langchain-core is required for LangChain integration. "
        "Install it with: pip install cilow[langchain]"
    ) from e

from ...client import CilowClient
from ...models import Memory


class CilowChatMessageHistory(BaseChatMessageHistory):
    """
    Cilow-backed chat message history for LangChain.

    Stores chat messages as memories in Cilow with automatic entity extraction
    and semantic indexing. Messages are tagged by session and role for easy
    retrieval.

    Example:
        ```python
        from cilow.integrations.langchain import CilowChatMessageHistory

        history = CilowChatMessageHistory(
            session_id="user-123-session-1",
            api_key="cilow_xxx"
        )

        # Add messages
        history.add_user_message("What is Python?")
        history.add_ai_message("Python is a programming language...")

        # Get all messages
        messages = history.messages

        # Clear history
        history.clear()
        ```

    Args:
        session_id: Unique identifier for the conversation session
        user_id: Optional user ID for multi-tenant isolation
        api_key: Optional Cilow API key
        access_token: Optional JWT access token
        base_url: Cilow API server URL (default: http://localhost:8080)
    """

    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "http://localhost:8080",
    ):
        self.session_id = session_id
        self.user_id = user_id
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

    def _memory_to_message(self, memory: Memory) -> BaseMessage:
        """Convert a Cilow memory to a LangChain message."""
        content = memory.content or ""
        role = "human"  # default

        # Determine role from tags
        if memory.tags:
            for tag in memory.tags:
                if tag == "role:human" or tag == "role:user":
                    role = "human"
                    break
                elif tag == "role:ai" or tag == "role:assistant":
                    role = "ai"
                    break
                elif tag == "role:system":
                    role = "system"
                    break

        # Also check metadata
        if memory.metadata and "role" in memory.metadata:
            role = memory.metadata["role"]
            if role in ("user", "human"):
                role = "human"
            elif role in ("ai", "assistant"):
                role = "ai"

        if role == "human":
            return HumanMessage(content=content)
        elif role == "ai":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        else:
            return HumanMessage(content=content)

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Retrieve all messages from Cilow for this session.

        Messages are returned in chronological order (oldest first).
        """

        async def _get_messages() -> List[BaseMessage]:
            async with self._get_client() as client:
                memories = await client.list_memories(
                    tags=[f"session:{self.session_id}"],
                    user_id=self.user_id,
                    limit=1000,  # Reasonable limit for a session
                )
                # Sort by created_at if available
                sorted_memories = sorted(
                    memories,
                    key=lambda m: m.created_at or "",
                )
                return [self._memory_to_message(m) for m in sorted_memories]

        return asyncio.run(_get_messages())

    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to Cilow.

        Args:
            message: LangChain message to add
        """

        async def _add_message():
            async with self._get_client() as client:
                # Determine role tag
                if isinstance(message, HumanMessage):
                    role = "human"
                elif isinstance(message, AIMessage):
                    role = "ai"
                elif isinstance(message, SystemMessage):
                    role = "system"
                else:
                    role = "unknown"

                tags = [
                    f"session:{self.session_id}",
                    f"role:{role}",
                    "source:langchain",
                    "type:chat-history",
                ]

                await client.add_memory(
                    content=str(message.content),
                    tags=tags,
                    user_id=self.user_id,
                    metadata={
                        "role": role,
                        "session_id": self.session_id,
                        "source": "langchain",
                        "message_type": message.__class__.__name__,
                    },
                )

        asyncio.run(_add_message())

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """
        Add multiple messages to Cilow.

        Args:
            messages: List of LangChain messages to add
        """
        for message in messages:
            self.add_message(message)

    def clear(self) -> None:
        """
        Clear all messages for this session.

        Warning: This permanently deletes all messages in the session.
        """

        async def _clear():
            async with self._get_client() as client:
                # Get all memories for this session
                memories = await client.list_memories(
                    tags=[f"session:{self.session_id}"],
                    user_id=self.user_id,
                    limit=10000,
                )
                # Delete each memory
                for memory in memories:
                    if memory.id:
                        try:
                            await client.delete_memory(memory.id)
                        except Exception:
                            pass  # Ignore deletion errors

        asyncio.run(_clear())

    # Async versions for better performance in async contexts

    async def aget_messages(self) -> List[BaseMessage]:
        """
        Async version of messages property.

        Example:
            ```python
            messages = await history.aget_messages()
            ```
        """
        async with self._get_client() as client:
            memories = await client.list_memories(
                tags=[f"session:{self.session_id}"],
                user_id=self.user_id,
                limit=1000,
            )
            sorted_memories = sorted(
                memories,
                key=lambda m: m.created_at or "",
            )
            return [self._memory_to_message(m) for m in sorted_memories]

    async def aadd_message(self, message: BaseMessage) -> None:
        """
        Async version of add_message.

        Args:
            message: LangChain message to add
        """
        async with self._get_client() as client:
            if isinstance(message, HumanMessage):
                role = "human"
            elif isinstance(message, AIMessage):
                role = "ai"
            elif isinstance(message, SystemMessage):
                role = "system"
            else:
                role = "unknown"

            tags = [
                f"session:{self.session_id}",
                f"role:{role}",
                "langchain",
                "chat_history",
            ]

            await client.add_memory(
                content=str(message.content),
                tags=tags,
                user_id=self.user_id,
                metadata={
                    "role": role,
                    "session_id": self.session_id,
                    "source": "langchain",
                    "message_type": message.__class__.__name__,
                },
            )

    async def aclear(self) -> None:
        """
        Async version of clear.
        """
        async with self._get_client() as client:
            memories = await client.list_memories(
                tags=[f"session:{self.session_id}"],
                user_id=self.user_id,
                limit=10000,
            )
            for memory in memories:
                if memory.id:
                    try:
                        await client.delete_memory(memory.id)
                    except Exception:
                        pass
