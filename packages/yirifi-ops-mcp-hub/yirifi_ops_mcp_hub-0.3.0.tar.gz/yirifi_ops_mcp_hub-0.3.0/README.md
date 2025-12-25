# yirifi-ops-mcp-hub

MCP (Model Context Protocol) servers for Yirifi Ops - expose REST APIs as MCP tools for AI assistants like Claude.

## Installation

```bash
# Using pip
pip install yirifi-ops-mcp-hub

# Using uv (recommended)
uv pip install yirifi-ops-mcp-hub
```

## Quick Start

### Claude Code Configuration

Add to your Claude Code MCP settings (`~/.claude.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "yirifi-ops": {
      "command": "yirifi-ops-mcp-hub",
      "env": {
        "YIRIFI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### CLI Options

```bash
# Run with all services (default)
YIRIFI_API_KEY=your_key yirifi-ops-mcp-hub

# Run specific service
YIRIFI_API_KEY=your_key yirifi-ops-mcp-hub --service=auth

# Development mode (localhost APIs)
YIRIFI_API_KEY=your_key yirifi-ops-mcp-hub --mode=dev

# HTTP transport (for remote deployment)
yirifi-ops-mcp-hub --transport=http --port=5200
```

**Options:**
- `--service`: `all` (default), `auth`, or `reg`
- `--mode`: `dev` (localhost) or `prd` (remote, default)
- `--transport`: `stdio` (default) or `http`
- `--port`: HTTP port (default: 5200)

### Utility Commands

```bash
# List available tools
yirifi-ops-mcp-hub list-tools

# Test API connection
yirifi-ops-mcp-hub test-connection --service=auth

# Show OpenAPI spec
yirifi-ops-mcp-hub show-spec --service=auth
```

## Architecture

This package uses a tiered exposure system for safe AI access:

- **DIRECT**: Safe, frequent operations exposed as individual MCP tools
- **GATEWAY**: Admin/dangerous operations accessible via `{service}_api_call` gateway tool
- **EXCLUDE**: Internal endpoints never exposed

## Environment Variables

- `YIRIFI_API_KEY`: API key for authentication (required)
- `AUTH_SERVICE_API_KEY`: Service-specific fallback for auth
- `REG_SERVICE_API_KEY`: Service-specific fallback for reg

## License

MIT
uv run yirifi-ops-mcp-hub --transport=http --port=5210 --mode=prd

uvx --refresh yirifi-ops-mcp-hub --version

⏺ Bash(curl -s -X POST 'https://mcp.ops.yirifi.ai/mcp/message' \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -H 'X-API-Key: yirifi_ops_8Ne_tU2wslZEtoeaD3TZJXmNuV7oyFT0bh1ZWFbsE9g' \
        -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","
      capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1)
