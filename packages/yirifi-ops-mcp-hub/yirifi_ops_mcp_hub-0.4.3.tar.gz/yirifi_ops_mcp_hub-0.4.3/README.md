# yirifi-ops-mcp-hub

MCP (Model Context Protocol) servers for Yirifi Ops - expose REST APIs as MCP tools for AI assistants like Claude.

## Installation

```bash
# Using uvx (recommended - no install needed)
uvx yirifi-ops-mcp-hub --version

# Using pip
pip install yirifi-ops-mcp-hub

# Using uv
uv pip install yirifi-ops-mcp-hub
```

### Optional: TOON Format (Compact Responses)

For optimized token-efficient responses, install toon-format (currently in beta):

```bash
# Install from GitHub (recommended for beta)
pip install git+https://github.com/toon-format/toon-python.git

# Or clone and install locally
git clone https://github.com/toon-format/toon-python.git
cd toon-python
uv sync
```

### Troubleshooting uvx Cache Issues

If `uvx` doesn't pick up the latest version after an upgrade:

```bash
# Clear cached environments and refresh
rm -rf ~/.cache/uv/environments* && uvx --refresh yirifi-ops-mcp-hub --version
```

## Quick Start

### Claude Code Configuration

Add to your Claude Code MCP settings (`~/.claude.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "yirifi-ops": {
      "command": "uvx",
      "args": ["yirifi-ops-mcp-hub"],
      "env": {
        "YIRIFI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Or with specific options:

```json
{
  "mcpServers": {
    "yirifi-dev": {
      "command": "uvx",
      "args": ["yirifi-ops-mcp-hub", "--mode=dev"],
      "env": {
        "YIRIFI_API_KEY": "your_api_key_here"
      }
    },
    "yirifi-prd": {
      "command": "uvx",
      "args": ["yirifi-ops-mcp-hub", "--mode=prd"],
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
YIRIFI_API_KEY=your_key uvx yirifi-ops-mcp-hub

# Run specific service
YIRIFI_API_KEY=your_key uvx yirifi-ops-mcp-hub --service=auth

# Development mode (localhost APIs)
YIRIFI_API_KEY=your_key uvx yirifi-ops-mcp-hub --mode=dev

# HTTP transport (for remote deployment)
uvx yirifi-ops-mcp-hub --transport=http --port=5200
```

**Options:**
- `--service`: `all` (default), `auth`, or `reg`
- `--mode`: `dev` (localhost) or `prd` (remote, default)
- `--transport`: `stdio` (default) or `http`
- `--port`: HTTP port (default: 5200)

### Utility Commands

```bash
# List available tools
uvx yirifi-ops-mcp-hub list-tools

# Test API connection
uvx yirifi-ops-mcp-hub test-connection --service=auth

# Show OpenAPI spec
uvx yirifi-ops-mcp-hub show-spec --service=auth

# Check version
uvx yirifi-ops-mcp-hub --version
```

## Architecture

This package uses a tiered exposure system for safe AI access:

- **DIRECT**: Safe, frequent operations exposed as individual MCP tools
- **GATEWAY**: Admin/dangerous operations accessible via `{service}_api_call` gateway tool
- **EXCLUDE**: Internal endpoints never exposed

### Spec-Driven Catalog (v0.4.0+)

Endpoints can be configured via OpenAPI `x-mcp-*` extensions or override files:

| Extension | Type | Default | Description |
|-----------|------|---------|-------------|
| `x-mcp-tier` | `direct\|gateway\|exclude` | `gateway` | Exposure tier |
| `x-mcp-risk-level` | `low\|medium\|high` | `medium` | Risk classification |
| `x-mcp-name` | `string` | `operationId` | Override tool name |
| `x-mcp-description` | `string` | `summary` | Override description |

## Environment Variables

- `YIRIFI_API_KEY`: API key for authentication (required)
- `AUTH_SERVICE_API_KEY`: Service-specific fallback for auth
- `REG_SERVICE_API_KEY`: Service-specific fallback for reg

## License

Proprietary - Yirifi
