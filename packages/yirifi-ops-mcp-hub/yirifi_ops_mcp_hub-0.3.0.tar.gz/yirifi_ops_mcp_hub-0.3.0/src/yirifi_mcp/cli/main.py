"""Main CLI entry point for Yirifi MCP Hub."""

import asyncio
import logging
import sys

import click
import structlog

# Configure structlog for CLI output - write to stderr to avoid interfering with MCP STDIO
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

logger = structlog.get_logger()


@click.group(invoke_without_command=True)
@click.version_option(package_name="yirifi-ops-mcp-hub")
@click.option(
    "--service",
    "-s",
    default="all",
    type=click.Choice(["all", "auth", "reg"]),
    help="Service: 'all' (default), 'auth', or 'reg'",
)
@click.option(
    "--mode",
    "-m",
    default="prd",
    type=click.Choice(["dev", "prd"]),
    help="Mode: 'dev' (localhost) or 'prd' (remote). Default: prd",
)
@click.option(
    "--transport",
    "-t",
    default="stdio",
    type=click.Choice(["stdio", "http"]),
    help="Transport: 'stdio' (Claude Code) or 'http' (remote). Default: stdio",
)
@click.option(
    "--port",
    "-p",
    default=None,
    type=int,
    help="HTTP port (default: 5200). Only for --transport http",
)
@click.option(
    "--output-format",
    "-f",
    default="auto",
    type=click.Choice(["auto", "json", "toon"]),
    help="Response format: 'auto' (detect best), 'json', or 'toon'. Default: auto",
)
@click.pass_context
def cli(
    ctx,
    service: str,
    mode: str,
    transport: str,
    port: int | None,
    output_format: str,
):
    """Yirifi MCP Hub - MCP servers for Yirifi Ops services.

    \b
    Authentication (STDIO mode):
      Set YIRIFI_API_KEY environment variable

    \b
    Examples:
      # Default: all services, prd mode, stdio transport
      yirifi-ops-mcp-hub

      # Specific service in dev mode
      yirifi-ops-mcp-hub -s auth -m dev

      # HTTP transport for remote deployment
      yirifi-ops-mcp-hub -t http -p 5200
    """
    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["service"] = service
    ctx.obj["mode"] = mode
    ctx.obj["transport"] = transport
    ctx.obj["port"] = port
    ctx.obj["output_format"] = output_format

    # If no subcommand provided, run the server
    if ctx.invoked_subcommand is None:
        _run_server(
            service=service,
            mode=mode,
            transport=transport,
            port=port,
            output_format=output_format,
        )


