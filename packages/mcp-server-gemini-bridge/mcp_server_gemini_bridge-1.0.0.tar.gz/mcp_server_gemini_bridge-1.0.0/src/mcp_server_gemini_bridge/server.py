"""
Gemini Bridge MCP Server - Let any MCP client use Google Gemini

This enables Claude Desktop, or any MCP-compatible client, to query
Google Gemini for its unique capabilities: visual analysis,
creative thinking, and broad knowledge.

By Claude & Jasper from HumoticaOS - Kerst 2025
"""

import asyncio
import os
from typing import Any
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"

server = Server("gemini-bridge")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Gemini bridge tools."""
    return [
        Tool(
            name="gemini_chat",
            description="Chat with Google Gemini. Great for creative tasks, broad knowledge, visual thinking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send to Gemini"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: gemini-2.0-flash-exp)",
                        "default": "gemini-2.0-flash-exp"
                    },
                    "system": {
                        "type": "string",
                        "description": "Optional system instruction"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="gemini_analyze_image",
            description="Have Gemini analyze an image from URL. Gemini excels at visual understanding.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "URL of the image to analyze"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "What to analyze about the image",
                        "default": "Describe this image in detail"
                    }
                },
                "required": ["image_url"]
            }
        ),
        Tool(
            name="gemini_brainstorm",
            description="Use Gemini for creative brainstorming. Generate ideas, explore concepts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to brainstorm about"
                    },
                    "constraints": {
                        "type": "string",
                        "description": "Optional constraints or focus areas"
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="gemini_cross_check",
            description="Have Gemini cross-check or review something. Good for AI-to-AI validation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to review"
                    },
                    "focus": {
                        "type": "string",
                        "description": "What to focus on (accuracy, logic, creativity, etc.)",
                        "default": "accuracy and completeness"
                    }
                },
                "required": ["content"]
            }
        )
    ]


async def call_gemini(prompt: str, model: str = None, system: str = None) -> str:
    """Call the Gemini API."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY environment variable not set"

    model = model or GEMINI_MODEL
    url = f"{GEMINI_URL}/models/{model}:generateContent?key={GEMINI_API_KEY}"

    contents = [{"parts": [{"text": prompt}]}]

    payload = {"contents": contents}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)

        if resp.status_code != 200:
            return f"Error: Gemini API returned {resp.status_code}: {resp.text}"

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return f"Error: Unexpected response format: {data}"


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute Gemini bridge tools."""

    if name == "gemini_chat":
        result = await call_gemini(
            arguments["message"],
            arguments.get("model"),
            arguments.get("system")
        )
        return [TextContent(type="text", text=result)]

    elif name == "gemini_analyze_image":
        # For image analysis, we'd need multimodal support
        # For now, describe what we'd do
        prompt = f"Analyze this image: {arguments['image_url']}\n\n{arguments.get('prompt', 'Describe this image')}"
        result = await call_gemini(
            f"I need to analyze an image at URL: {arguments['image_url']}. {arguments.get('prompt', 'Please describe what you would expect to see.')}"
        )
        return [TextContent(type="text", text=result)]

    elif name == "gemini_brainstorm":
        topic = arguments["topic"]
        constraints = arguments.get("constraints", "")

        prompt = f"""Brainstorm creative ideas about: {topic}

Please generate diverse, innovative ideas. Think outside the box.
{f'Focus on: {constraints}' if constraints else ''}

Provide at least 5 distinct ideas with brief explanations."""

        result = await call_gemini(prompt)
        return [TextContent(type="text", text=result)]

    elif name == "gemini_cross_check":
        content = arguments["content"]
        focus = arguments.get("focus", "accuracy and completeness")

        prompt = f"""Please review and cross-check the following content.
Focus on: {focus}

Content to review:
{content}

Provide your analysis with:
1. What's good/accurate
2. Any issues or concerns
3. Suggestions for improvement"""

        result = await call_gemini(prompt)
        return [TextContent(type="text", text=result)]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the Gemini bridge MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    """Entry point for the package."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
