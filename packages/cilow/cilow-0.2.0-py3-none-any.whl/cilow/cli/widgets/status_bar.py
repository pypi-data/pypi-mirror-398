"""Status Bar Widget for Cilow CLI"""

from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style


# Triquetra gradient colors
COLORS = {
    "blue": "#00BFFF",
    "cyan": "#00CED1",
    "green": "#32CD32",
    "yellow": "#FFD700",
    "dim": "#8b949e",
    "red": "#ff6b6b",
}


class StatusBar(Widget):
    """
    Status bar showing connection status, model info, and memory stats.

    Displays:
    - Connection status (green/red dot)
    - Active LLM model
    - Memory count
    - Current project/session
    """

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: #161b22;
        color: #8b949e;
        padding: 0 2;
    }
    """

    connected = reactive(False)
    model_name = reactive("auto")
    memory_count = reactive(0)
    session_id = reactive("")
    project_name = reactive("")

    def __init__(
        self,
        connected: bool = False,
        model_name: str = "auto",
        session_id: str = "",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.connected = connected
        self.model_name = model_name
        self.session_id = session_id

    def render(self) -> Text:
        """Render the status bar."""
        text = Text()

        # Connection status
        if self.connected:
            text.append("● ", style=Style(color=COLORS["green"]))
            text.append("connected", style=Style(color=COLORS["dim"]))
        else:
            text.append("○ ", style=Style(color=COLORS["red"]))
            text.append("disconnected", style=Style(color=COLORS["dim"]))

        text.append("  │  ", style=Style(color=COLORS["dim"]))

        # Model info
        text.append("model: ", style=Style(color=COLORS["dim"]))
        text.append(self.model_name, style=Style(color=COLORS["cyan"]))

        text.append("  │  ", style=Style(color=COLORS["dim"]))

        # Memory count
        text.append("memories: ", style=Style(color=COLORS["dim"]))
        text.append(str(self.memory_count), style=Style(color=COLORS["yellow"]))

        # Session/Project info (if available)
        if self.project_name:
            text.append("  │  ", style=Style(color=COLORS["dim"]))
            text.append("project: ", style=Style(color=COLORS["dim"]))
            text.append(self.project_name, style=Style(color=COLORS["green"]))
        elif self.session_id:
            text.append("  │  ", style=Style(color=COLORS["dim"]))
            text.append("session: ", style=Style(color=COLORS["dim"]))
            # Truncate long session IDs
            display_id = self.session_id[:12] + "..." if len(self.session_id) > 15 else self.session_id
            text.append(display_id, style=Style(color=COLORS["dim"]))

        return text

    def set_connected(self, connected: bool) -> None:
        """Update connection status."""
        self.connected = connected

    def set_model(self, model_name: str) -> None:
        """Update model name."""
        self.model_name = model_name

    def set_memory_count(self, count: int) -> None:
        """Update memory count."""
        self.memory_count = count

    def set_session(self, session_id: str) -> None:
        """Update session ID."""
        self.session_id = session_id

    def set_project(self, project_name: str) -> None:
        """Update project name."""
        self.project_name = project_name
