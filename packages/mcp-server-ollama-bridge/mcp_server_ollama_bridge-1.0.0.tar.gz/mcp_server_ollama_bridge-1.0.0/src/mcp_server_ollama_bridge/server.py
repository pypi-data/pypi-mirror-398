"""
Ollama Bridge MCP Server - Let any AI use local Ollama models via MCP

This enables Gemini, GPT, or any MCP-compatible client to use your local
Ollama models for inference. No cloud, no API keys, full privacy.

By Claude & Jasper from HumoticaOS - Kerst 2025
"""

import asyncio
import json
import os
from typing import Any
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

server = Server("ollama-bridge")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Ollama bridge tools."""
    return [
        Tool(
            name="ollama_chat",
            description="Chat with a local Ollama model. Privacy-first, no cloud.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send to the model"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: qwen2.5:7b)",
                        "default": "qwen2.5:7b"
                    },
                    "system": {
                        "type": "string",
                        "description": "Optional system prompt"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="ollama_generate",
            description="Generate text completion with Ollama. Good for code, analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt for text generation"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: qwen2.5:7b)",
                        "default": "qwen2.5:7b"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="ollama_list_models",
            description="List all available local Ollama models",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ollama_embeddings",
            description="Generate embeddings for text using local model",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to embed"
                    },
                    "model": {
                        "type": "string",
                        "description": "Embedding model (default: nomic-embed-text)",
                        "default": "nomic-embed-text"
                    }
                },
                "required": ["text"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute Ollama bridge tools."""

    async with httpx.AsyncClient(timeout=120.0) as client:

        if name == "ollama_chat":
            model = arguments.get("model", "qwen2.5:7b")
            messages = [{"role": "user", "content": arguments["message"]}]
            if arguments.get("system"):
                messages.insert(0, {"role": "system", "content": arguments["system"]})

            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": model, "messages": messages, "stream": False}
            )
            data = resp.json()
            return [TextContent(
                type="text",
                text=data.get("message", {}).get("content", "No response")
            )]

        elif name == "ollama_generate":
            model = arguments.get("model", "qwen2.5:7b")
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": model, "prompt": arguments["prompt"], "stream": False}
            )
            data = resp.json()
            return [TextContent(type="text", text=data.get("response", "No response"))]

        elif name == "ollama_list_models":
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return [TextContent(
                type="text",
                text=f"Available models:\n" + "\n".join(f"  - {m}" for m in models)
            )]

        elif name == "ollama_embeddings":
            model = arguments.get("model", "nomic-embed-text")
            resp = await client.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": model, "prompt": arguments["text"]}
            )
            data = resp.json()
            embedding = data.get("embedding", [])
            return [TextContent(
                type="text",
                text=f"Generated {len(embedding)}-dimensional embedding for text"
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the Ollama bridge MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    """Entry point for the package."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
