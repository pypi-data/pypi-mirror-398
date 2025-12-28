"""
OpenAI Bridge MCP Server - Let any MCP client use OpenAI GPT and o1

This enables any MCP-compatible client to use OpenAI's models.
o1 excels at deep reasoning and complex analysis.
GPT-4 is great for creative writing and general tasks.

By Claude & Jasper from HumoticaOS - Kerst 2025
"""

import asyncio
import os
from typing import Any
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_URL = "https://api.openai.com/v1"

server = Server("openai-bridge")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available OpenAI bridge tools."""
    return [
        Tool(
            name="gpt_chat",
            description="Chat with GPT-4. Great for creative tasks, writing, general knowledge.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send to GPT"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: gpt-4o)",
                        "default": "gpt-4o"
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
            name="o1_reason",
            description="Use o1 for deep reasoning. Best for complex logic, math, analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem": {
                        "type": "string",
                        "description": "The problem to reason about"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: o1-preview)",
                        "default": "o1-preview"
                    }
                },
                "required": ["problem"]
            }
        ),
        Tool(
            name="gpt_summarize",
            description="Have GPT summarize content. Good for long documents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to summarize"
                    },
                    "style": {
                        "type": "string",
                        "description": "Summary style: brief, detailed, bullet-points",
                        "default": "brief"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="gpt_code_review",
            description="Have GPT review code for bugs, improvements, best practices.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to review"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "default": "python"
                    },
                    "focus": {
                        "type": "string",
                        "description": "What to focus on (bugs, performance, security, style)",
                        "default": "bugs and improvements"
                    }
                },
                "required": ["code"]
            }
        )
    ]


async def call_openai(messages: list, model: str = None) -> str:
    """Call the OpenAI API."""
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY environment variable not set"

    model = model or OPENAI_MODEL
    url = f"{OPENAI_URL}/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)

        if resp.status_code != 200:
            return f"Error: OpenAI API returned {resp.status_code}: {resp.text}"

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return f"Error: Unexpected response format: {data}"


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute OpenAI bridge tools."""

    if name == "gpt_chat":
        messages = []
        if arguments.get("system"):
            messages.append({"role": "system", "content": arguments["system"]})
        messages.append({"role": "user", "content": arguments["message"]})

        result = await call_openai(messages, arguments.get("model"))
        return [TextContent(type="text", text=result)]

    elif name == "o1_reason":
        # o1 doesn't support system prompts, just user messages
        messages = [{"role": "user", "content": arguments["problem"]}]

        result = await call_openai(messages, arguments.get("model", "o1-preview"))
        return [TextContent(type="text", text=result)]

    elif name == "gpt_summarize":
        style = arguments.get("style", "brief")
        style_instructions = {
            "brief": "Provide a brief 2-3 sentence summary.",
            "detailed": "Provide a detailed summary covering all main points.",
            "bullet-points": "Provide a summary as bullet points."
        }

        messages = [
            {"role": "system", "content": f"You are a summarization expert. {style_instructions.get(style, style_instructions['brief'])}"},
            {"role": "user", "content": f"Please summarize the following:\n\n{arguments['content']}"}
        ]

        result = await call_openai(messages)
        return [TextContent(type="text", text=result)]

    elif name == "gpt_code_review":
        language = arguments.get("language", "python")
        focus = arguments.get("focus", "bugs and improvements")

        messages = [
            {"role": "system", "content": f"You are an expert {language} code reviewer. Focus on: {focus}"},
            {"role": "user", "content": f"Please review this {language} code:\n\n```{language}\n{arguments['code']}\n```"}
        ]

        result = await call_openai(messages)
        return [TextContent(type="text", text=result)]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the OpenAI bridge MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    """Entry point for the package."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
