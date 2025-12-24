"""Message List Widget for Chat Display"""

from textual.widgets import RichLog
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style
from rich.markdown import Markdown
from rich.panel import Panel
from rich.console import Group
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class MessageRole(Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: MessageRole
    content: str
    timestamp: Optional[str] = None
    memory_indicator: Optional[str] = None


# Triquetra gradient colors
COLORS = {
    "blue": "#00BFFF",
    "cyan": "#00CED1",
    "green": "#32CD32",
    "yellow": "#FFD700",
    "dim": "#8b949e",
    "text": "#c9d1d9",
}


class MessageList(RichLog):
    """
    Scrollable message display with rich formatting.

    Features:
    - User/Assistant message styling
    - Markdown rendering for assistant responses
    - Memory indicators (saved, searched, context)
    - Thinking animation support
    - Auto-scroll to bottom
    """

    DEFAULT_CSS = """
    MessageList {
        height: 1fr;
        background: #0d1117;
        border: none;
        scrollbar-color: #00CED1;
        padding: 1 2;
    }
    """

    is_streaming = reactive(False)
    thinking_text = reactive("")

    def __init__(self, **kwargs):
        super().__init__(
            highlight=True,
            markup=True,
            wrap=True,
            auto_scroll=True,
            **kwargs
        )
        self._current_stream = ""
        self._stream_message_id: Optional[str] = None

    def add_user_message(self, content: str, saved: bool = False) -> None:
        """Add a user message to the list."""
        text = Text()
        text.append("You", style=Style(color=COLORS["blue"], bold=True))
        text.append(" > ", style=Style(color=COLORS["dim"]))
        text.append(content, style=Style(color=COLORS["text"]))

        if saved:
            text.append("\n")
            text.append("  [+] saved to memory", style=Style(color=COLORS["cyan"], italic=True))

        self.write(text)
        self.write("")  # Spacing

    def add_assistant_message(self, content: str, memory_info: Optional[str] = None) -> None:
        """Add an assistant message to the list."""
        text = Text()
        # Gradient "cilow" text
        text.append("c", style=Style(color=COLORS["blue"], bold=True))
        text.append("i", style=Style(color=COLORS["cyan"], bold=True))
        text.append("l", style=Style(color=COLORS["cyan"], bold=True))
        text.append("o", style=Style(color=COLORS["green"], bold=True))
        text.append("w", style=Style(color=COLORS["yellow"], bold=True))
        text.append(" > ", style=Style(color=COLORS["dim"]))

        self.write(text)

        # Render content as markdown for rich formatting
        try:
            md = Markdown(content)
            self.write(md)
        except Exception:
            # Fallback to plain text
            self.write(Text(content, style=Style(color=COLORS["text"])))

        if memory_info:
            indicator = Text()
            indicator.append(f"  [{memory_info}]", style=Style(color=COLORS["yellow"], italic=True))
            self.write(indicator)

        self.write("")  # Spacing

    def add_system_message(self, content: str, style_type: str = "info") -> None:
        """Add a system message (info, warning, error)."""
        color_map = {
            "info": COLORS["cyan"],
            "warning": COLORS["yellow"],
            "error": "#ff6b6b",
            "success": COLORS["green"],
        }
        color = color_map.get(style_type, COLORS["dim"])

        text = Text()
        text.append(f"[{style_type}] ", style=Style(color=color, bold=True))
        text.append(content, style=Style(color=COLORS["dim"]))
        self.write(text)

    def start_streaming(self) -> None:
        """Start streaming mode for assistant response."""
        self.is_streaming = True
        self._current_stream = ""

        # Write the cilow prefix with gradient
        text = Text()
        text.append("c", style=Style(color=COLORS["blue"], bold=True))
        text.append("i", style=Style(color=COLORS["cyan"], bold=True))
        text.append("l", style=Style(color=COLORS["cyan"], bold=True))
        text.append("o", style=Style(color=COLORS["green"], bold=True))
        text.append("w", style=Style(color=COLORS["yellow"], bold=True))
        text.append(" > ", style=Style(color=COLORS["dim"]))
        self.write(text)

    def stream_token(self, token: str) -> None:
        """Add a token to the streaming response."""
        if not self.is_streaming:
            return

        self._current_stream += token
        # For now, we'll accumulate and refresh
        # Textual RichLog doesn't support inline updates easily

    def end_streaming(self) -> str:
        """End streaming mode and return full response."""
        self.is_streaming = False
        content = self._current_stream

        # Render the accumulated content
        if content:
            try:
                md = Markdown(content)
                self.write(md)
            except Exception:
                self.write(Text(content, style=Style(color=COLORS["text"])))

        self.write("")  # Spacing
        self._current_stream = ""
        return content

    def show_thinking(self, message: str = "thinking") -> None:
        """Show thinking animation."""
        self.thinking_text = message
        text = Text()
        # Gradient cilow
        text.append("c", style=Style(color=COLORS["blue"], bold=True))
        text.append("i", style=Style(color=COLORS["cyan"], bold=True))
        text.append("l", style=Style(color=COLORS["cyan"], bold=True))
        text.append("o", style=Style(color=COLORS["green"], bold=True))
        text.append("w", style=Style(color=COLORS["yellow"], bold=True))
        text.append(" > ", style=Style(color=COLORS["dim"]))
        text.append(f"{message}...", style=Style(color=COLORS["dim"], italic=True))
        self.write(text)

    def hide_thinking(self) -> None:
        """Hide thinking indicator (clears last line conceptually)."""
        self.thinking_text = ""
        # Note: RichLog doesn't support removing lines easily
        # The thinking message will be overwritten by the actual response

    def show_memory_indicator(self, indicator_type: str, detail: str = "") -> None:
        """Show a memory operation indicator."""
        icons = {
            "save": ("+", COLORS["cyan"]),
            "search": ("~", COLORS["yellow"]),
            "context": (">", COLORS["green"]),
            "entity": ("*", COLORS["blue"]),
        }

        icon, color = icons.get(indicator_type, ("i", COLORS["dim"]))
        text = Text()
        text.append(f"  [{icon}] {indicator_type}", style=Style(color=color, italic=True))
        if detail:
            text.append(f": {detail}", style=Style(color=COLORS["dim"]))
        self.write(text)

    def add_divider(self, label: str = "") -> None:
        """Add a visual divider."""
        width = 50
        if label:
            padding = (width - len(label) - 2) // 2
            line = "─" * padding + f" {label} " + "─" * padding
        else:
            line = "─" * width

        text = Text(line, style=Style(color=COLORS["dim"]))
        self.write(text)
