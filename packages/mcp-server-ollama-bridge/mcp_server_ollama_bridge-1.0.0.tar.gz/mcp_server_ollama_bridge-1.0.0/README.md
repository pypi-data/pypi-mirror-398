# MCP Server Ollama Bridge

**Use local Ollama models from any MCP-compatible AI client.**

Part of the HumoticaOS "MCP for Any AI" initiative - no vendor lock-in, your choice of AI, same powerful tools.

## Why?

MCP (Model Context Protocol) lets AI assistants use external tools. But what if you want to use Ollama's local models as part of your workflow? This bridge exposes Ollama to any MCP client.

**Use cases:**
- Let Claude Desktop query your local Qwen/Llama for sensitive data
- Have Gemini use your local models for embeddings
- Run hybrid workflows: cloud AI for creativity, local for privacy

## Installation

```bash
pip install mcp-server-ollama-bridge
```

## Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ollama": {
      "command": "python3",
      "args": ["-m", "mcp_server_ollama_bridge"],
      "env": {
        "OLLAMA_URL": "http://localhost:11434"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `ollama_chat` | Chat with local model (conversation style) |
| `ollama_generate` | Text completion (good for code) |
| `ollama_list_models` | List available local models |
| `ollama_embeddings` | Generate embeddings for semantic search |

## Examples

**Chat:**
```
ollama_chat(message="Explain quantum computing", model="qwen2.5:7b")
```

**Code generation:**
```
ollama_generate(prompt="Write a Python function to sort a list", model="qwen2.5:32b")
```

**Embeddings for RAG:**
```
ollama_embeddings(text="HumoticaOS is an AI orchestration platform")
```

## Part of HumoticaOS

This is one of our published MCP servers:
- **mcp-server-rabel** - AI Memory & Communication
- **mcp-server-tibet** - Trust & Provenance
- **mcp-server-inject-bender** - Security Through Absurdity
- **mcp-server-ollama-bridge** - Local LLM Bridge

## License

MIT - By Claude & Jasper from HumoticaOS, Kerst 2025

*One love, one fAmIly*
