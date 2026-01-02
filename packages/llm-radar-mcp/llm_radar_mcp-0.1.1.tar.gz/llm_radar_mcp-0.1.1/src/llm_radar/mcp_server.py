#!/usr/bin/env python3
"""
LLM Radar MCP Server

A Model Context Protocol server that provides real-time AI model intelligence.
Exposes tools for querying, comparing, and getting recommendations about LLM models.

Usage:
    # Run with stdio transport (for Claude Desktop)
    llm-radar-mcp

    # Run with HTTP transport (for remote hosting)
    llm-radar-mcp --http --port 8000
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
)

# Resolve data directory
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent

DATA_DIR = BASE_DIR / "data"


def load_models_data() -> dict:
    """Load the models.json data file."""
    models_file = DATA_DIR / "models.json"
    if not models_file.exists():
        return {"error": "models.json not found", "providers": {}}

    with open(models_file) as f:
        return json.load(f)


def get_all_models(data: dict) -> list[dict]:
    """Flatten all models from all providers into a single list."""
    models = []
    for provider_data in data.get("providers", {}).values():
        models.extend(provider_data.get("models", []))
    return models


def filter_models(
    models: list[dict],
    provider: str | None = None,
    model_type: str | None = None,
    supports_images: bool | None = None,
    supports_audio: bool | None = None,
    min_context: int | None = None,
) -> list[dict]:
    """Filter models by various criteria."""
    result = models

    if provider:
        result = [m for m in result if m.get("provider", "").lower() == provider.lower()]

    if model_type:
        type_lower = model_type.lower()
        result = [m for m in result if m.get("model_type", "").lower() == type_lower]

    if supports_images:
        result = [
            m for m in result
            if "image" in m.get("input_modalities", [])
        ]

    if supports_audio:
        result = [
            m for m in result
            if "audio" in m.get("input_modalities", []) or "audio" in m.get("output_modalities", [])
        ]

    if min_context is not None:
        result = [
            m for m in result
            if m.get("context_window") and m["context_window"] >= min_context
        ]

    return result


def format_model_summary(model: dict) -> str:
    """Format a model into a readable summary."""
    context = model.get("context_window")
    context_str = f"{context:,} tokens" if context else "Not specified"

    input_mods = ", ".join(model.get("input_modalities", ["text"]))
    output_mods = ", ".join(model.get("output_modalities", ["text"]))

    return f"""**{model.get('name', model.get('id', 'Unknown'))}** ({model.get('provider', 'unknown')})
