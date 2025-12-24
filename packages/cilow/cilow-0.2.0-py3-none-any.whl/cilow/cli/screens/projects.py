"""Projects Screen - Project management"""

from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, ListView, ListItem, Input
from textual.binding import Binding
from rich.text import Text
from rich.style import Style


class ProjectItem(ListItem):
    """A project list item."""

    def __init__(self, name: str, description: str = "", active: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.project_name = name
        self.description = description
        self.active = active

    def compose(self):
        """Compose the project item."""
        text = Text()
        if self.active:
            text.append("● ", style=Style(color="#32CD32"))
        else:
            text.append("○ ", style=Style(color="#8b949e"))

        text.append(self.project_name, style=Style(color="#00CED1", bold=True))

        if self.description:
            text.append(f"  {self.description}", style=Style(color="#8b949e"))

        yield Static(text)


class ProjectsScreen(Screen):
    """
    Projects screen for managing Cilow projects.

    Features:
    - List projects
    - Create new project
    - Switch active project
    - Delete projects
    - Project-specific memory isolation
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("n", "new_project", "New Project"),
        Binding("d", "delete_project", "Delete"),
        Binding("enter", "select_project", "Select"),
    ]

    DEFAULT_CSS = """
    ProjectsScreen {
        background: #0d1117;
    }

    #projects-header {
        dock: top;
        height: 3;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 2;
        content-align: left middle;
    }

    #projects-title {
        color: #00CED1;
        text-style: bold;
    }

    #projects-container {
        padding: 2;
    }

    #project-list {
        height: 1fr;
        background: #0d1117;
        border: solid #30363d;
        padding: 1;
    }

    ProjectItem {
        padding: 1;
        background: #161b22;
        margin-bottom: 1;
    }

    ProjectItem:hover {
        background: #21262d;
    }

    ProjectItem.-selected {
        background: #21262d;
        border-left: thick #00CED1;
    }

    #new-project-container {
        height: auto;
        padding: 1;
        background: #161b22;
        border: solid #30363d;
        margin-top: 1;
    }

    #button-row {
        dock: bottom;
        height: 3;
        padding: 0 2;
        background: #161b22;
        border-top: solid #30363d;
    }

    .section-label {
        color: #00CED1;
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.projects = [
            {"name": "Default", "description": "Default project", "active": True},
            {"name": "my-app", "description": "My application project", "active": False},
            {"name": "research", "description": "Research notes and findings", "active": False},
        ]

    def compose(self):
        """Compose the projects screen."""
        # Header
        with Container(id="projects-header"):
            yield Static("Projects", id="projects-title")

        # Main container
        with Container(id="projects-container"):
            yield Static("Your Projects", classes="section-label")
            yield Static("Select a project to switch context. Each project has isolated memories.",
                        style="color: #8b949e;")

            # Project list
            with ListView(id="project-list"):
                for project in self.projects:
                    yield ProjectItem(
                        name=project["name"],
                        description=project["description"],
                        active=project["active"],
                    )

            # New project input
            with Vertical(id="new-project-container"):
                yield Static("Create New Project", classes="section-label")
                with Horizontal():
                    yield Input(
                        placeholder="Project name...",
                        id="new-project-input"
                    )
                    yield Button("Create", variant="primary", id="create-btn")

        # Button row
        with Horizontal(id="button-row"):
            yield Button("Back", variant="default", id="back-btn")
            yield Button("Delete Selected", variant="error", id="delete-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id == "create-btn":
            self._create_project()
        elif event.button.id == "delete-btn":
            self._delete_selected()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle project selection."""
        if isinstance(event.item, ProjectItem):
            self._select_project(event.item.project_name)

    def _create_project(self) -> None:
        """Create a new project."""
        input_widget = self.query_one("#new-project-input", Input)
        name = input_widget.value.strip()

        if not name:
            self.app.notify("Please enter a project name", severity="warning")
            return

        # Check for duplicates
        if any(p["name"] == name for p in self.projects):
            self.app.notify(f"Project '{name}' already exists", severity="warning")
            return

        # Add project
        self.projects.append({
            "name": name,
            "description": "New project",
            "active": False,
        })

        # Refresh list
        self._refresh_list()
        input_widget.value = ""
        self.app.notify(f"Created project: {name}")

    def _select_project(self, name: str) -> None:
        """Select and activate a project."""
        for project in self.projects:
            project["active"] = (project["name"] == name)

        self._refresh_list()
        self.app.notify(f"Switched to project: {name}")

    def _delete_selected(self) -> None:
        """Delete the selected project."""
        list_view = self.query_one("#project-list", ListView)
        selected = list_view.highlighted_child

        if isinstance(selected, ProjectItem):
            name = selected.project_name

            if name == "Default":
                self.app.notify("Cannot delete the Default project", severity="warning")
                return

            # Remove project
            self.projects = [p for p in self.projects if p["name"] != name]

            # If deleted was active, switch to Default
            if selected.active:
                for p in self.projects:
                    if p["name"] == "Default":
                        p["active"] = True
                        break

            self._refresh_list()
            self.app.notify(f"Deleted project: {name}")

    def _refresh_list(self) -> None:
        """Refresh the project list."""
        list_view = self.query_one("#project-list", ListView)
        list_view.clear()

        for project in self.projects:
            list_view.append(
                ProjectItem(
                    name=project["name"],
                    description=project["description"],
                    active=project["active"],
                )
            )

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_new_project(self) -> None:
        """Focus the new project input."""
        self.query_one("#new-project-input", Input).focus()

    def action_delete_project(self) -> None:
        """Delete selected project."""
        self._delete_selected()

    def action_select_project(self) -> None:
        """Select the highlighted project."""
        list_view = self.query_one("#project-list", ListView)
        selected = list_view.highlighted_child

        if isinstance(selected, ProjectItem):
            self._select_project(selected.project_name)
