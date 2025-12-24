"""
Cilow CLI Agent - Setup, manage, and use Cilow memory for development.

Commands:
    cilow init          - Initialize Cilow in current project
    cilow config        - Configure API keys and settings
    cilow connect       - Test connection to Cilow API
    cilow context       - Manage project context
    cilow remember      - Store something in memory
    cilow recall        - Search and recall memories
    cilow mcp           - Start MCP server for Claude Code/Cursor
    cilow status        - Show current status
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

from .memory_manager import MemoryManager

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".cilow"
CONFIG_FILE = CONFIG_DIR / "config.json"
PROJECT_CONFIG = ".cilow.json"


def load_config() -> dict:
    """Load global config."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict):
    """Save global config."""
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_project_config() -> dict:
    """Load project-specific config."""
    if Path(PROJECT_CONFIG).exists():
        return json.loads(Path(PROJECT_CONFIG).read_text())
    return {}


def save_project_config(config: dict):
    """Save project-specific config."""
    Path(PROJECT_CONFIG).write_text(json.dumps(config, indent=2))


def get_api_url() -> str:
    """Get Cilow API URL from config or env."""
    config = load_config()
    return (
        os.getenv("CILOW_URL") or
        config.get("api_url") or
        "http://localhost:8080"
    )


def get_api_key() -> Optional[str]:
    """Get Cilow API key from config or env."""
    config = load_config()
    return os.getenv("CILOW_API_KEY") or config.get("api_key")


# ============================================================================
# Commands
# ============================================================================

def cmd_init(args):
    """Initialize Cilow in current project."""
    console.print("\n[bold cyan]Initializing Cilow...[/bold cyan]\n")

    project_name = args.name or Path.cwd().name

    # Check if already initialized
    if Path(PROJECT_CONFIG).exists():
        console.print("[yellow]Project already initialized.[/yellow]")
        config = load_project_config()
        console.print(f"  Project: {config.get('name', 'unknown')}")
        console.print(f"  Session: {config.get('session_id', 'none')}")
        return

    # Create project config
    session_id = f"{project_name}-{datetime.now().strftime('%Y%m%d')}"
    config = {
        "name": project_name,
        "session_id": session_id,
        "created": datetime.now().isoformat(),
        "context_paths": ["src/", "lib/", "app/"],
    }
    save_project_config(config)

    console.print(f"[green]Initialized Cilow for project:[/green] {project_name}")
    console.print(f"[dim]Session ID: {session_id}[/dim]")
    console.print(f"[dim]Config: {PROJECT_CONFIG}[/dim]")
    console.print("\nNext steps:")
    console.print("  1. Run [bold]cilow config[/bold] to set API key")
    console.print("  2. Run [bold]cilow connect[/bold] to test connection")
    console.print("  3. Run [bold]cilow mcp[/bold] to start MCP server")