def _run_server(
    service: str,
    mode: str,
    transport: str = "stdio",
    port: int | None = None,
    output_format: str = "auto",
):
    """Internal function to run the MCP server."""
    from yirifi_mcp.core.toon_encoder import OutputFormat

    # Convert string to OutputFormat enum
    output_format_enum = OutputFormat(output_format)

    # For STDIO transport, all output must go to stderr to avoid interfering with MCP protocol
    use_stderr = transport == "stdio"

    async def create_server():
        # Multi-service mode: combine all services into one server
        if service == "all":
            from yirifi_mcp.server.multi_service import (
                create_multi_service_server,
                get_available_services,
            )

            services = get_available_services()
            click.echo(f"Starting multi-service MCP hub (mode: {mode})", err=use_stderr)
            click.echo(f"Services: {', '.join(services)}", err=use_stderr)
            return await create_multi_service_server(
                services=services, mode=mode, output_format=output_format_enum
            )

        # Single service mode
        elif service == "auth":
            from yirifi_mcp.core.config import AuthServiceConfig
            from yirifi_mcp.servers.auth_service.server import create_auth_server

            config = AuthServiceConfig(mode=mode, output_format=output_format_enum)
            click.echo(f"Starting MCP server for: {service} (mode: {mode})", err=use_stderr)
            click.echo(f"Connecting to: {config.base_url}", err=use_stderr)
            return await create_auth_server(config=config)

        elif service == "reg":
            from yirifi_mcp.core.config import RegServiceConfig
            from yirifi_mcp.servers.reg_service.server import create_reg_server

            config = RegServiceConfig(mode=mode, output_format=output_format_enum)
            click.echo(f"Starting MCP server for: {service} (mode: {mode})", err=use_stderr)
            click.echo(f"Connecting to: {config.base_url}", err=use_stderr)
            return await create_reg_server(config=config)

        else:
            click.echo(f"Unknown service: {service}", err=True)
            raise click.Abort()

    try:
        if transport == "stdio":
            # STDIO mode - standard MCP over stdin/stdout
            # Disable banner to avoid stdout pollution that breaks MCP protocol
            click.echo("Transport: STDIO", err=True)
            mcp = asyncio.run(create_server())
            mcp.run(show_banner=False)

        elif transport == "http":
            # HTTP mode - Streamable HTTP with path-based service scoping
            from yirifi_mcp.core.transport import HTTPTransportConfig
            from yirifi_mcp.server.http import run_scoped_http_server

            # Build HTTP config from CLI args and env vars
            http_config_kwargs = {}
            if port:
                http_config_kwargs["port"] = port

            http_config = HTTPTransportConfig(**http_config_kwargs)

            click.echo("Transport: HTTP (Streamable) with Service Scoping")
            click.echo(f"Base URL: http://{http_config.host}:{http_config.port}")
            click.echo("")
            click.echo("Available endpoints:")
            click.echo("  /mcp       → All services (auth + reg)")
            click.echo("  /mcp/auth  → Auth service only")
            click.echo("  /mcp/reg   → Reg service only")
            click.echo("")
            click.echo("Auth: X-API-Key passthrough to upstream")

            # Note: --service flag is ignored for HTTP mode
            # All services are loaded, path determines scope
            if service != "all":
                click.echo(
                    f"\nNote: --service={service} is ignored in HTTP mode. "
                    "Use URL paths for scoping.",
                    err=True,
                )

            run_scoped_http_server(
                mode=mode,
                output_format=output_format_enum,
                config=http_config,
            )

    except KeyboardInterrupt:
        click.echo("\nShutting down...", err=True)


@cli.command("list-tools")
@click.option(
    "--service",
    "-s",
    default="all",
    type=click.Choice(["all", "auth", "reg"]),
    help="Service to list tools for: 'all' (default) or individual service",
)
@click.option(
    "--mode",
    "-m",
    default="prd",
    type=click.Choice(["dev", "prd"]),
    help="Environment mode: dev (localhost) or prd (remote). Default: prd",
)
def list_tools(service: str, mode: str):
    """List all MCP tools available for a service."""

    async def show_tools():
        if service == "all":
            from yirifi_mcp.server.multi_service import (
                create_multi_service_server,
                get_available_services,
            )

            services = get_available_services()
            mcp = await create_multi_service_server(services=services, mode=mode)
            title = "MULTI-SERVICE HUB"
        elif service == "auth":
            from yirifi_mcp.core.config import AuthServiceConfig
            from yirifi_mcp.servers.auth_service.server import create_auth_server

            config = AuthServiceConfig(mode=mode)
            mcp = await create_auth_server(config=config)
            title = "AUTH SERVICE"
        elif service == "reg":
            from yirifi_mcp.core.config import RegServiceConfig
            from yirifi_mcp.servers.reg_service.server import create_reg_server

            config = RegServiceConfig(mode=mode)
            mcp = await create_reg_server(config=config)
            title = "REG SERVICE"
        else:
            click.echo(f"Unknown service: {service}", err=True)
            return

        # Get tools from the server - returns dict of name -> Tool
        tools_dict = await mcp._tool_manager.get_tools()
        tools = list(tools_dict.values())

        click.echo(f"\n{title} TOOLS ({len(tools)} total):\n")
        click.echo("-" * 60)

        for tool in sorted(tools, key=lambda t: t.name):
            click.echo(f"  {tool.name}")
            if tool.description:
                # Truncate long descriptions
                desc = tool.description[:100]
                if len(tool.description) > 100:
                    desc += "..."
                click.echo(f"    {desc}")
            click.echo()

    asyncio.run(show_tools())


