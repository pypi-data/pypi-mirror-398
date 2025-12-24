"""
Cilow Integrations

Third-party framework integrations for the Cilow memory SDK.

Available integrations:
- langchain: LangChain memory and chat history implementations
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .langchain import CilowChatMessageHistory, CilowSemanticMemory, CilowConversationMemory

__all__ = [
    "CilowChatMessageHistory",
    "CilowSemanticMemory",
    "CilowConversationMemory",
]


def __getattr__(name: str):
    """Lazy import for integrations to avoid importing optional dependencies."""
    if name in ("CilowChatMessageHistory", "CilowSemanticMemory", "CilowConversationMemory"):
        from .langchain import CilowChatMessageHistory, CilowSemanticMemory, CilowConversationMemory

        if name == "CilowChatMessageHistory":
            return CilowChatMessageHistory
        elif name == "CilowSemanticMemory":
            return CilowSemanticMemory
        return CilowConversationMemory

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
