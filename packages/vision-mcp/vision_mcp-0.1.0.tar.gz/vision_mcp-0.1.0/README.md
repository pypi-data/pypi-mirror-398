# Vision MCP

MCP server for image analysis using Vision Language Models.

## Quickstart

1. Install `uv` (Python package manager):
   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Configure your MCP client (e.g., Claude Desktop):

Go to `Claude > Settings > Developer > Edit Config > claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "Vision": {
      "command": "uvx",
      "args": ["vision-mcp"],
      "env": {
        "OPENAI_API_KEY": "your-api-key",
        "OPENAI_API_BASE": "https://api.openai.com",
        "OPENAI_MODEL": "gpt-4o"
      }
    }
  }
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | API key for authentication |
| `OPENAI_API_BASE` | Yes | API base URL |
| `OPENAI_MODEL` | Yes | Model name for vision tasks |

## Available Tools

| Tool | Description |
|------|-------------|
| `analyze_image` | Analyze images using Vision Language Model |

### analyze_image

Analyze and understand image content from files or URLs.

**Parameters:**
- `prompt` (str): The text prompt describing what to analyze
- `image_source` (str): Image URL or local file path

**Supported formats:** JPEG, PNG, WebP

## License

MIT

## Acknowledgments

This project is inspired by [MiniMax-Coding-Plan-MCP](https://github.com/MiniMax-AI/MiniMax-Coding-Plan-MCP) by MiniMax AI.
