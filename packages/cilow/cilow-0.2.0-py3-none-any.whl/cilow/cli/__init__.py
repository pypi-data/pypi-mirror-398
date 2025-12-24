"""
Cilow CLI Agent - AI Memory Assistant

A professional CLI agent with persistent memory powered by Textual.

Usage:
    cilow                   # Launch CLI agent (TUI)
    cilow --model gpt       # Use OpenAI GPT
    cilow --model claude    # Use Anthropic Claude
    cilow-mcp               # Run MCP server for Claude Code/Cursor

Environment Variables:
    ANTHROPIC_API_KEY - Anthropic API key for Claude
    OPENAI_API_KEY - OpenAI API key for GPT
    CILOW_URL - Cilow API URL (default: http://localhost:8080)
    CILOW_API_KEY - Cilow API key (from dashboard.cilow.ai)
"""

from .app import CilowApp, main
from .llm_providers import LLMProvider, AnthropicProvider, OpenAIProvider
from .memory_manager import MemoryManager

__all__ = [
    # TUI App
    "CilowApp",
    "main",
    # Providers
    "LLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    # Core components
    "MemoryManager",
]
