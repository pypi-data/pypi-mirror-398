"""
Cilow LangChain Integration

Provides LangChain-compatible memory implementations backed by Cilow's
high-performance semantic search and entity extraction capabilities.

Example usage:
    ```python
    from langchain_openai import ChatOpenAI
    from langchain.chains import ConversationChain
    from cilow.integrations.langchain import CilowChatMessageHistory, CilowSemanticMemory

    # Option 1: Chat message history (stores every message)
    history = CilowChatMessageHistory(
        session_id="user-123-session-1",
        api_key="cilow_xxx"
    )

    # Option 2: Semantic memory (intelligent retrieval based on query)
    memory = CilowSemanticMemory(
        user_id="user-123",
        api_key="cilow_xxx"
    )

    chain = ConversationChain(
        llm=ChatOpenAI(),
        memory=memory
    )

    response = chain.invoke({"input": "What did we discuss about Python?"})
    ```
"""

from .chat_message_history import CilowChatMessageHistory
from .memory import CilowSemanticMemory, CilowConversationMemory
from .utils import messages_to_cilow, cilow_to_messages

__all__ = [
    "CilowChatMessageHistory",
    "CilowSemanticMemory",
    "CilowConversationMemory",
    "messages_to_cilow",
    "cilow_to_messages",
]
