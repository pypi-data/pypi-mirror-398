"""
Utility functions for Cilow LangChain integration.

Provides converters between LangChain message formats and Cilow memory structures.
"""

from typing import Any, Dict, List, Optional, Tuple

try:
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
        FunctionMessage,
        ToolMessage,
    )
except ImportError as e:
    raise ImportError(
        "langchain-core is required for LangChain integration. "
        "Install it with: pip install cilow[langchain]"
    ) from e

from ...models import Memory


def messages_to_cilow(
    messages: List[BaseMessage],
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convert LangChain messages to Cilow memory format.

    Args:
        messages: List of LangChain messages
        session_id: Optional session ID to tag messages
        user_id: Optional user ID for isolation

    Returns:
        List of dictionaries ready to be stored in Cilow

    Example:
        ```python
        from langchain_core.messages import HumanMessage, AIMessage
        from cilow.integrations.langchain.utils import messages_to_cilow

        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]

        cilow_memories = messages_to_cilow(messages, session_id="session-123")
        ```
    """
    result = []

    for i, message in enumerate(messages):
        role = _get_role_from_message(message)

        tags = [f"role:{role}", "langchain"]
        if session_id:
            tags.append(f"session:{session_id}")

        memory_data: Dict[str, Any] = {
            "content": str(message.content),
            "tags": tags,
            "metadata": {
                "role": role,
                "message_type": message.__class__.__name__,
                "sequence": i,
                "source": "langchain",
            },
        }

        if user_id:
            memory_data["user_id"] = user_id

        if session_id:
            memory_data["metadata"]["session_id"] = session_id

        # Include additional message attributes
        if hasattr(message, "additional_kwargs") and message.additional_kwargs:
            memory_data["metadata"]["additional_kwargs"] = message.additional_kwargs

        result.append(memory_data)

    return result


def cilow_to_messages(
    memories: List[Memory],
    sort_by_created: bool = True,
) -> List[BaseMessage]:
    """
    Convert Cilow memories to LangChain messages.

    Args:
        memories: List of Cilow Memory objects
        sort_by_created: Whether to sort by created_at timestamp

    Returns:
        List of LangChain BaseMessage objects

    Example:
        ```python
        from cilow import CilowClient
        from cilow.integrations.langchain.utils import cilow_to_messages

        async with CilowClient(api_key="xxx") as client:
            memories = await client.list_memories(tags=["session:123"])
            messages = cilow_to_messages(memories)
        ```
    """
    if sort_by_created:
        memories = sorted(memories, key=lambda m: m.created_at or "")

    result: List[BaseMessage] = []

    for memory in memories:
        role, content = _extract_role_and_content(memory)

        if role == "human" or role == "user":
            result.append(HumanMessage(content=content))
        elif role == "ai" or role == "assistant":
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))
        elif role == "function":
            # FunctionMessage requires name
            name = memory.metadata.get("function_name", "unknown") if memory.metadata else "unknown"
            result.append(FunctionMessage(content=content, name=name))
        elif role == "tool":
            # ToolMessage requires tool_call_id
            tool_id = memory.metadata.get("tool_call_id", "") if memory.metadata else ""
            result.append(ToolMessage(content=content, tool_call_id=tool_id))
        else:
            # Default to human message
            result.append(HumanMessage(content=content))

    return result


def format_memories_for_prompt(
    memories: List[Memory],
    format_style: str = "bullet",
    include_metadata: bool = False,
    max_length: Optional[int] = None,
) -> str:
    """
    Format memories as a string suitable for prompt injection.

    Args:
        memories: List of Cilow Memory objects
        format_style: "bullet", "numbered", "conversation", or "plain"
        include_metadata: Whether to include tags and timestamps
        max_length: Optional maximum character length

    Returns:
        Formatted string

    Example:
        ```python
        context = format_memories_for_prompt(
            memories,
            format_style="conversation",
            max_length=2000,
        )

        prompt = f\"\"\"Given this context:
        {context}

        Answer the following question: {question}\"\"\"
        ```
    """
    if not memories:
        return ""

    lines = []

    for i, memory in enumerate(memories, 1):
        content = memory.content or ""

        if format_style == "bullet":
            prefix = "- "
        elif format_style == "numbered":
            prefix = f"{i}. "
        elif format_style == "conversation":
            role = _get_role_from_memory(memory)
            prefix = f"{role.capitalize()}: "
        else:  # plain
            prefix = ""

        line = f"{prefix}{content}"

        if include_metadata:
            meta_parts = []
            if memory.tags:
                meta_parts.append(f"tags: {', '.join(memory.tags)}")
            if memory.created_at:
                meta_parts.append(f"created: {memory.created_at}")
            if meta_parts:
                line += f" [{'; '.join(meta_parts)}]"

        lines.append(line)

    result = "\n".join(lines)

    if max_length and len(result) > max_length:
        result = result[: max_length - 3] + "..."

    return result


def split_conversation_content(content: str) -> Tuple[str, str]:
    """
    Split conversation-style content into user and assistant parts.

    Args:
        content: Content in format "User: ... Assistant: ..."

    Returns:
        Tuple of (user_message, assistant_message)

    Example:
        ```python
        content = "User: Hello\\nAssistant: Hi there!"
        user_msg, ai_msg = split_conversation_content(content)
        # user_msg = "Hello"
        # ai_msg = "Hi there!"
        ```
    """
    user_msg = ""
    assistant_msg = ""

    # Try to split on "User:" and "Assistant:" markers
    if "User:" in content:
        parts = content.split("User:", 1)
        if len(parts) > 1:
            remainder = parts[1]
            if "Assistant:" in remainder:
                user_part, assistant_part = remainder.split("Assistant:", 1)
                user_msg = user_part.strip()
                assistant_msg = assistant_part.strip()
            else:
                user_msg = remainder.strip()
    elif "Human:" in content:
        parts = content.split("Human:", 1)
        if len(parts) > 1:
            remainder = parts[1]
            if "AI:" in remainder:
                user_part, assistant_part = remainder.split("AI:", 1)
                user_msg = user_part.strip()
                assistant_msg = assistant_part.strip()
            elif "Assistant:" in remainder:
                user_part, assistant_part = remainder.split("Assistant:", 1)
                user_msg = user_part.strip()
                assistant_msg = assistant_part.strip()
            else:
                user_msg = remainder.strip()

    return user_msg, assistant_msg


def _get_role_from_message(message: BaseMessage) -> str:
    """Extract role string from a LangChain message."""
    if isinstance(message, HumanMessage):
        return "human"
    elif isinstance(message, AIMessage):
        return "ai"
    elif isinstance(message, SystemMessage):
        return "system"
    elif isinstance(message, FunctionMessage):
        return "function"
    elif isinstance(message, ToolMessage):
        return "tool"
    else:
        return "unknown"


def _get_role_from_memory(memory: Memory) -> str:
    """Extract role from a Cilow memory."""
    # Check metadata first
    if memory.metadata and "role" in memory.metadata:
        return str(memory.metadata["role"])

    # Check tags
    if memory.tags:
        for tag in memory.tags:
            if tag.startswith("role:"):
                return tag.split(":", 1)[1]

    return "human"


def _extract_role_and_content(memory: Memory) -> Tuple[str, str]:
    """Extract role and clean content from a memory."""
    role = _get_role_from_memory(memory)
    content = memory.content or ""

    # If content has conversation format, extract the relevant part
    if content.startswith("User:") or content.startswith("Human:"):
        user_msg, assistant_msg = split_conversation_content(content)
        if role in ("human", "user") and user_msg:
            content = user_msg
        elif role in ("ai", "assistant") and assistant_msg:
            content = assistant_msg

    return role, content
