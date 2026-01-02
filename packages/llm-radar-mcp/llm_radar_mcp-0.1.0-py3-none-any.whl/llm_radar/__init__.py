"""
LLM Radar - Real-time AI Model Intelligence MCP Server

Provides up-to-date information about LLM models from OpenAI, Anthropic, and Google
including pricing, capabilities, and recommendations.
"""

__version__ = "0.1.0"

from .mcp_server import create_server, main

__all__ = ["create_server", "main", "__version__"]
