"""Settings Screen - Configuration management"""

from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Select, Switch, Input, Label
from textual.binding import Binding


class SettingsScreen(Screen):
    """
    Settings screen for configuring Cilow.

    Settings:
    - LLM Provider selection
    - API URL configuration
    - API Key management
    - Memory settings
    - Theme selection
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+s", "save", "Save"),
    ]

    DEFAULT_CSS = """
    SettingsScreen {
        background: #0d1117;
    }

    #settings-header {
        dock: top;
        height: 3;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 2;
        content-align: left middle;
    }

    #settings-title {
        color: #00CED1;
        text-style: bold;
    }

    #settings-container {
        padding: 2;
    }

    .setting-group {
        margin-bottom: 2;
        padding: 1;
        background: #161b22;
        border: solid #30363d;
    }

    .setting-label {
        color: #00CED1;
        text-style: bold;
        margin-bottom: 1;
    }

    .setting-description {
        color: #8b949e;
        margin-bottom: 1;
    }

    #button-row {
        dock: bottom;
        height: 3;
        padding: 0 2;
        background: #161b22;
        border-top: solid #30363d;
    }
    """

    def compose(self):
        """Compose the settings screen."""
        # Header
        with Container(id="settings-header"):
            yield Static("Settings", id="settings-title")

        # Main container
        with Container(id="settings-container"):
            # LLM Provider
            with Vertical(classes="setting-group"):
                yield Static("LLM Provider", classes="setting-label")
                yield Static("Select the AI model to use for conversations", classes="setting-description")
                yield Select(
                    [
                        ("Auto-detect", "auto"),
                        ("Claude (Anthropic)", "claude"),
                        ("GPT (OpenAI)", "gpt"),
                    ],
                    value="auto",
                    id="model-select"
                )

            # API URL
            with Vertical(classes="setting-group"):
                yield Static("Cilow API URL", classes="setting-label")
                yield Static("URL of your Cilow server instance", classes="setting-description")
                yield Input(
                    value="http://localhost:8080",
                    placeholder="http://localhost:8080",
                    id="api-url-input"
                )

            # API Key
            with Vertical(classes="setting-group"):
                yield Static("API Key", classes="setting-label")
                yield Static("Your Cilow API key (from dashboard.cilow.ai)", classes="setting-description")
                yield Input(
                    placeholder="Enter your API key...",
                    password=True,
                    id="api-key-input"
                )

            # Auto-save
            with Vertical(classes="setting-group"):
                yield Static("Auto-save Memories", classes="setting-label")
                yield Static("Automatically save meaningful conversations to memory", classes="setting-description")
                with Horizontal():
                    yield Switch(value=True, id="auto-save-switch")
                    yield Static("  Enabled", classes="setting-description")

            # Context Limit
            with Vertical(classes="setting-group"):
                yield Static("Context Token Limit", classes="setting-label")
                yield Static("Maximum tokens to include from memory context", classes="setting-description")
                yield Input(
                    value="2000",
                    placeholder="2000",
                    id="context-limit-input"
                )

        # Button row
        with Horizontal(id="button-row"):
            yield Button("Cancel", variant="default", id="cancel-btn")
            yield Button("Save", variant="primary", id="save-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.app.pop_screen()
        elif event.button.id == "save-btn":
            self._save_settings()
            self.app.pop_screen()

    def _save_settings(self) -> None:
        """Save settings to config."""
        # Get values
        model = self.query_one("#model-select", Select).value
        api_url = self.query_one("#api-url-input", Input).value
        api_key = self.query_one("#api-key-input", Input).value
        auto_save = self.query_one("#auto-save-switch", Switch).value
        context_limit = self.query_one("#context-limit-input", Input).value

        # TODO: Save to config file
        self.app.notify(f"Settings saved: model={model}, auto_save={auto_save}")

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_save(self) -> None:
        """Save and go back."""
        self._save_settings()
        self.app.pop_screen()
