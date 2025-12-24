"""Animated Cilow Logo Widget with Triquetra Design"""

from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style


# Color mapping - Triquetra gradient
COLORS = {
    "blue": "#00BFFF",
    "cyan": "#00CED1",
    "green": "#32CD32",
    "yellow": "#FFD700",
    "dim": "#6e7681",
}

# Clean minimal logo - sleek and modern
CILOW_LOGO = [
    ("  ┏━━┓┏┓┏┓     ┏━━┓┏┓ ┏┓", "blue"),
    ("  ┃  ┃┃┃┃┃     ┃  ┃┃┃ ┃┃", "cyan"),
    ("  ┃  ┗┛┃┃┃     ┃  ┃┃┃ ┃┃", "cyan"),
    ("  ┃    ┃┃┃     ┃  ┃┃┗┳┛┃", "green"),
    ("  ┗━━━━┛┗┻━━━━━┻━━┛┗━┻━┛", "yellow"),
]

# Alternative: Simple text-based logo
CILOW_TEXT = [
    ("   _____ _ _               ", "blue"),
    ("  / ____(_) |              ", "blue"),
    (" | |     _| | _____      __", "cyan"),
    (" | |    | | |/ _ \\ \\ /\\ / /", "green"),
    (" | |____| | | (_) \\ V  V / ", "green"),
    ("  \\_____|_|_|\\___/ \\_/\\_/  ", "yellow"),
]

# Sleek minimal version
CILOW_MINIMAL = [
    ("╭─────────────────────────╮", "blue"),
    ("│    C I L O W            │", "cyan"),
    ("│    ═══════════          │", "green"),
    ("╰─────────────────────────╯", "yellow"),
]

# Ultra clean - just the name with style
CILOW_CLEAN = "CILOW"


class CilowLogo(Widget):
    """Animated Cilow logo with triquetra gradient colors."""

    DEFAULT_CSS = """
    CilowLogo {
        width: 100%;
        height: auto;
        content-align: center middle;
        padding: 1 0;
    }
    """

    frame = reactive(0)
    loading = reactive(False)

    def __init__(
        self,
        compact: bool = False,
        animate: bool = False,
        style: str = "clean",  # "clean", "box", "text"
        **kwargs
    ):
        super().__init__(**kwargs)
        self.compact = compact
        self.animate = animate
        self.logo_style = style
        self._timer = None

    def on_mount(self) -> None:
        """Start animation if enabled."""
        if self.animate:
            self._timer = self.set_interval(0.5, self._next_frame)

    def _next_frame(self) -> None:
        """Advance to next animation frame."""
        if self.loading:
            self.frame = (self.frame + 1) % 4

    def render(self) -> Text:
        """Render the logo."""
        if self.compact:
            return self._render_compact()
        return self._render_full()

    def _render_compact(self) -> Text:
        """Render compact logo for header."""
        spinner_frames = ["◐", "◓", "◑", "◒"]
        if self.loading:
            spinner = spinner_frames[self.frame]
            return Text(f"{spinner} CILOW", style=Style(color=COLORS["cyan"], bold=True))
        return Text("CILOW", style=Style(color=COLORS["cyan"], bold=True))

    def _render_full(self) -> Text:
        """Render full logo with gradient."""
        text = Text()

        if self.logo_style == "box":
            # Box style
            for line, color in CILOW_MINIMAL:
                text.append(line, style=Style(color=COLORS.get(color, "#FFFFFF")))
                text.append("\n")
        elif self.logo_style == "text":
            # Text ASCII art style
            for line, color in CILOW_TEXT:
                text.append(line, style=Style(color=COLORS.get(color, "#FFFFFF")))
                text.append("\n")
        else:
            # Clean modern style (default)
            text.append("\n")
            # Gradient letters
            letters = [
                ("C", "blue"),
                ("I", "cyan"),
                ("L", "cyan"),
                ("O", "green"),
                ("W", "yellow"),
            ]
            for letter, color in letters:
                text.append(letter, style=Style(color=COLORS[color], bold=True))
            text.append("\n")
            text.append("─" * 5, style=Style(color=COLORS["green"]))
            text.append("\n")

        # Add tagline
        text.append("\n")
        text.append("AI Memory Agent", style=Style(color="#8b949e", italic=True))

        return text

    def start_loading(self) -> None:
        """Start loading animation."""
        self.loading = True

    def stop_loading(self) -> None:
        """Stop loading animation."""
        self.loading = False
        self.frame = 0


# Keep exports for backwards compatibility
TRIQUETRA_KNOT = CILOW_MINIMAL
