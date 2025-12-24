"""
Cilow CLI Agent - Main Textual Application

A professional CLI agent with persistent memory, powered by Textual framework.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from textual.app import App
from textual.binding import Binding

from .screens import ChatScreen
from .llm_providers import LLMProvider, get_default_provider, AnthropicProvider, OpenAIProvider
from .memory_manager import MemoryManager


class CilowApp(App):
    """
    Cilow CLI Agent - AI Memory Assistant.

    Features:
    - Chat with persistent memory
    - Semantic context retrieval
    - Multiple LLM provider support
    - Project management
    - Settings configuration
    """

    TITLE = "Cilow"
    SUB_TITLE = "AI Memory Agent"

    # Use relative path from this file's location
    CSS_PATH = "styles/cilow.tcss"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "settings", "Settings"),
        Binding("ctrl+p", "projects", "Projects"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        session_id: Optional[str] = None,
        model: str = "auto",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.llm_provider = llm_provider
        self.base_url = base_url
        self.api_key = api_key or os.getenv("CILOW_API_KEY") or "test-api-key"
        self.access_token = access_token
        self.session_id = session_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        self.model = model

        # Will be initialized on mount
        self.memory_manager: Optional[MemoryManager] = None
        self.chatbot = None

    async def on_mount(self) -> None:
        """Initialize components when app mounts."""
        # Initialize LLM provider (may be None if no API key)
        if self.llm_provider is None:
            self.llm_provider = self._get_llm_provider()

        # Initialize memory manager
        self.memory_manager = MemoryManager(
            base_url=self.base_url,
            api_key=self.api_key,
            access_token=self.access_token,
            session_id=self.session_id,
        )
        await self.memory_manager.__aenter__()

        # Create chatbot adapter (handles None provider gracefully)
        self.chatbot = ChatbotAdapter(
            llm_provider=self.llm_provider,
            memory_manager=self.memory_manager,
            session_id=self.session_id,
        )

        # Push the chat screen
        chat_screen = ChatScreen(chatbot=self.chatbot)
        await self.push_screen(chat_screen)

        # Show warning if no LLM provider
        if self.llm_provider is None:
            self.notify(
                "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY",
                severity="warning",
                timeout=10
            )

    def _get_llm_provider(self) -> Optional[LLMProvider]:
        """Get the appropriate LLM provider based on model setting."""
        try:
            if self.model == "claude":
                return AnthropicProvider()
            elif self.model == "gpt":
                return OpenAIProvider()
            else:
                # Auto-detect
                return get_default_provider()
        except ValueError:
            # No API key configured - return None and handle gracefully
            return None

    async def on_unmount(self) -> None:
        """Cleanup when app unmounts."""
        if self.memory_manager:
            await self.memory_manager.__aexit__(None, None, None)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_settings(self) -> None:
        """Open settings screen."""
        # Will push SettingsScreen when implemented
        self.notify("Settings coming soon...")

    def action_projects(self) -> None:
        """Open projects screen."""
        # Will push ProjectsScreen when implemented
        self.notify("Projects coming soon...")

    def action_help(self) -> None:
        """Show help."""
        self.notify("Help: Type /help in chat for commands")


class ChatbotAdapter:
    """
    Adapter that wraps LLM provider and memory manager for TUI integration.

    This provides a simplified interface for the ChatScreen to use.
    """

    SYSTEM_PROMPT = """You are a helpful AI assistant with access to a sophisticated memory system powered by Cilow.

Your capabilities:
- You remember information from our conversations
- You can recall relevant context from past discussions
- You understand preferences, plans, and goals the user shares
- You can make cross-references between different topics

When the user shares information:
- Acknowledge what they've told you
- Connect it to relevant past information when appropriate
- Be helpful and conversational

The memory system automatically:
- Extracts entities (people, places, organizations, concepts)
- Identifies relationships between entities
- Tags content by type (preference, plan, fact, etc.)
- Builds a knowledge graph for deeper understanding

