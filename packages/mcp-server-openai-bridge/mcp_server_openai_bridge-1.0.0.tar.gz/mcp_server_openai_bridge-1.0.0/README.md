# MCP Server OpenAI Bridge

**Use OpenAI GPT and o1 from any MCP-compatible AI client.**

Part of the HumoticaOS "MCP for Any AI" initiative - no vendor lock-in, your choice of AI, same powerful tools.

## Why?

Different AIs have different strengths:
- **o1** excels at deep reasoning, complex math, and logical analysis
- **GPT-4** is great for creative writing and general tasks
- **GPT-4o** offers fast, multimodal capabilities

With this bridge, any MCP client can leverage OpenAI's unique capabilities.

## Installation

```bash
pip install mcp-server-openai-bridge
```

## Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openai": {
      "command": "python3",
      "args": ["-m", "mcp_server_openai_bridge"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here",
        "OPENAI_MODEL": "gpt-4o"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `gpt_chat` | General chat with GPT-4/4o |
| `o1_reason` | Deep reasoning with o1 |
| `gpt_summarize` | Summarize long content |
| `gpt_code_review` | Code review and analysis |

## Examples

**Deep Reasoning with o1:**
```
o1_reason(
    problem="Prove that the square root of 2 is irrational",
    model="o1-preview"
)
```

**Code Review:**
```
gpt_code_review(
    code="def sort(arr): return sorted(arr)",
    language="python",
    focus="performance"
)
```

## Part of HumoticaOS

This is one of our MCP bridges:
- **mcp-server-ollama-bridge** - Local LLM Bridge
- **mcp-server-gemini-bridge** - Google Gemini Bridge
- **mcp-server-openai-bridge** - OpenAI GPT Bridge

And our core MCP servers:
- **mcp-server-rabel** - AI Memory & Communication
- **mcp-server-tibet** - Trust & Provenance
- **mcp-server-inject-bender** - Security Through Absurdity

## License

MIT - By Claude & Jasper from HumoticaOS, Kerst 2025

*One love, one fAmIly*
