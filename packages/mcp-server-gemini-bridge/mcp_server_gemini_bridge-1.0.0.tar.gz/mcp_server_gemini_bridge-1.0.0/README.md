# MCP Server Gemini Bridge

**Use Google Gemini from any MCP-compatible AI client.**

Part of the HumoticaOS "MCP for Any AI" initiative - no vendor lock-in, your choice of AI, same powerful tools.

## Why?

Different AIs have different strengths. Gemini excels at:
- Visual understanding and image analysis
- Creative brainstorming
- Broad knowledge synthesis
- Cross-checking and validation

With this bridge, Claude can ask Gemini for a second opinion. Or any MCP client can leverage Gemini's unique capabilities.

## Installation

```bash
pip install mcp-server-gemini-bridge
```

## Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "python3",
      "args": ["-m", "mcp_server_gemini_bridge"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here",
        "GEMINI_MODEL": "gemini-2.0-flash-exp"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `gemini_chat` | General chat with Gemini |
| `gemini_analyze_image` | Visual analysis of images |
| `gemini_brainstorm` | Creative idea generation |
| `gemini_cross_check` | Review and validate content |

## Examples

**AI-to-AI Cross-Validation:**
```
gemini_cross_check(
    content="The Earth is the third planet from the Sun...",
    focus="accuracy"
)
```

**Creative Brainstorming:**
```
gemini_brainstorm(
    topic="sustainable packaging solutions",
    constraints="must be biodegradable and cost-effective"
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