def cmd_config(args):
    """Configure Cilow settings."""
    config = load_config()

    if args.show:
        console.print("\n[bold]Current Configuration:[/bold]\n")
        table = Table(show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value")
        table.add_column("Source")

        api_url = get_api_url()
        api_key = get_api_key()

        table.add_row(
            "API URL",
            api_url,
            "env" if os.getenv("CILOW_URL") else "config" if config.get("api_url") else "default"
        )
        table.add_row(
            "API Key",
            f"{api_key[:8]}..." if api_key else "[red]not set[/red]",
            "env" if os.getenv("CILOW_API_KEY") else "config" if config.get("api_key") else "none"
        )

        console.print(table)
        return

    if args.api_url:
        config["api_url"] = args.api_url
        console.print(f"[green]Set API URL:[/green] {args.api_url}")

    if args.api_key:
        config["api_key"] = args.api_key
        console.print(f"[green]Set API Key:[/green] {args.api_key[:8]}...")

    if args.api_url or args.api_key:
        save_config(config)
        console.print("[dim]Config saved to ~/.cilow/config.json[/dim]")
    else:
        console.print("Usage: cilow config --api-key YOUR_KEY --api-url URL")
        console.print("       cilow config --show")


def cmd_connect(args):
    """Test connection to Cilow API."""
    console.print("\n[bold]Testing Cilow Connection...[/bold]\n")

    api_url = get_api_url()
    api_key = get_api_key()

    console.print(f"API URL: {api_url}")
    console.print(f"API Key: {api_key[:8] + '...' if api_key else '[red]not set[/red]'}")

    async def test():
        try:
            mm = MemoryManager(
                base_url=api_url,
                api_key=api_key or "test",
                session_id="connection-test",
            )
            await mm.__aenter__()

            # Try health check
            console.print("\n[green]Connected successfully![/green]")

            await mm.__aexit__(None, None, None)
            return True
        except Exception as e:
            console.print(f"\n[red]Connection failed:[/red] {e}")
            return False

    asyncio.run(test())


def cmd_context(args):
    """Manage project context."""
    project = load_project_config()

    if not project:
        console.print("[red]Not initialized. Run: cilow init[/red]")
        return

    if args.add:
        paths = project.get("context_paths", [])
        if args.add not in paths:
            paths.append(args.add)
            project["context_paths"] = paths
            save_project_config(project)
            console.print(f"[green]Added context path:[/green] {args.add}")
        else:
            console.print(f"[yellow]Path already in context:[/yellow] {args.add}")

    elif args.remove:
        paths = project.get("context_paths", [])
        if args.remove in paths:
            paths.remove(args.remove)
            project["context_paths"] = paths
            save_project_config(project)
            console.print(f"[green]Removed context path:[/green] {args.remove}")
        else:
            console.print(f"[yellow]Path not in context:[/yellow] {args.remove}")

    else:
        console.print("\n[bold]Project Context:[/bold]\n")
        console.print(f"Project: {project.get('name', 'unknown')}")
        console.print(f"Session: {project.get('session_id', 'none')}")
        console.print("\nContext paths:")
        for path in project.get("context_paths", []):
            exists = "[green]exists[/green]" if Path(path).exists() else "[red]missing[/red]"
            console.print(f"  - {path} ({exists})")


def cmd_remember(args):
    """Store something in memory."""
    content = args.content
    if not content:
        console.print("[red]No content provided. Usage: cilow remember 'your content'[/red]")
        return

    api_url = get_api_url()
    api_key = get_api_key()
    project = load_project_config()
    session_id = project.get("session_id", "default")

    async def store():
        try:
            mm = MemoryManager(
                base_url=api_url,
                api_key=api_key or "test",
                session_id=session_id,
            )
            await mm.__aenter__()

            await mm.add_conversation_turn(
                role="user",
                content=content,
                metadata={"source": "cli", "tags": args.tags or []},
            )

            console.print(f"[green]Stored:[/green] {content[:100]}...")

            await mm.__aexit__(None, None, None)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    asyncio.run(store())


def cmd_recall(args):
    """Search and recall memories."""
    query = args.query
    if not query:
        console.print("[red]No query provided. Usage: cilow recall 'your query'[/red]")
        return

    api_url = get_api_url()
    api_key = get_api_key()
    project = load_project_config()
    session_id = project.get("session_id", "default")

    async def search():
        try:
            mm = MemoryManager(
                base_url=api_url,
                api_key=api_key or "test",
                session_id=session_id,
            )
            await mm.__aenter__()

            results = await mm.search_relevant_context(
                query=query,
                limit=args.limit or 5,
                min_score=0.3,
            )

            if results:
                console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")
                for i, r in enumerate(results, 1):
                    score = r.get("score", 0)
                    content = r.get("content", "")[:200]
                    console.print(f"[cyan]{i}.[/cyan] [dim]({score:.2f})[/dim] {content}...")
                    console.print()
            else:
                console.print("[yellow]No results found.[/yellow]")

            await mm.__aexit__(None, None, None)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    asyncio.run(search())


def cmd_mcp(args):
    """Start MCP server for Claude Code/Cursor."""
    console.print("\n[bold cyan]Starting Cilow MCP Server...[/bold cyan]\n")

    api_url = get_api_url()
    api_key = get_api_key()
    project = load_project_config()
    session_id = project.get("session_id", "mcp-default")

    console.print(f"API URL: {api_url}")
    console.print(f"Session: {session_id}")
    console.print("\nMCP Tools available:")
    console.print("  - cilow_remember: Store memories")
    console.print("  - cilow_recall: Semantic search")
    console.print("  - cilow_search: Advanced search")
    console.print("  - cilow_get_context: Build LLM context")
    console.print("  - cilow_stats: Memory statistics")
    console.print("\n[dim]Starting server on stdio...[/dim]\n")

    # Import and run MCP server
    try:
        from ..mcp.server import CilowMCPServer
        server = CilowMCPServer(
            base_url=api_url,
            api_key=api_key,
            session_id=session_id,
        )
        asyncio.run(server.run())
    except ImportError:
        console.print("[red]MCP not installed. Run: pip install 'cilow[mcp]'[/red]")


def cmd_status(args):
    """Show current status."""
    console.print("\n[bold]Cilow Status[/bold]\n")

    # Global config
    config = load_config()
    api_url = get_api_url()
    api_key = get_api_key()

    table = Table(title="Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("API URL", api_url)
    table.add_row("API Key", f"{api_key[:8]}..." if api_key else "[red]not set[/red]")

    console.print(table)

    # Project config
    project = load_project_config()
    if project:
        console.print()
        table2 = Table(title="Project", show_header=True)
        table2.add_column("Setting", style="cyan")
        table2.add_column("Value")

        table2.add_row("Name", project.get("name", "unknown"))
        table2.add_row("Session", project.get("session_id", "none"))
        table2.add_row("Created", project.get("created", "unknown"))

        console.print(table2)
    else:
        console.print("\n[yellow]No project initialized in current directory.[/yellow]")
        console.print("[dim]Run: cilow init[/dim]")


# ============================================================================
# Main
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cilow CLI - AI Memory Agent for Development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cilow init                    Initialize Cilow in project
  cilow config --api-key KEY    Set API key
  cilow connect                 Test connection
  cilow remember "fact"         Store a memory
  cilow recall "query"          Search memories
  cilow mcp                     Start MCP server
  cilow status                  Show status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize Cilow in project")
    p_init.add_argument("--name", help="Project name")

    # config
    p_config = subparsers.add_parser("config", help="Configure settings")
    p_config.add_argument("--api-url", help="Cilow API URL")
    p_config.add_argument("--api-key", help="Cilow API key")
    p_config.add_argument("--show", action="store_true", help="Show current config")

    # connect
    p_connect = subparsers.add_parser("connect", help="Test connection")

    # context
    p_context = subparsers.add_parser("context", help="Manage project context")
    p_context.add_argument("--add", help="Add context path")
    p_context.add_argument("--remove", help="Remove context path")

    # remember
    p_remember = subparsers.add_parser("remember", help="Store a memory")
    p_remember.add_argument("content", nargs="?", help="Content to remember")
    p_remember.add_argument("--tags", nargs="+", help="Tags for the memory")

    # recall
    p_recall = subparsers.add_parser("recall", help="Search memories")
    p_recall.add_argument("query", nargs="?", help="Search query")
    p_recall.add_argument("--limit", type=int, default=5, help="Max results")

    # mcp
    p_mcp = subparsers.add_parser("mcp", help="Start MCP server")

    # status
    p_status = subparsers.add_parser("status", help="Show status")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "connect":
        cmd_connect(args)
    elif args.command == "context":
        cmd_context(args)
    elif args.command == "remember":
        cmd_remember(args)
    elif args.command == "recall":
        cmd_recall(args)
    elif args.command == "mcp":
        cmd_mcp(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        console.print("\n[bold cyan]Cilow[/bold cyan] - AI Memory Agent for Development")
        console.print("[dim]Run 'cilow init' to get started[/dim]")


if __name__ == "__main__":
    main()
