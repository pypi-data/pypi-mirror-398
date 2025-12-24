"""
LLM Provider Abstraction Layer

Supports both Anthropic Claude and OpenAI GPT with streaming responses.
Auto-detects provider from environment variables.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List
from dataclasses import dataclass
import os


@dataclass
class Message:
    """Chat message with role and content."""
    role: str  # "user", "assistant", "system"
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for display."""
        pass

    @abstractmethod
    async def stream_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream response tokens."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate complete response (non-streaming)."""
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider with streaming support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.model = model
        self.max_tokens = max_tokens
        self._client = None

    @property
    def name(self) -> str:
        return f"Claude ({self.model})"

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
        return self._client

    async def stream_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream response tokens from Claude."""
        client = self._get_client()

        # Convert messages to Anthropic format
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        async with client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or "",
            messages=api_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate complete response from Claude."""
        client = self._get_client()

        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        response = await client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or "",
            messages=api_messages,
        )

        return response.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider with streaming support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.model = model
        self.max_tokens = max_tokens
        self._client = None

    @property
    def name(self) -> str:
        return f"GPT ({self.model})"

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install openai"
                )
        return self._client

    async def stream_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream response tokens from GPT."""
        client = self._get_client()

        # Build messages with optional system prompt
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend([
            {"role": m.role, "content": m.content}
            for m in messages
        ])

        stream = await client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            max_tokens=self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate complete response from GPT."""
        client = self._get_client()

        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend([
            {"role": m.role, "content": m.content}
            for m in messages
        ])

        response = await client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            max_tokens=self.max_tokens,
        )

        return response.choices[0].message.content


def get_default_provider() -> LLMProvider:
    """
    Get default LLM provider based on available API keys.

    Priority:
    1. ANTHROPIC_API_KEY -> Claude
    2. OPENAI_API_KEY -> GPT
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key:
        return AnthropicProvider(api_key=anthropic_key)
    elif openai_key:
        return OpenAIProvider(api_key=openai_key)
    else:
        raise ValueError(
            "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
        )
