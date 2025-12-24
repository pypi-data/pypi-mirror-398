"""State Indicator Widget - Animated cilow branding with state display"""

from enum import Enum
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style
from typing import Optional


# Triquetra gradient colors
COLORS = {
    "blue": "#00BFFF",
    "cyan": "#00CED1",
    "green": "#32CD32",
    "yellow": "#FFD700",
    "dim": "#6e7681",
    "bright": "#ffffff",
    "error": "#ff6b6b",
}

# Letter colors for gradient
LETTER_COLORS = ["blue", "cyan", "cyan", "green", "yellow"]
LETTERS = "cilow"


class AgentState(Enum):
    """Current state of the agent."""
    IDLE = "idle"
    THINKING = "thinking"
    SAVING = "saving"
    RECALLING = "recalling"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class StateIndicator(Widget):
    """
    Animated "cilow" branding widget that shows current application state.

    States:
    - IDLE: Static gradient text
    - THINKING: Wave animation through letters
    - SAVING: Cyan flash effect
    - RECALLING: Yellow pulse effect
    - CONNECTED: Green dot prefix
    - DISCONNECTED: Gray dot prefix
    - ERROR: Red dot + red tint
    """

    DEFAULT_CSS = """
    StateIndicator {
        width: auto;
        height: 1;
        content-align: left middle;
    }
    """

    state = reactive(AgentState.IDLE)
    frame = reactive(0)
    connected = reactive(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._timer = None
        self._flash_frames = 0

    def on_mount(self) -> None:
        """Start animation timer."""
        self._timer = self.set_interval(0.1, self._tick)

    def _tick(self) -> None:
        """Animation tick - advance frame."""
        if self.state in (AgentState.THINKING, AgentState.SAVING, AgentState.RECALLING):
            self.frame = (self.frame + 1) % 10

            # Flash states auto-reset after animation
            if self.state in (AgentState.SAVING, AgentState.RECALLING):
                self._flash_frames += 1
                if self._flash_frames >= 6:  # 600ms flash
                    self._flash_frames = 0
                    self.state = AgentState.CONNECTED if self.connected else AgentState.IDLE

    def render(self) -> Text:
        """Render the state indicator."""
        text = Text()

        # Connection dot
        if self.state == AgentState.ERROR:
            text.append("! ", style=Style(color=COLORS["error"], bold=True))
        elif self.state == AgentState.DISCONNECTED or not self.connected:
            text.append("o ", style=Style(color=COLORS["dim"]))
        elif self.connected:
            text.append("* ", style=Style(color=COLORS["green"]))

        # Render "cilow" with state-based styling
        if self.state == AgentState.THINKING:
            self._render_thinking(text)
        elif self.state == AgentState.SAVING:
            self._render_saving(text)
        elif self.state == AgentState.RECALLING:
            self._render_recalling(text)
        elif self.state == AgentState.ERROR:
            self._render_error(text)
        else:
            self._render_idle(text)

        # State label
        if self.state == AgentState.THINKING:
            text.append(" ", style=Style(color=COLORS["dim"]))
            dots = "." * ((self.frame // 3) % 4)
            text.append(dots.ljust(3), style=Style(color=COLORS["dim"]))
        elif self.state == AgentState.SAVING:
            text.append(" [+]", style=Style(color=COLORS["cyan"]))
        elif self.state == AgentState.RECALLING:
            text.append(" [~]", style=Style(color=COLORS["yellow"]))

        return text

    def _render_idle(self, text: Text) -> None:
        """Render static gradient."""
        for i, letter in enumerate(LETTERS):
            color = COLORS[LETTER_COLORS[i]]
            text.append(letter, style=Style(color=color, bold=True))

    def _render_thinking(self, text: Text) -> None:
        """Render wave animation - one letter highlighted at a time."""
        highlight_idx = self.frame % 5

        for i, letter in enumerate(LETTERS):
            if i == highlight_idx:
                # Highlighted letter - bright white
                text.append(letter, style=Style(color=COLORS["bright"], bold=True))
            else:
                # Normal gradient color but slightly dimmed
                color = COLORS[LETTER_COLORS[i]]
                text.append(letter, style=Style(color=color, bold=False))

    def _render_saving(self, text: Text) -> None:
        """Render cyan flash effect."""
        flash_intensity = self.frame % 6

        if flash_intensity < 3:
            # Flash phase - all cyan
            for letter in LETTERS:
                text.append(letter, style=Style(color=COLORS["cyan"], bold=True))
        else:
            # Fade back to normal
            self._render_idle(text)

    def _render_recalling(self, text: Text) -> None:
        """Render yellow pulse effect."""
        pulse_intensity = self.frame % 6

        if pulse_intensity < 3:
            # Pulse phase - all yellow
            for letter in LETTERS:
                text.append(letter, style=Style(color=COLORS["yellow"], bold=True))
        else:
            # Fade back to normal
            self._render_idle(text)

    def _render_error(self, text: Text) -> None:
        """Render error state - red tinted."""
        for letter in LETTERS:
            text.append(letter, style=Style(color=COLORS["error"], bold=True))

    # Public API for state changes

    def set_thinking(self) -> None:
        """Start thinking animation."""
        self.state = AgentState.THINKING
        self.frame = 0

    def set_idle(self) -> None:
        """Return to idle state."""
        self.state = AgentState.CONNECTED if self.connected else AgentState.IDLE
        self.frame = 0

    def set_saving(self) -> None:
        """Trigger save animation."""
        self.state = AgentState.SAVING
        self.frame = 0
        self._flash_frames = 0

    def set_recalling(self) -> None:
        """Trigger recall animation."""
        self.state = AgentState.RECALLING
        self.frame = 0
        self._flash_frames = 0

    def set_connected(self, connected: bool) -> None:
        """Update connection status."""
        self.connected = connected
        if self.state in (AgentState.IDLE, AgentState.CONNECTED, AgentState.DISCONNECTED):
            self.state = AgentState.CONNECTED if connected else AgentState.DISCONNECTED

    def set_error(self, error: bool = True) -> None:
        """Set or clear error state."""
        if error:
            self.state = AgentState.ERROR
        else:
            self.set_idle()
