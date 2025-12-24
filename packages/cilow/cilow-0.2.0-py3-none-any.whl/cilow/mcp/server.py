"""Cilow MCP Server - Model Context Protocol server for memory integration."""

import os
import asyncio
import json
from typing import Optional, Any
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None

from ..cli.memory_manager import MemoryManager
from .tools import (
    cilow_remember,
    cilow_recall,
    cilow_search,
    cilow_get_context,
    cilow_stats,
)


class CilowMCPServer:
    """
    MCP Server for Cilow memory operations.

    Provides tools for:
    - cilow_remember: Store memories
    - cilow_recall: Semantic search
    - cilow_search: Advanced filtered search
    - cilow_get_context: Build LLM context
    - cilow_stats: Memory statistics
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP package not installed. Install with: pip install 'cilow[mcp]'"
            )

        self.base_url = base_url or os.getenv("CILOW_URL", "http://localhost:8080")
        self.api_key = api_key or os.getenv("CILOW_API_KEY", "test-api-key")
        self.session_id = session_id or f"mcp-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        self.server = Server("cilow-memory")
        self.memory_manager: Optional[MemoryManager] = None

        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools():
            """List available Cilow tools."""
            return [
                Tool(
                    name="cilow_remember",
                    description="Store a memory in Cilow. Use this to save important information, facts, preferences, or context that should be remembered for future conversations.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The content to remember",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional tags for categorization (e.g., 'preference', 'fact', 'project')",
                            },
                        },
                        "required": ["content"],
                    },
                ),
                Tool(
                    name="cilow_recall",
                    description="Search and recall memories from Cilow using semantic search. Use this to find relevant past information, preferences, or context.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="cilow_search",
                    description="Advanced memory search with filters. Use for specific lookups with tag or metadata filters.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query",
                            },
                            "filters": {
                                "type": "object",
                                "description": "Optional filters (tags, role, etc.)",
                                "properties": {
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "role": {
                                        "type": "string",
                                        "enum": ["user", "assistant"],
                                    },
                                },
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 10)",
                                "default": 10,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="cilow_get_context",
                    description="Build LLM-ready context from relevant memories. Returns a formatted context string ready for use in prompts.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The context query",
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum context size in tokens (default: 2000)",
                                "default": 2000,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="cilow_stats",
                    description="Get memory system statistics including connection status and memory counts.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            if not self.memory_manager:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Memory manager not initialized"})
                )]

            try:
                if name == "cilow_remember":
                    result = await cilow_remember(
                        self.memory_manager,
                        content=arguments["content"],
                        tags=arguments.get("tags"),
                    )
                elif name == "cilow_recall":
                    result = await cilow_recall(
                        self.memory_manager,
                        query=arguments["query"],
                        limit=arguments.get("limit", 5),
                    )
                elif name == "cilow_search":
                    result = await cilow_search(
                        self.memory_manager,
                        query=arguments["query"],
                        filters=arguments.get("filters"),
                        limit=arguments.get("limit", 10),
                    )
                elif name == "cilow_get_context":
                    result = await cilow_get_context(
                        self.memory_manager,
                        query=arguments["query"],
                        max_tokens=arguments.get("max_tokens", 2000),
                    )
                elif name == "cilow_stats":
                    result = await cilow_stats(self.memory_manager)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]

    async def run(self):
        """Run the MCP server."""
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            base_url=self.base_url,
            api_key=self.api_key,
            session_id=self.session_id,
        )
        await self.memory_manager.__aenter__()

        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )
        finally:
            await self.memory_manager.__aexit__(None, None, None)


def main():
    """Entry point for the Cilow MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Cilow MCP Server")
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

    if not MCP_AVAILABLE:
        print("Error: MCP package not installed.")
        print("Install with: pip install 'cilow[mcp]'")
        return 1

    server = CilowMCPServer(
        base_url=args.api_url,
        api_key=args.api_key,
        session_id=args.session,
    )

    asyncio.run(server.run())


if __name__ == "__main__":
    main()
