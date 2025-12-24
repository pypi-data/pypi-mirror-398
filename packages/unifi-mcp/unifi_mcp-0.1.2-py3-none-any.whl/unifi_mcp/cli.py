"""CLI for UniFi MCP server management."""

import typer

from unifi_mcp.config import Settings
from unifi_mcp.server import run_server
from unifi_mcp.utils.process_utils import ServerManager

app = typer.Typer(
    help="UniFi MCP CLI for server management and configuration.",
    invoke_without_command=True,
)
manager = ServerManager(project_name="unifi-mcp")


@app.callback()
def main(
    ctx: typer.Context,
    start_server: bool = typer.Option(
        False,
        "--start-mcp-server",
        help="Starts the UniFi MCP server in the background.",
    ),
    stop_server: bool = typer.Option(
        False, "--stop-mcp-server", help="Stops the UniFi MCP server."
    ),
    restart_server: bool = typer.Option(
        False, "--restart-mcp-server", help="Restarts the UniFi MCP server."
    ),
    server_status: bool = typer.Option(
        False, "--server-status", help="Checks the status of the UniFi MCP server."
    ),
    host: str = typer.Option("127.0.0.1", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    reload: bool = typer.Option(
        False, "--reload", help="Enable auto-reload on file changes"
    ),
) -> None:
    """Main CLI entry point for UniFi MCP."""
    actions = [start_server, stop_server, restart_server, server_status]
    if sum(actions) > 1:
        typer.echo(
            "Error: Please use only one of --start-mcp-server, --stop-mcp-server, "
            "--restart-mcp-server, or --server-status at a time.",
            err=True,
        )
        raise typer.Exit(code=1)

    # If a management flag was used, execute the action and exit.
    if sum(actions) == 1:
        if restart_server:
            manager.stop_server()
            manager.start_server(host, port, debug, reload)
        elif start_server:
            manager.start_server(host, port, debug, reload)
        elif stop_server:
            manager.stop_server()
        elif server_status:
            manager.get_status()
        raise typer.Exit()

    # If no management flags were used and no subcommand is invoked, run the default action.
    if ctx.invoked_subcommand is None:
        typer.echo(f"Starting UniFi MCP server in foreground on {host}:{port}")
        # This call blocks, running the server in the foreground.
        run_server()


@app.command()
def config() -> None:
    """Display current configuration."""
    settings = Settings()
    typer.echo("Current UniFi MCP Server Configuration:")
    typer.echo(f"  Server Host: {settings.server.host}")
    typer.echo(f"  Server Port: {settings.server.port}")
    typer.echo(f"  Debug Mode: {settings.server.debug}")
    typer.echo(f"  Reload Mode: {settings.server.reload}")

    if settings.network_controller:
        typer.echo("  Network Controller: Configured")
        typer.echo(f"    Host: {settings.network_controller.host}")
        typer.echo(f"    Port: {settings.network_controller.port}")
        typer.echo(f"    Site ID: {settings.network_controller.site_id}")
    else:
        typer.echo("  Network Controller: Not configured")

    if settings.access_controller:
        typer.echo("  Access Controller: Configured")
        typer.echo(f"    Host: {settings.access_controller.host}")
        typer.echo(f"    Port: {settings.access_controller.port}")
        typer.echo(f"    Site ID: {settings.access_controller.site_id}")
    else:
        typer.echo("  Access Controller: Not configured")


@app.command()
def test_connection(
    controller_type: str = typer.Argument(
        ..., help="Type of controller to test (network or access)"
    ),
) -> None:
    """Test connection to UniFi controller."""
    settings = Settings()

    if controller_type.lower() == "network":
        if not settings.network_controller:
            typer.echo("Error: Network controller not configured")
            raise typer.Exit(code=1)

        typer.echo(
            f"Testing connection to Network Controller at {settings.network_controller.host}:{settings.network_controller.port}"
        )
        typer.echo("Network controller connection test: Not implemented yet")

    elif controller_type.lower() == "access":
        if not settings.access_controller:
            typer.echo("Error: Access controller not configured")
            raise typer.Exit(code=1)

        typer.echo(
            f"Testing connection to Access Controller at {settings.access_controller.host}:{settings.access_controller.port}"
        )
        typer.echo("Access controller connection test: Not implemented yet")

    else:
        typer.echo("Error: controller_type must be either 'network' or 'access'")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