Be natural and helpful. Reference past context when relevant."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider],
        memory_manager: MemoryManager,
        session_id: str,
    ):
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
        self.session_id = session_id
        self.conversation_history: list = []

    async def process_message(self, user_input: str) -> Optional[str]:
        """
        Process a user message and return the response.

        Returns "quit" if the user wants to exit, None otherwise.
        Raises ValueError if no LLM provider is configured.
        """
        if self.llm_provider is None:
            raise ValueError("No LLM configured. Use /models to set up.")

        from .llm_providers import Message

        # Check if message is meaningful
        if self._is_meaningful_content(user_input):
            await self.memory_manager.add_conversation_turn(
                role="user",
                content=user_input,
            )

        # Search for relevant context
        context = ""
        if self._needs_context(user_input):
            search_results = await self.memory_manager.search_relevant_context(
                query=user_input,
                limit=5,
                min_score=0.4,
            )
            session_memories = await self.memory_manager.get_session_context(limit=5)
            context = self.memory_manager.build_context_prompt(
                search_results=search_results,
                session_memories=session_memories,
                max_tokens=2000,
            )

        # Build messages
        messages = list(self.conversation_history)
        messages.append(Message(role="user", content=user_input))

        # Build system prompt with context
        system_with_context = self.SYSTEM_PROMPT
        if context:
            system_with_context += f"\n\n## Retrieved Context\n{context}"

        # Get response
        full_response = ""
        async for token in self.llm_provider.stream_response(
            messages=messages,
            system_prompt=system_with_context,
        ):
            full_response += token

        # Store response if user message was meaningful
        if self._is_meaningful_content(user_input):
            await self.memory_manager.add_conversation_turn(
                role="assistant",
                content=full_response,
            )

        # Update conversation history
        self.conversation_history.append(Message(role="user", content=user_input))
        self.conversation_history.append(Message(role="assistant", content=full_response))
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return None

    def _is_meaningful_content(self, text: str) -> bool:
        """Check if content is worth saving to memory."""
        text_lower = text.lower().strip()

        trivial_patterns = [
            'hello', 'hi', 'hey', 'yo', 'sup', 'greetings',
            'good morning', 'good afternoon', 'good evening', 'goodnight',
            'ok', 'okay', 'k', 'sure', 'yes', 'no', 'yeah', 'yep', 'nope',
            'got it', 'understood', 'thanks', 'thank you', 'thx', 'ty',
            'cool', 'nice', 'great', 'awesome', 'perfect', 'sounds good',
            'what', 'why', 'how', 'when', 'where', 'who',
            'can you', 'could you', 'would you', 'will you',
            'bye', 'goodbye', 'see you', 'later', 'cya',
            'um', 'uh', 'hmm', 'hm', 'well', 'so', 'anyway',
        ]

        if text_lower in trivial_patterns:
            return False

        for pattern in trivial_patterns:
            if text_lower.startswith(pattern) and len(text_lower) < 20:
                return False

        info_signals = [
            'i am', "i'm", 'my name', 'i like', 'i love', 'i hate', 'i prefer',
            'i work', 'i live', 'i want', 'i need', 'i plan', 'i have',
            'favorite', 'working on', 'building', 'creating', 'launching',
            'remember', 'don\'t forget', 'note that', 'important',
            'schedule', 'meeting', 'deadline', 'project', 'goal',
            'love ', 'like ', 'hate ', 'prefer ',
        ]

        for signal in info_signals:
            if signal in text_lower:
                return True

        if len(text_lower) > 50:
            return True

        return False

    def _needs_context(self, text: str) -> bool:
        """Check if the message needs context retrieval."""
        context_triggers = [
            'what', 'who', 'when', 'where', 'remember', 'recall', 'told you',
            'said', 'mentioned', 'earlier', 'before', 'last time', 'my',
            'about me', 'do you know', 'did i', 'have i',
        ]
        return any(word in text.lower() for word in context_triggers) or len(text) > 30

    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different LLM provider.

        Args:
            model_name: Either 'claude' or 'gpt'

        Returns:
            True if switch was successful, False otherwise
        """
        try:
            if model_name == "claude":
                new_provider = AnthropicProvider()
            elif model_name == "gpt":
                new_provider = OpenAIProvider()
            else:
                return False

            self.llm_provider = new_provider
            return True
        except ValueError as e:
            # API key not set or other initialization error
            return False
        except Exception:
            return False

    def get_available_models(self) -> list[dict]:
        """Get list of available models with their status."""
        import os

        models = []

        # Check Claude availability
        has_anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
        models.append({
            "name": "claude",
            "display_name": "Claude (Anthropic)",
            "available": has_anthropic_key,
            "active": isinstance(self.llm_provider, AnthropicProvider),
        })

        # Check GPT availability
        has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
        models.append({
            "name": "gpt",
            "display_name": "GPT-4 (OpenAI)",
            "available": has_openai_key,
            "active": isinstance(self.llm_provider, OpenAIProvider),
        })

        return models


def main():
    """Entry point for the Cilow CLI agent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cilow - AI Memory Agent CLI"
    )
    parser.add_argument(
        "--model",
        choices=["claude", "gpt", "auto"],
        default="auto",
        help="LLM provider to use (default: auto-detect)",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("CILOW_URL", "http://localhost:8080"),
        help="Cilow API URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("CILOW_API_KEY"),
        help="Cilow API key",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="Session ID (default: auto-generated)",
    )

    args = parser.parse_args()

    # Create and run app
    app = CilowApp(
        base_url=args.api_url,
        api_key=args.api_key,
        session_id=args.session,
        model=args.model,
    )

    app.run()


if __name__ == "__main__":
    main()
