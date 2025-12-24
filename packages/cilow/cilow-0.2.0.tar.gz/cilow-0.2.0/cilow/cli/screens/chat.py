"""Chat Screen - Main conversation interface"""

from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, RichLog
from textual.binding import Binding
from textual import work
from typing import Optional
import asyncio
from rich.text import Text
from rich.style import Style

from ..widgets import ChatInput, MessageList, StatusBar, StateIndicator, AgentState


class ChatScreen(Screen):
    """
    Main chat screen with message list, input box, and status bar.

    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  CILOW - AI Memory Agent                    [Settings]  │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │  You > Hello, I'm working on a new project             │
    │                                                         │
    │  Cilow > That's great! I've saved that to memory.      │
    │          [~] found 3 relevant memories                  │
    │                                                         │
    ├─────────────────────────────────────────────────────────┤
    │  │ Type your message...                            [⏎] │
    ├─────────────────────────────────────────────────────────┤
    │  ● connected  │  model: claude  │  memories: 42        │
    └─────────────────────────────────────────────────────────┘
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+s", "settings", "Settings", show=True),
        Binding("escape", "focus_input", "Focus Input"),
        Binding("f1", "help", "Help", show=True),
    ]

    DEFAULT_CSS = """
    ChatScreen {
        background: #0d1117;
    }

    #chat-header {
        dock: top;
        height: 3;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 2;
    }

    #state-indicator {
        width: 1fr;
        content-align: left middle;
    }

    #header-actions {
        dock: right;
        width: auto;
        color: #8b949e;
        content-align: right middle;
    }

    #chat-container {
        height: 1fr;
        padding: 0;
    }

    #message-area {
        height: 1fr;
    }

    #input-container {
        dock: bottom;
        height: auto;
        max-height: 6;
        background: #161b22;
        border-top: solid #30363d;
        padding: 1 2;
    }

    #chat-input {
        width: 100%;
    }
    """

    def __init__(
        self,
        chatbot=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.chatbot = chatbot
        self._is_processing = False

    def compose(self):
        """Compose the chat screen layout."""
        # Header with state indicator
        with Container(id="chat-header"):
            yield StateIndicator(id="state-indicator")
            yield Static("/help", id="header-actions")

        # Main chat container
        with Container(id="chat-container"):
            yield MessageList(id="message-list")

        # Input container
        with Container(id="input-container"):
            yield ChatInput(
                placeholder="Type your message... (Enter to send, /help for commands)",
                id="chat-input"
            )

        # Status bar
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        """Handle screen mount."""
        # Focus the input
        self.query_one("#chat-input", ChatInput).focus()

        # Show minimal welcome
        message_list = self.query_one("#message-list", MessageList)
        message_list.add_system_message("ready", "success")

        # Update state indicator and status bar
        state_indicator = self.query_one("#state-indicator", StateIndicator)
        if self.chatbot:
            state_indicator.set_connected(True)
            self._update_status()
        else:
            state_indicator.set_connected(False)

    def _update_status(self) -> None:
        """Update the status bar with current info."""
        status_bar = self.query_one("#status-bar", StatusBar)

        if self.chatbot:
            status_bar.set_connected(True)
            if self.chatbot.llm_provider:
                status_bar.set_model(self.chatbot.llm_provider.name)
            if self.chatbot.session_id:
                status_bar.set_session(self.chatbot.session_id)

    async def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """Handle chat input submission."""
        if self._is_processing:
            return

        user_input = event.value.strip()
        if not user_input:
            return

        message_list = self.query_one("#message-list", MessageList)

        # Check for slash commands
        if user_input.startswith("/"):
            await self._handle_command(user_input)
            return

        # Process chat message
        await self._process_message(user_input)

    async def _handle_command(self, command: str) -> None:
        """Handle slash commands."""
        message_list = self.query_one("#message-list", MessageList)
        parts = command.split()
        cmd = parts[0].lower()

        if cmd in ["/quit", "/exit", "/q"]:
            self.app.exit()
        elif cmd in ["/clear", "/cls"]:
            message_list.clear()
            message_list.add_system_message("Chat cleared", "info")
        elif cmd in ["/help", "/?"]:
            self._show_help()
        elif cmd == "/status":
            self._show_status()
        elif cmd in ["/models", "/model"]:
            if len(parts) > 1:
                await self._switch_model(parts[1])
            else:
                self._show_models()
        elif cmd == "/search":
            query = command[7:].strip() if len(command) > 7 else ""
            if query:
                await self._search_memory(query)
            else:
                message_list.add_system_message("Usage: /search <query>", "warning")
        elif cmd == "/memories":
            await self._show_memories()
        else:
            message_list.add_system_message(f"Unknown command: {cmd}. Type /help for available commands.", "warning")

    def _show_help(self) -> None:
        """Show help information."""
        message_list = self.query_one("#message-list", MessageList)
        message_list.add_divider("Help")
        message_list.add_system_message("Available commands:", "info")
        message_list.add_system_message("  /help, /?        - Show this help", "info")
        message_list.add_system_message("  /models          - List available models", "info")
        message_list.add_system_message("  /models <name>   - Switch to a model (claude, gpt)", "info")
        message_list.add_system_message("  /clear, /cls     - Clear chat history", "info")
        message_list.add_system_message("  /search <query>  - Search memories", "info")
        message_list.add_system_message("  /memories        - Show recent memories", "info")
        message_list.add_system_message("  /status          - Show connection status", "info")
        message_list.add_system_message("  /quit, /exit     - Exit Cilow", "info")
        message_list.add_divider()

    def _show_models(self) -> None:
        """Show available models."""
        message_list = self.query_one("#message-list", MessageList)
        message_list.add_divider("Models")

        current_model = "none"
        if self.chatbot and self.chatbot.llm_provider:
            current_model = self.chatbot.llm_provider.name

        message_list.add_system_message(f"Current model: {current_model}", "info")
        message_list.add_system_message("", "info")

        if self.chatbot:
            models = self.chatbot.get_available_models()
            message_list.add_system_message("Available models:", "info")
            for model in models:
                status = ""
                if model["active"]:
                    status = " [active]"
                elif model["available"]:
                    status = " [ready]"
                else:
                    status = " [no API key]"
                message_list.add_system_message(f"  {model['name']:8} - {model['display_name']}{status}", "info")
        else:
            message_list.add_system_message("Available models:", "info")
            message_list.add_system_message("  claude  - Anthropic Claude", "info")
            message_list.add_system_message("  gpt     - OpenAI GPT-4", "info")

        message_list.add_system_message("", "info")
        message_list.add_system_message("Usage: /models <name>  (e.g., /models claude)", "info")
        message_list.add_divider()

    async def _switch_model(self, model_name: str) -> None:
        """Switch to a different model."""
        message_list = self.query_one("#message-list", MessageList)
        status_bar = self.query_one("#status-bar", StatusBar)

        model_name = model_name.lower().strip()

        if model_name not in ["claude", "gpt"]:
            message_list.add_system_message(
                f"Unknown model: {model_name}. Available: claude, gpt",
                "warning"
            )
            return

        if not self.chatbot:
            message_list.add_system_message("Chatbot not initialized", "error")
            return

        try:
            message_list.add_system_message(f"Switching to {model_name}...", "info")

            # Switch the model
            success = self.chatbot.switch_model(model_name)

            if success:
                new_name = self.chatbot.llm_provider.name
                message_list.add_system_message(f"Switched to {new_name}", "success")
                status_bar.set_model(new_name)
            else:
                message_list.add_system_message(
                    f"Failed to switch to {model_name}. Check your API key.",
                    "error"
                )
        except Exception as e:
            message_list.add_system_message(f"Error switching model: {e}", "error")

    def _show_status(self) -> None:
        """Show current status."""
        message_list = self.query_one("#message-list", MessageList)
        message_list.add_divider("Status")

        if self.chatbot:
            message_list.add_system_message(f"Model: {self.chatbot.llm_provider.name if self.chatbot.llm_provider else 'Not connected'}", "info")
            message_list.add_system_message(f"Session: {self.chatbot.session_id}", "info")
            message_list.add_system_message(f"API URL: {self.chatbot.memory_manager.base_url}", "info")
        else:
            message_list.add_system_message("Chatbot not initialized", "warning")

        message_list.add_divider()

    async def _search_memory(self, query: str) -> None:
        """Search memory for relevant context."""
        message_list = self.query_one("#message-list", MessageList)
        state_indicator = self.query_one("#state-indicator", StateIndicator)

        if not self.chatbot:
            message_list.add_system_message("Chatbot not initialized", "error")
            return

        message_list.add_system_message(f"Searching for: {query}", "info")
        state_indicator.set_recalling()

        try:
            results = await self.chatbot.memory_manager.search_relevant_context(
                query=query,
                limit=5,
                min_score=0.3,
            )

            if results:
                message_list.add_system_message(f"Found {len(results)} results:", "success")
                for i, result in enumerate(results, 1):
                    content = result.get("content", "")[:100]
                    score = result.get("score", 0)
                    message_list.add_system_message(f"  {i}. [{score:.2f}] {content}...", "info")
            else:
                message_list.add_system_message("No relevant memories found", "info")
        except Exception as e:
            message_list.add_system_message(f"Search error: {e}", "error")
        finally:
            state_indicator.set_idle()

    async def _show_memories(self) -> None:
        """Show recent memories."""
        message_list = self.query_one("#message-list", MessageList)
        state_indicator = self.query_one("#state-indicator", StateIndicator)

        if not self.chatbot:
            message_list.add_system_message("Chatbot not initialized", "error")
            return

        state_indicator.set_recalling()
        try:
            memories = await self.chatbot.memory_manager.get_session_context(limit=5)
            if memories:
                message_list.add_divider("Recent Memories")
                for memory in memories:
                    content = memory.get("content", "")[:80]
                    message_list.add_system_message(f"  - {content}...", "info")
                message_list.add_divider()
            else:
                message_list.add_system_message("No memories in current session", "info")
        except Exception as e:
            message_list.add_system_message(f"Error: {e}", "error")
        finally:
            state_indicator.set_idle()

    @work(exclusive=True)
    async def _process_message(self, user_input: str) -> None:
        """Process a user message through the chatbot."""
        self._is_processing = True
        message_list = self.query_one("#message-list", MessageList)
        chat_input = self.query_one("#chat-input", ChatInput)
        state_indicator = self.query_one("#state-indicator", StateIndicator)

        # Disable input while processing
        chat_input.disabled = True

        # Show user message
        message_list.add_user_message(user_input)

        if not self.chatbot:
            message_list.add_system_message("Chatbot not initialized. Please restart.", "error")
            state_indicator.set_error(True)
            chat_input.disabled = False
            self._is_processing = False
            return

        try:
            # Check if LLM is configured
            if not self.chatbot.llm_provider:
                message_list.add_system_message(
                    "No LLM configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY and restart.",
                    "warning"
                )
                message_list.add_system_message(
                    "Or use /models to see available options.",
                    "info"
                )
                return

            # Show thinking state
            state_indicator.set_thinking()
            message_list.show_thinking("thinking")

            # Process through chatbot
            result = await self.chatbot.process_message(user_input)

            # Hide thinking (will be overwritten by response)
            message_list.hide_thinking()
            state_indicator.set_idle()

            if result == "quit":
                self.app.exit()

        except ValueError as e:
            # Handle missing LLM config
            message_list.add_system_message(str(e), "warning")
            state_indicator.set_idle()
        except Exception as e:
            message_list.add_system_message(f"Error: {e}", "error")
            state_indicator.set_error(True)

        finally:
            chat_input.disabled = False
            chat_input.focus()
            self._is_processing = False

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_clear(self) -> None:
        """Clear the chat."""
        message_list = self.query_one("#message-list", MessageList)
        message_list.clear()
        message_list.add_system_message("Chat cleared", "info")

    def action_settings(self) -> None:
        """Open settings screen."""
        # Will be implemented with SettingsScreen
        message_list = self.query_one("#message-list", MessageList)
        message_list.add_system_message("Settings screen coming soon...", "info")

    def action_focus_input(self) -> None:
        """Focus the chat input."""
        self.query_one("#chat-input", ChatInput).focus()

    def action_help(self) -> None:
        """Show help."""
        self._show_help()
