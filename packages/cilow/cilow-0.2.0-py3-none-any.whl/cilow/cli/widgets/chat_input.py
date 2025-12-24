"""Enhanced Chat Input Widget with Command History"""

from textual.widgets import Input
from textual.message import Message
from textual import events
from typing import Optional


class ChatInput(Input):
    """
    Enhanced chat input with command history and slash command support.

    Features:
    - Command history navigation (up/down arrows)
    - Slash command auto-complete
    - Multi-line support hints
    """

    DEFAULT_CSS = """
    ChatInput {
        height: 3;
        background: #21262d;
        border: tall #00CED1;
        padding: 0 1;
    }

    ChatInput:focus {
        border: tall #32CD32;
    }

    ChatInput.-invalid {
        border: tall red;
    }
    """

    class Submitted(Message):
        """Message sent when user submits input."""
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def __init__(
        self,
        placeholder: str = "Type your message...",
        max_history: int = 100,
        **kwargs
    ):
        super().__init__(placeholder=placeholder, **kwargs)
        self.history: list[str] = []
        self.history_index: int = -1
        self.max_history = max_history
        self._current_input: str = ""

    def on_key(self, event: events.Key) -> None:
        """Handle key events for history navigation."""
        if event.key == "up":
            self._navigate_history(1)
            event.stop()
        elif event.key == "down":
            self._navigate_history(-1)
            event.stop()
        elif event.key == "enter":
            self._submit()
            event.stop()
        elif event.key == "escape":
            # Clear input on escape
            self.value = ""
            self.history_index = -1
            event.stop()

    def _navigate_history(self, direction: int) -> None:
        """Navigate through command history."""
        if not self.history:
            return

        # Save current input when starting navigation
        if self.history_index == -1:
            self._current_input = self.value

        # Calculate new index
        new_index = self.history_index + direction

        if new_index < -1:
            new_index = -1
        elif new_index >= len(self.history):
            new_index = len(self.history) - 1

        self.history_index = new_index

        # Update input value
        if self.history_index == -1:
            self.value = self._current_input
        else:
            self.value = self.history[-(self.history_index + 1)]

        # Move cursor to end
        self.cursor_position = len(self.value)

    def _submit(self) -> None:
        """Submit the current input."""
        value = self.value.strip()
        if not value:
            return

        # Add to history (avoid duplicates)
        if not self.history or self.history[-1] != value:
            self.history.append(value)
            if len(self.history) > self.max_history:
                self.history.pop(0)

        # Reset state
        self.history_index = -1
        self._current_input = ""
        self.value = ""

        # Post message
        self.post_message(self.Submitted(value))

    def get_suggestions(self, prefix: str) -> list[str]:
        """Get slash command suggestions for auto-complete."""
        commands = [
            "/help", "/models", "/clear", "/search",
            "/memories", "/status", "/quit", "/exit"
        ]

        if not prefix.startswith("/"):
            return []

        return [cmd for cmd in commands if cmd.startswith(prefix)]

    def clear_history(self) -> None:
        """Clear command history."""
        self.history.clear()
        self.history_index = -1
        self._current_input = ""