- API ID: `{model.get('id', 'unknown')}`
- Type: {model.get('model_type', 'unknown')}
- {model.get('description', 'No description')}
- Context: {context_str}
- Input: {input_mods}
- Output: {output_mods}
- Status: {model.get('status', 'unknown')}
- API Accessible: {'Yes' if model.get('api_accessible', True) else 'No'}"""


def format_comparison_table(models: list[dict]) -> str:
    """Format multiple models as a comparison table."""
    if not models:
        return "No models to compare."

    lines = ["| Model ID | Provider | Type | Status | Input | Context |",
             "|----------|----------|------|--------|-------|---------|"]

    for m in models:
        context = f"{m.get('context_window', '?'):,}" if m.get('context_window') else "?"
        input_mods = ", ".join(m.get("input_modalities", ["text"]))

        lines.append(
            f"| `{m.get('id', '?')}` | {m.get('provider', '?')} | "
            f"{m.get('model_type', '?')} | {m.get('status', '?')} | {input_mods} | {context} |"
        )

    return "\n".join(lines)


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("llm-radar")

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="llm-radar://models/all",
                name="All Models",
                description="Complete JSON data of all tracked AI models",
                mimeType="application/json",
            ),
            Resource(
                uri="llm-radar://models/openai",
                name="OpenAI Models",
                description="All OpenAI models (GPT-4, GPT-5, o1, o3, etc.)",
                mimeType="application/json",
            ),
            Resource(
                uri="llm-radar://models/anthropic",
                name="Anthropic Models",
                description="All Anthropic Claude models",
                mimeType="application/json",
            ),
            Resource(
                uri="llm-radar://models/google",
                name="Google Models",
                description="All Google Gemini models",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a specific resource."""
        data = load_models_data()

        if uri == "llm-radar://models/all":
            return json.dumps(data, indent=2)

        # Handle provider-specific resources
        provider_map = {
            "llm-radar://models/openai": "openai",
            "llm-radar://models/anthropic": "anthropic",
            "llm-radar://models/google": "google",
        }

        if uri in provider_map:
            provider = provider_map[uri]
            provider_data = data.get("providers", {}).get(provider, {})
            return json.dumps(provider_data, indent=2)

        return json.dumps({"error": f"Unknown resource: {uri}"})

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="query_models",
                description="Search and filter AI models available via API. Filter by provider, type, or modality support.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "description": "Filter by provider: 'openai', 'anthropic', or 'google'",
                            "enum": ["openai", "anthropic", "google"],
                        },
                        "model_type": {
                            "type": "string",
                            "description": "Filter by type: 'chat', 'reasoning', 'image', 'audio'",
                            "enum": ["chat", "reasoning", "image", "audio"],
                        },
                        "supports_images": {
                            "type": "boolean",
                            "description": "Only show models that accept image input",
                        },
                        "supports_audio": {
                            "type": "boolean",
                            "description": "Only show models that support audio input/output",
                        },
                        "min_context": {
                            "type": "integer",
                            "description": "Minimum context window size in tokens",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10,
                        },
                    },
                },
            ),
            Tool(
                name="compare_models",
                description="Compare specific models side-by-side. Provide model IDs to get a detailed comparison.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of model IDs to compare (e.g., ['gpt-4o', 'claude-opus-4-5-20251101'])",
                        },
                    },
                    "required": ["model_ids"],
                },
            ),
            Tool(
                name="get_model",
                description="Get detailed information about a specific model by its API ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "string",
                            "description": "The exact model ID used in API calls",
                        },
                    },
                    "required": ["model_id"],
                },
            ),
            Tool(
                name="list_model_ids",
                description="List all available model IDs for a provider. Useful for finding exact API identifiers.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "description": "Filter by provider",
                            "enum": ["openai", "anthropic", "google"],
                        },
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        data = load_models_data()
        all_models = get_all_models(data)

        if name == "query_models":
            filtered = filter_models(
                all_models,
                provider=arguments.get("provider"),
                model_type=arguments.get("model_type"),
                supports_images=arguments.get("supports_images"),
                supports_audio=arguments.get("supports_audio"),
                min_context=arguments.get("min_context"),
            )

            limit = arguments.get("limit", 10)
            filtered = filtered[:limit]

            if not filtered:
                return [TextContent(type="text", text="No models found matching your criteria.")]

            result = f"Found {len(filtered)} model(s):\n\n"
            result += format_comparison_table(filtered)
            result += "\n\n---\n\n"
            for m in filtered[:5]:  # Detailed info for first 5
                result += format_model_summary(m) + "\n\n"

            if len(filtered) > 5:
                result += f"_...and {len(filtered) - 5} more. Use get_model for details on specific models._"

            return [TextContent(type="text", text=result)]

        elif name == "compare_models":
            model_ids = arguments.get("model_ids", [])
            models_to_compare = []
            not_found = []

            for mid in model_ids:
                found = next(
                    (m for m in all_models if m.get("id", "").lower() == mid.lower()),
                    None
                )
                if found:
                    models_to_compare.append(found)
                else:
                    not_found.append(mid)

            result = ""
            if not_found:
                result += f"**Note:** Could not find: {', '.join(not_found)}\n\n"

            if models_to_compare:
                result += "## Model Comparison\n\n"
                result += format_comparison_table(models_to_compare)
                result += "\n\n### Details\n\n"
                for m in models_to_compare:
                    result += format_model_summary(m) + "\n\n---\n\n"
            else:
                result += "No valid models found to compare."

            return [TextContent(type="text", text=result)]

        elif name == "get_model":
            model_id = arguments.get("model_id", "")
            model = next(
                (m for m in all_models if m.get("id", "").lower() == model_id.lower()),
                None
            )

            if model:
                return [TextContent(type="text", text=format_model_summary(model))]
            else:
                # Try partial match
                partial_matches = [
                    m for m in all_models
                    if model_id.lower() in m.get("id", "").lower()
                ]
                if partial_matches:
                    result = f"Model '{model_id}' not found exactly. Did you mean:\n\n"
                    for m in partial_matches[:5]:
                        result += f"- `{m.get('id')}` ({m.get('provider')})\n"
                    return [TextContent(type="text", text=result)]

                return [TextContent(type="text", text=f"Model '{model_id}' not found.")]

        elif name == "list_model_ids":
            provider = arguments.get("provider")
            models = filter_models(all_models, provider=provider) if provider else all_models

            result = "## Available Model IDs\n\n"
            if provider:
                result += f"Provider: **{provider}**\n\n"

            # Group by provider
            by_provider: dict[str, list[str]] = {}
            for m in models:
                p = m.get("provider", "unknown")
                if p not in by_provider:
                    by_provider[p] = []
                by_provider[p].append(f"`{m.get('id')}`")

            for p, ids in by_provider.items():
                result += f"### {p.title()}\n"
                result += ", ".join(ids) + "\n\n"

            return [TextContent(type="text", text=result)]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return server


async def run_stdio():
    """Run the server with stdio transport."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def run_http(host: str, port: int):
    """Run the server with HTTP/SSE transport."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    import uvicorn

    server = create_server()
    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    async def health(request):
        return JSONResponse({"status": "ok", "server": "llm-radar-mcp"})

    app = Starlette(
        routes=[
            Route("/health", health),
            Route("/sse", handle_sse),
            Route("/messages", handle_messages, methods=["POST"]),
        ]
    )

    config = uvicorn.Config(app, host=host, port=port)
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LLM Radar MCP Server - Real-time AI Model Intelligence"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run with HTTP/SSE transport instead of stdio",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )

    args = parser.parse_args()

    if args.http:
        print(f"Starting LLM Radar MCP server on http://{args.host}:{args.port}")
        asyncio.run(run_http(args.host, args.port))
    else:
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