@cli.command("test-connection")
@click.option(
    "--service",
    "-s",
    default="auth",
    type=click.Choice(["auth", "reg"]),
    help="Service to test connection for",
)
@click.option(
    "--mode",
    "-m",
    default="prd",
    type=click.Choice(["dev", "prd"]),
    help="Environment mode: dev (localhost) or prd (remote). Default: prd",
)
def test_connection(service: str, mode: str):
    """Test connectivity to a service."""

    async def test():
        import httpx

        if service == "auth":
            from yirifi_mcp.core.config import AuthServiceConfig

            config = AuthServiceConfig(mode=mode)
            service_name = "auth-service"
        elif service == "reg":
            from yirifi_mcp.core.config import RegServiceConfig

            config = RegServiceConfig(mode=mode)
            service_name = "reg-service"
        else:
            click.echo(f"Unknown service: {service}", err=True)
            return

        url = f"{config.base_url}/api/v1/health/live"

        click.echo(f"Testing connection to: {config.base_url} (mode: {mode})")
        click.echo(f"API Key configured: {'Yes' if config.api_key else 'No'}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                click.echo(f"Health check status: {response.status_code}")

                if response.status_code == 200:
                    click.echo(click.style("Connection successful!", fg="green"))
                else:
                    click.echo(
                        click.style(f"Unexpected status: {response.status_code}", fg="yellow")
                    )

        except httpx.ConnectError:
            click.echo(click.style(f"Failed to connect to {config.base_url}", fg="red"))
            click.echo(f"Make sure the {service_name} is running.")
        except Exception as e:
            click.echo(click.style(f"Error: {e}", fg="red"))

    asyncio.run(test())


@cli.command()
@click.argument("name")
@click.option("--base-url", required=True, help="Service base URL")
@click.option("--openapi-path", default="/api/v1/docs/swagger.json", help="OpenAPI spec path")
def scaffold(name: str, base_url: str, openapi_path: str):
    """Scaffold a new MCP server for a service."""
    from yirifi_mcp.cli.scaffold import create_server_scaffold

    create_server_scaffold(name, base_url, openapi_path)
    click.echo(f"\nCreated server scaffold: src/yirifi_mcp/servers/{name}/")
    click.echo("\nNext steps:")
    click.echo(f"1. Add {name.upper()}_API_KEY to your .env file")
    click.echo("2. Customize routes.py to exclude unwanted endpoints")
    click.echo("3. Register the service in cli/main.py")
    click.echo(f"4. Run: yirifi-mcp run --service {name}")


@cli.command("show-spec")
@click.option(
    "--service",
    "-s",
    default="auth",
    type=click.Choice(["auth", "reg"]),
    help="Service to show spec info for",
)
@click.option(
    "--mode",
    "-m",
    default="prd",
    type=click.Choice(["dev", "prd"]),
    help="Environment mode: dev (localhost) or prd (remote). Default: prd",
)
def show_spec(service: str, mode: str):
    """Show OpenAPI spec information for a service."""

    async def show():
        from yirifi_mcp.core.openapi_utils import fetch_openapi_spec, get_spec_info

        if service == "auth":
            from yirifi_mcp.core.config import AuthServiceConfig

            config = AuthServiceConfig(mode=mode)
        elif service == "reg":
            from yirifi_mcp.core.config import RegServiceConfig

            config = RegServiceConfig(mode=mode)
        else:
            click.echo(f"Unknown service: {service}", err=True)
            return

        spec_url = f"{config.base_url}{config.openapi_path}"
        click.echo(f"Fetching OpenAPI spec from: {spec_url} (mode: {mode})")

        try:
            spec = await fetch_openapi_spec(
                base_url=config.base_url,
                openapi_path=config.openapi_path,
                api_key=config.api_key,
            )
            info = get_spec_info(spec)

            click.echo(f"\nAPI: {info['title']} v{info['version']}")
            click.echo(f"Paths: {info['paths_count']}")
            click.echo(f"Endpoints: {info['endpoints_count']}")
            click.echo("\nEndpoints:")
            click.echo("-" * 60)
            for endpoint in info["endpoints"]:
                click.echo(f"  {endpoint}")

        except Exception as e:
            click.echo(click.style(f"Error fetching spec: {e}", fg="red"))

    asyncio.run(show())


if __name__ == "__main__":
    cli()
