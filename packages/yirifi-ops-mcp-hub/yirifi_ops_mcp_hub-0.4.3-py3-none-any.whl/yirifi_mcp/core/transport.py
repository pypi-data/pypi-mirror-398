"""Transport configuration for MCP servers.

Supports both STDIO (default, for Claude Code) and HTTP (for remote deployment).
"""

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings


class TransportType(str, Enum):
    """Supported MCP transport types."""

    STDIO = "stdio"
    HTTP = "http"


class HTTPTransportConfig(BaseSettings):
    """Configuration for HTTP transport.

    All settings can be overridden via environment variables with MCP_HTTP_ prefix.
    Example: MCP_HTTP_HOST=0.0.0.0, MCP_HTTP_PORT=8000

    Note: Authentication is handled via API key passthrough. The client's X-API-Key
    header is extracted and forwarded to upstream services for validation.
    """

    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the HTTP server to",
    )
    port: int = Field(
        default=5200,
        description="Port to bind the HTTP server to",
    )
    path: str = Field(
        default="/mcp",
        description="URL path for the MCP endpoint",
    )
    stateless: bool = Field(
        default=True,
        description="Run in stateless mode for horizontal scaling",
    )

    model_config = {
        "env_prefix": "MCP_HTTP_",
        "extra": "ignore",
    }
